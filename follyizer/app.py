from __future__ import annotations

import argparse
import logging
import signal
import threading
from dataclasses import dataclass, field

from follyizer.commands import CommandError, CommandType, parse_command
from follyizer.config import AppConfig, load_config
from follyizer.fpp_client import FppClient
from follyizer.meshtastic_link import MeshtasticLink


LOGGER = logging.getLogger(__name__)


@dataclass
class RuntimeState:
    last_sequences: dict[str, int] = field(default_factory=dict)
    last_command: str | None = None


class CathedralControl:
    def __init__(self, config: AppConfig):
        self.config = config
        self.state = RuntimeState()
        self.stop_event = threading.Event()

        self.fpp = FppClient(
            host=config.fpp.host,
            port=config.fpp.port,
            timeout_seconds=config.fpp.timeout_seconds,
        )
        self.mesh = MeshtasticLink(
            serial_device=config.meshtastic.serial_device,
            channel_index=config.meshtastic.channel_index,
            destination_node=config.meshtastic.destination_node,
            on_text=self.handle_message,
        )

    def run(self) -> None:
        self.mesh.connect()
        threading.Thread(target=self._status_loop, daemon=True).start()
        LOGGER.info("Follyizer started")
        self.stop_event.wait()
        LOGGER.info("Follyizer stopping")
        self.mesh.close()

    def stop(self) -> None:
        self.stop_event.set()

    def handle_message(self, text: str, sender: str | None) -> None:
        if self.config.meshtastic.authorized_senders:
            if sender not in self.config.meshtastic.authorized_senders:
                LOGGER.warning("Rejected unauthorized sender: %s", sender)
                return

        try:
            command = parse_command(
                text,
                require_sequence_number=self.config.commands.require_sequence_number,
            )
        except CommandError as exc:
            self._reply(sender, f"FZ NAK REASON={exc}")
            return

        if command.sequence is not None and sender:
            last = self.state.last_sequences.get(sender)
            if last is not None and command.sequence <= last:
                self._reply(sender, f"FZ NAK Q={command.sequence} REASON=DUPLICATE")
                return
            self.state.last_sequences[sender] = command.sequence

        self.state.last_command = text
        q = f" Q={command.sequence}" if command.sequence is not None else ""

        try:
            if command.type is CommandType.RUN:
                playlist = self.config.shows.get(command.show_id or "")
                if playlist is None:
                    self._reply(sender, f"FZ NAK{q} REASON=UNKNOWN_SHOW")
                    return
                self.fpp.start_playlist(playlist)
                self._reply(sender, f"FZ ACK{q} RUN {command.show_id}")

            elif command.type is CommandType.STOP:
                self.fpp.stop_gracefully()
                self._reply(sender, f"FZ ACK{q} STOP")

            elif command.type is CommandType.BLACKOUT:
                self.fpp.blackout()
                self._reply(sender, f"FZ ACK{q} BLACKOUT")

            elif command.type is CommandType.STATUS:
                self._reply(sender, self._build_status_message(q=q))

        except Exception:
            LOGGER.exception("Command failed")
            self._reply(sender, f"FZ NAK{q} REASON=FPP_ERROR")

    def _status_loop(self) -> None:
        interval = self.config.meshtastic.status_interval_seconds
        while not self.stop_event.wait(interval):
            try:
                self.mesh.send_text(self._build_status_message())
            except Exception:
                LOGGER.exception("Periodic status transmission failed")

    def _build_status_message(self, q: str = "") -> str:
        try:
            status = self.fpp.get_status()
            playlist = _compact(status.playlist or "-")
            state = _compact(status.state)
            elapsed = _format_seconds(status.elapsed_seconds) if status.elapsed_seconds is not None else "--:--"
            return f"FZ STAT S={playlist} P={state} T={elapsed}{q}"
        except Exception:
            LOGGER.exception("Unable to query FPP status")
            return f"FZ STAT P=ERROR FPP=OFFLINE{q}"

    def _reply(self, sender: str | None, text: str) -> None:
        try:
            self.mesh.send_text(text, destination_id=sender)
        except Exception:
            LOGGER.exception("Unable to send reply: %s", text)


def _compact(value: str) -> str:
    return value.upper().replace(" ", "_")[:24]


def _format_seconds(seconds: int) -> str:
    minutes, seconds = divmod(max(seconds, 0), 60)
    return f"{minutes:02d}:{seconds:02d}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Meshtastic-to-FPP control bridge")
    parser.add_argument("--config", default="config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    logging.basicConfig(
        level=getattr(logging, config.logging_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = CathedralControl(config)

    def request_stop(signum: int, frame: object) -> None:
        LOGGER.info("Received signal %s", signum)
        app.stop()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    app.run()


if __name__ == "__main__":
    main()
