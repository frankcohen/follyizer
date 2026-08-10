from __future__ import annotations

import argparse
import logging
import signal
import threading

from follyizer.config import AppConfig, load_config
from follyizer.fpp_client import FppClient
from follyizer.meshtastic_link import MeshtasticLink


LOGGER = logging.getLogger(__name__)

FPP_POLL_INTERVAL_SECONDS = 10


class Follyizer:
    """Follyizer v0.1.1: persistent Meshtastic + FPP status polling."""

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

        LOGGER.info("Listening for Meshtastic text. Press Ctrl-C to stop.")
        self.stop_event.wait()

        LOGGER.info("Follyizer stopping")
        self.fpp.close()
        self.mesh.close()

    def stop(self) -> None:
        self.stop_event.set()

    def handle_message(self, text: str, sender: str | None) -> None:
        # Milestone 2 still does not parse or act on commands.
        LOGGER.info("MESHTASTIC RX from=%s text=%r", sender or "unknown", text)

    def _fpp_status_loop(self) -> None:
        # Query immediately at startup, then every 10 seconds.
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
            # A temporary FPP/API failure must not kill Follyizer or release
            # the Meshtastic serial connection.
            LOGGER.warning("FPP STATUS unavailable: %s", exc)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Follyizer persistent Meshtastic and FPP status monitor"
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
