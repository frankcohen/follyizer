from __future__ import annotations

import argparse
import logging
import signal
import threading

from follyizer.config import AppConfig, load_config
from follyizer.meshtastic_link import MeshtasticLink


LOGGER = logging.getLogger(__name__)


class Follyizer:
    """Follyizer v0.1.0: persistent Meshtastic connection milestone."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.stop_event = threading.Event()

        self.mesh = MeshtasticLink(
            serial_device=config.meshtastic.serial_device,
            channel_index=config.meshtastic.channel_index,
            destination_node=config.meshtastic.destination_node,
            on_text=self.handle_message,
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
        LOGGER.info("Listening for Meshtastic text. Press Ctrl-C to stop.")

        self.stop_event.wait()

        LOGGER.info("Follyizer stopping")
        self.mesh.close()

    def stop(self) -> None:
        self.stop_event.set()

    def handle_message(self, text: str, sender: str | None) -> None:
        # Milestone 1 intentionally does not parse or act on commands yet.
        # It proves one long-lived process can own the serial port and receive
        # messages continuously.
        LOGGER.info("MESHTASTIC RX from=%s text=%r", sender or "unknown", text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Follyizer persistent Meshtastic connection"
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
