from unittest.mock import MagicMock

from follyizer.commands import CommandType, parse_command
from follyizer.fpp_client import FppClient


def test_stop_protocol_is_case_insensitive():
    command = parse_command("Fz stop q=5")
    assert command.type is CommandType.STOP
    assert command.sequence == 5


def test_fpp_stop_posts_stop_now():
    client = FppClient("127.0.0.1")
    response = MagicMock()
    client.session.post = MagicMock(return_value=response)

    client.stop_playlist()

    client.session.post.assert_called_once_with(
        "http://127.0.0.1:80/api/command",
        json={
            "command": "Stop Now",
            "args": [],
        },
        timeout=5,
    )
    response.raise_for_status.assert_called_once()
