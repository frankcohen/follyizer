from unittest.mock import MagicMock

from follyizer.app import Follyizer
from follyizer.config import (
    AppConfig,
    CommandConfig,
    FppConfig,
    MeshtasticConfig,
)


def make_app(
    channel_index: int = 1,
    authorized_senders: tuple[str, ...] = (),
) -> Follyizer:
    config = AppConfig(
        meshtastic=MeshtasticConfig(
            serial_device="/dev/ttyUSB0",
            status_interval_seconds=120,
            channel_index=channel_index,
            destination_node=None,
            authorized_senders=authorized_senders,
        ),
        fpp=FppConfig(host="127.0.0.1", port=80, timeout_seconds=5),
        commands=CommandConfig(
            require_sequence_number=True,
            allow_broadcast_commands=False,
        ),
        shows={},
        logging_level="INFO",
    )

    app = Follyizer(config)
    # Replace the real link/client so no serial port or HTTP is touched.
    app.mesh = MagicMock()
    app.fpp = MagicMock()
    return app


def test_command_on_control_channel_is_executed():
    app = make_app(channel_index=1)

    app.handle_message("FZ RUN Test01 Q=2", "!be49a244", channel=1)

    app.fpp.start_playlist.assert_called_once_with("Test01")


def test_command_on_public_channel_is_ignored():
    app = make_app(channel_index=1)

    # Same command, but arriving on the public default channel (0).
    app.handle_message("FZ RUN Test01 Q=2", "!be49a244", channel=0)

    app.fpp.start_playlist.assert_not_called()


def test_unauthorized_sender_is_ignored():
    app = make_app(channel_index=1, authorized_senders=("!trusted01",))

    app.handle_message("FZ RUN Test01 Q=2", "!attacker99", channel=1)

    app.fpp.start_playlist.assert_not_called()


def test_authorized_sender_on_control_channel_is_executed():
    app = make_app(channel_index=1, authorized_senders=("!trusted01",))

    app.handle_message("FZ RUN Test01 Q=2", "!trusted01", channel=1)

    app.fpp.start_playlist.assert_called_once_with("Test01")


def test_empty_allowlist_permits_any_sender_on_control_channel():
    app = make_app(channel_index=1, authorized_senders=())

    app.handle_message("FZ STOP Q=5", "!anybody", channel=1)

    app.fpp.stop_playlist.assert_called_once()


def test_authorized_sender_still_blocked_on_wrong_channel():
    app = make_app(channel_index=1, authorized_senders=("!trusted01",))

    # Right sender, wrong channel - channel gate takes precedence.
    app.handle_message("FZ RUN Test01 Q=2", "!trusted01", channel=0)

    app.fpp.start_playlist.assert_not_called()
