from unittest.mock import MagicMock

from follyizer.app import Follyizer, format_status_message
from follyizer.commands import CommandError, CommandType, parse_command
from follyizer.fpp_client import FppStatus


def make_status():
    return FppStatus(
        state="idle",
        playlist="-",
        sequence="-",
        song="-",
        elapsed="00:00",
        remaining="00:00",
        volume=70,
        temperature_c=34.6,
        power_bad=False,
        version="9.5",
        raw={},
    )


def test_status_protocol_parses():
    command = parse_command("FZ STATUS Q=42")
    assert command.type is CommandType.STATUS
    assert command.sequence == 42


def test_status_message_format():
    message = format_status_message(make_status(), 42)
    assert message == (
        "FZ STAT S=- P=IDLE T=00:00/00:00 "
        "V=70 C=35 PWR=OK Q=42"
    )


def test_status_message_marks_bad_power():
    status = make_status()
    status = FppStatus(
        state=status.state,
        playlist=status.playlist,
        sequence=status.sequence,
        song=status.song,
        elapsed=status.elapsed,
        remaining=status.remaining,
        volume=status.volume,
        temperature_c=status.temperature_c,
        power_bad=True,
        version=status.version,
        raw=status.raw,
    )
    assert "PWR=BAD" in format_status_message(status, 1)


def test_unexpected_status_argument_rejected():
    try:
        parse_command("FZ STATUS PLEASE Q=1")
    except CommandError as exc:
        assert str(exc) == "UNEXPECTED_ARGUMENT"
    else:
        raise AssertionError("Expected CommandError")
