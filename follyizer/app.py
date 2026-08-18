from __future__ import annotations

import argparse
import logging
import signal
import threading

from follyizer.commands import CommandError, CommandType, parse_command
from follyizer.config import AppConfig, load_config
from follyizer.fpp_client import FppClient, FppStatus
from follyizer.meshtastic_link import MeshtasticLink


LOGGER = logging.getLogger(__name__)

FPP_POLL_INTERVAL_SECONDS = 10


class Follyizer:
    """Follyizer v0.1.4: persistent mesh + FPP STATUS + FZ RUN."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.stop_event = threading.Event()

        self.mesh = MeshtasticLink(
            serial_device=config.meshtastic.serial_device,
            channel_index=config.meshtastic.channel_index,
            destination_node=config.meshtastic.destination_node,
            on_text=self.handle_message,
        )

        self.fpp = FppClient(
            host=config.fpp.host,
            port=config.fpp.port,
            timeout_seconds=config.fpp.timeout_seconds,
        )

    def run(self) -> None:
        self.mesh.connect()

        node = self.mesh.get_my_node_info()
        user = (node or {}).get("user", {})
        LOGGER.info(
            "Follyizer connected: node=%s name=%s hardware=%s",
            user.get("id", "unknown"),
            user.get("longName", "unknown"),
            user.get("hwModel", "unknown"),
        )

        fpp_thread = threading.Thread(
            target=self._fpp_status_loop,
            name="fpp-status",
            daemon=True,
        )
        fpp_thread.start()

        LOGGER.info(
            "Listening for Meshtastic text. STATUS command enabled. "
            "Press Ctrl-C to stop."
        )
        self.stop_event.wait()

        LOGGER.info("Follyizer stopping")
        self.fpp.close()
        self.mesh.close()

    def stop(self) -> None:
        self.stop_event.set()

    def handle_message(
        self, text: str, sender: str | None, channel: int = 0
    ) -> None:
        LOGGER.info(
            "MESHTASTIC RX from=%s channel=%s text=%r",
            sender or "unknown",
            channel,
            text,
        )

        # Ordinary Meshtastic chat is not a Follyizer command.
        if not text.strip().upper().startswith("FZ "):
            return

        # Only honor commands that arrive on the configured control channel.
        # The Meshtastic firmware has already decrypted the packet, so arrival
        # on this index proves the sender holds that channel's PSK. Commands on
        # any other channel - including the public default channel - are ignored.
        if channel != self.config.meshtastic.channel_index:
            LOGGER.warning(
                "Ignoring FZ command on channel=%s; control channel is %s (from=%s)",
                channel,
                self.config.meshtastic.channel_index,
                sender or "unknown",
            )
            return

        # Optional per-sender allowlist, layered on top of the channel PSK.
        # An empty authorized_senders list disables the allowlist and permits
        # any sender that can already reach the control channel. Node IDs are
        # self-asserted and spoofable, so this is defense-in-depth, not the
        # primary control.
        authorized = self.config.meshtastic.authorized_senders
        if authorized and (sender is None or sender not in authorized):
            LOGGER.warning(
                "Ignoring FZ command from unauthorized sender=%s on channel=%s",
                sender or "unknown",
                channel,
            )
            return

        try:
            command = parse_command(
                text,
                require_sequence_number=self.config.commands.require_sequence_number,
            )
        except CommandError as exc:
            self._reply(sender, f"FZ NAK REASON={exc}")
            return

        q = (
            f" Q={command.sequence}"
            if command.sequence is not None
            else ""
        )

        if command.type is CommandType.STATUS:
            self._handle_status(sender, command.sequence)
            return

        if command.type is CommandType.RUN:
            self._handle_run(sender, command.show_id, command.sequence)
            return

        if command.type is CommandType.STOP:
            self._handle_stop(sender, command.sequence)
            return

        # BLACKOUT remains intentionally unimplemented.
        LOGGER.info(
            "FZ command %s recognized but not implemented in milestone 5",
            command.type.value,
        )
        self._reply(
            sender,
            f"FZ NAK{q} REASON=NOT_IMPLEMENTED",
        )

    def _handle_run(
        self,
        sender: str | None,
        playlist_name: str | None,
        sequence: int | None,
    ) -> None:
        q = f" Q={sequence}" if sequence is not None else ""

        if not playlist_name:
            self._reply(sender, f"FZ NAK{q} REASON=MISSING_SHOW")
            return

        try:
            LOGGER.info(
                "FPP RUN playlist=%s requested_by=%s",
                playlist_name,
                sender or "unknown",
            )
            self.fpp.start_playlist(playlist_name)

            reply = f"FZ ACK{q} RUN {playlist_name}"
            LOGGER.info(
                "MESHTASTIC TX to=%s text=%r",
                sender or "channel",
                reply,
            )
            self._reply(sender, reply)
        except Exception as exc:
            LOGGER.warning(
                "FZ RUN failed playlist=%s: %s",
                playlist_name,
                exc,
            )
            self._reply(sender, f"FZ NAK{q} REASON=FPP_ERROR")

    def _handle_stop(
        self,
        sender: str | None,
        sequence: int | None,
    ) -> None:
        q = f" Q={sequence}" if sequence is not None else ""

        try:
            LOGGER.info(
                "FPP STOP requested_by=%s",
                sender or "unknown",
            )
            self.fpp.stop_playlist()

            reply = f"FZ ACK{q} STOP"
            LOGGER.info(
                "MESHTASTIC TX to=%s text=%r",
                sender or "channel",
                reply,
            )
            self._reply(sender, reply)
        except Exception as exc:
            LOGGER.warning("FZ STOP failed: %s", exc)
            self._reply(sender, f"FZ NAK{q} REASON=FPP_ERROR")

    def _handle_status(self, sender: str | None, sequence: int | None) -> None:
        q = f" Q={sequence}" if sequence is not None else ""

        try:
            status = self.fpp.get_status()
            message = format_status_message(status, sequence)
            LOGGER.info("MESHTASTIC TX to=%s text=%r", sender or "channel", message)
            self._reply(sender, message)
        except Exception as exc:
            LOGGER.warning("FZ STATUS failed: %s", exc)
            self._reply(sender, f"FZ NAK{q} REASON=FPP_ERROR")

    def _reply(self, sender: str | None, text: str) -> None:
        try:
            self.mesh.send_text(text, destination_id=sender)
        except Exception:
            LOGGER.exception("Unable to send Meshtastic reply: %s", text)

    def _fpp_status_loop(self) -> None:
        while not self.stop_event.is_set():
            self._log_fpp_status()

            if self.stop_event.wait(FPP_POLL_INTERVAL_SECONDS):
                break

    def _log_fpp_status(self) -> None:
        try:
            status = self.fpp.get_status()

            temp = (
                f"{status.temperature_c:.1f}"
                if status.temperature_c is not None
                else "?"
            )
            volume = str(status.volume) if status.volume is not None else "?"

            LOGGER.info(
                "FPP STATUS state=%s playlist=%s elapsed=%s remaining=%s "
                "volume=%s temp=%s powerBad=%s version=%s",
                status.state,
                status.playlist,
                status.elapsed,
                status.remaining,
                volume,
                temp,
                status.power_bad,
                status.version,
            )
        except Exception as exc:
            LOGGER.warning("FPP STATUS unavailable: %s", exc)


def format_status_message(
    status: FppStatus,
    sequence: int | None = None,
) -> str:
    state = _compact(status.state).upper()
    playlist = _compact(status.playlist)

    volume = str(status.volume) if status.volume is not None else "?"
    temp = (
        str(round(status.temperature_c))
        if status.temperature_c is not None
        else "?"
    )
    power = "BAD" if status.power_bad else "OK"
    q = f" Q={sequence}" if sequence is not None else ""

    return (
        f"FZ STAT "
        f"S={playlist} "
        f"P={state} "
        f"T={status.elapsed}/{status.remaining} "
        f"V={volume} "
        f"C={temp} "
        f"PWR={power}"
        f"{q}"
    )


def _compact(value: str) -> str:
    return str(value).strip().replace(" ", "_")[:24] or "-"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Follyizer Meshtastic/FPP bridge"
    )
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)

    logging.basicConfig(
        level=getattr(logging, config.logging_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = Follyizer(config)

    def request_stop(signum: int, frame: object) -> None:
        LOGGER.info("Received signal %s", signum)
        app.stop()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    app.run()


if __name__ == "__main__":
    main()
