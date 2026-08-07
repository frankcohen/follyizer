from __future__ import annotations

import logging
from collections.abc import Callable

from meshtastic.serial_interface import SerialInterface
from pubsub import pub


LOGGER = logging.getLogger(__name__)


class MeshtasticLink:
    def __init__(
        self,
        serial_device: str,
        channel_index: int,
        destination_node: str | None,
        on_text: Callable[[str, str | None], None],
    ):
        self.serial_device = serial_device
        self.channel_index = channel_index
        self.destination_node = destination_node
        self.on_text = on_text
        self.interface = None

    def connect(self) -> None:
        LOGGER.info("Connecting to Meshtastic node at %s", self.serial_device)
        pub.subscribe(self._on_receive, "meshtastic.receive")
        self.interface = SerialInterface(devPath=self.serial_device)
        LOGGER.info("Meshtastic connected")

    def close(self) -> None:
        pub.unsubscribe(self._on_receive, "meshtastic.receive")
        if self.interface is not None:
            self.interface.close()
            self.interface = None

    def send_text(self, text: str, destination_id: str | None = None) -> None:
        if self.interface is None:
            raise RuntimeError("Meshtastic interface is not connected")

        destination = destination_id or self.destination_node
        kwargs = {
            "text": text,
            "channelIndex": self.channel_index,
            "wantAck": bool(destination),
        }
        if destination:
            kwargs["destinationId"] = destination

        self.interface.sendText(**kwargs)

    def _on_receive(self, packet: dict, interface: SerialInterface) -> None:
        decoded = packet.get("decoded", {})
        text = decoded.get("text")
        if not text:
            return

        sender = packet.get("fromId")
        LOGGER.info("Received Meshtastic text from %s: %s", sender, text)
        self.on_text(str(text), str(sender) if sender else None)
