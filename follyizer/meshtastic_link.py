from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

from meshtastic.serial_interface import SerialInterface
from pubsub import pub


LOGGER = logging.getLogger(__name__)


class MeshtasticLink:
    """
    Owns one persistent Meshtastic serial connection.

    Follyizer should be the only process opening this serial port while it runs.
    Both future receive and transmit operations will use this same interface.
    """

    def __init__(
        self,
        serial_device: str,
        channel_index: int,
        destination_node: str | None,
        on_text: Callable[[str, str | None, int], None],
    ):
        self.serial_device = serial_device
        self.channel_index = channel_index
        self.destination_node = destination_node
        self.on_text = on_text
        self.interface: SerialInterface | None = None
        self._subscribed = False
        self._lock = threading.Lock()

    @property
    def connected(self) -> bool:
        return self.interface is not None

    def connect(self) -> None:
        with self._lock:
            if self.interface is not None:
                LOGGER.debug("Meshtastic already connected")
                return

            LOGGER.info("Connecting to Meshtastic node at %s", self.serial_device)

            if not self._subscribed:
                pub.subscribe(self._on_receive, "meshtastic.receive")
                self._subscribed = True

            try:
                self.interface = SerialInterface(devPath=self.serial_device)
            except Exception:
                if self._subscribed:
                    pub.unsubscribe(self._on_receive, "meshtastic.receive")
                    self._subscribed = False
                raise

            LOGGER.info("Meshtastic serial connection established")

    def close(self) -> None:
        with self._lock:
            if self._subscribed:
                try:
                    pub.unsubscribe(self._on_receive, "meshtastic.receive")
                finally:
                    self._subscribed = False

            if self.interface is not None:
                try:
                    self.interface.close()
                finally:
                    self.interface = None

            LOGGER.info("Meshtastic serial connection closed")

    def get_my_node_info(self) -> dict[str, Any] | None:
        if self.interface is None:
            raise RuntimeError("Meshtastic interface is not connected")
        return self.interface.getMyNodeInfo()

    def send_text(self, text: str, destination_id: str | None = None) -> None:
        """
        Available for later milestones. Uses the same persistent connection.
        """
        if self.interface is None:
            raise RuntimeError("Meshtastic interface is not connected")

        destination = destination_id or self.destination_node
        kwargs: dict[str, Any] = {
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

        # The channel index the packet arrived on. meshtastic-python omits this
        # field for channel 0, so a missing value defaults to 0. This is the
        # decrypted-channel index, not a key - the firmware has already
        # verified the PSK before handing us the packet.
        channel = packet.get("channel", 0)
        try:
            channel = int(channel)
        except (TypeError, ValueError):
            channel = 0

        LOGGER.debug(
            "Raw Meshtastic packet received from %s on channel %s", sender, channel
        )

        try:
            self.on_text(str(text), str(sender) if sender else None, channel)
        except Exception:
            LOGGER.exception("Unhandled exception in Meshtastic receive callback")
