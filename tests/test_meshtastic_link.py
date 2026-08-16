from unittest.mock import MagicMock, patch

from follyizer.meshtastic_link import MeshtasticLink


def test_connect_is_idempotent():
    callback = MagicMock()

    with patch("follyizer.meshtastic_link.SerialInterface") as serial_cls, \
         patch("follyizer.meshtastic_link.pub.subscribe"), \
         patch("follyizer.meshtastic_link.pub.unsubscribe"):
        interface = MagicMock()
        serial_cls.return_value = interface

        link = MeshtasticLink("/dev/ttyUSB0", 0, None, callback)
        link.connect()
        link.connect()

        assert serial_cls.call_count == 1
        assert link.connected is True

        link.close()
        assert interface.close.call_count == 1
        assert link.connected is False


def test_receive_forwards_text_and_sender():
    callback = MagicMock()
    link = MeshtasticLink("/dev/ttyUSB0", 0, None, callback)

    packet = {
        "fromId": "!be49a244",
        "channel": 1,
        "decoded": {
            "portnum": "TEXT_MESSAGE_APP",
            "text": "Hello Follyizer",
        },
    }

    link._on_receive(packet, MagicMock())
    callback.assert_called_once_with("Hello Follyizer", "!be49a244", 1)


def test_receive_defaults_channel_zero_when_absent():
    callback = MagicMock()
    link = MeshtasticLink("/dev/ttyUSB0", 0, None, callback)

    packet = {
        "fromId": "!be49a244",
        "decoded": {
            "portnum": "TEXT_MESSAGE_APP",
            "text": "Hello Follyizer",
        },
    }

    link._on_receive(packet, MagicMock())
    callback.assert_called_once_with("Hello Follyizer", "!be49a244", 0)
