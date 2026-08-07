import pytest

from follyizer.commands import CommandError, CommandType, parse_command


def test_parse_run_command():
    command = parse_command("FZ RUN TEST01 Q=7")
    assert command.type is CommandType.RUN
    assert command.show_id == "TEST01"
    assert command.sequence == 7


def test_parse_status_command():
    command = parse_command("FZ STATUS Q=8")
    assert command.type is CommandType.STATUS
    assert command.show_id is None
    assert command.sequence == 8


def test_reject_missing_sequence():
    with pytest.raises(CommandError, match="MISSING_SEQUENCE"):
        parse_command("FZ STOP")


def test_reject_unknown_protocol():
    with pytest.raises(CommandError, match="BAD_PROTOCOL"):
        parse_command("RUN TEST01 Q=1")
