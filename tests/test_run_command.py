from unittest.mock import MagicMock

from follyizer.commands import CommandType, parse_command
from follyizer.fpp_client import FppClient


def test_run_protocol_parses_direct_playlist_name():
    command = parse_command("FZ RUN TEST01 Q=2")
    assert command.type is CommandType.RUN
    assert command.show_id == "TEST01"
    assert command.sequence == 2


def test_protocol_keywords_are_case_insensitive():
    command = parse_command("fz run Test01 q=2")
    assert command.type is CommandType.RUN
    assert command.show_id == "Test01"
    assert command.sequence == 2


def test_playlist_case_is_preserved():
    command = parse_command("Fz RuN SaturdayShow Q=9")
    assert command.show_id == "SaturdayShow"


def test_fpp_start_playlist_posts_start_playlist_command():
    client = FppClient("127.0.0.1")
    response = MagicMock()
    client.session.post = MagicMock(return_value=response)

    client.start_playlist("TEST01")

    client.session.post.assert_called_once_with(
        "http://127.0.0.1:80/api/command",
        json={
            "command": "Start Playlist",
            "args": ["TEST01", "false"],
        },
        timeout=5,
    )
    response.raise_for_status.assert_called_once()
