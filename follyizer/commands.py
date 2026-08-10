from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CommandType(str, Enum):
    RUN = "RUN"
    STOP = "STOP"
    STATUS = "STATUS"
    BLACKOUT = "BLACKOUT"


@dataclass(frozen=True)
class Command:
    type: CommandType
    show_id: str | None
    sequence: int | None


class CommandError(ValueError):
    pass


def parse_command(text: str, require_sequence_number: bool = True) -> Command:
    parts = text.strip().split()

    if len(parts) < 2 or parts[0].upper() != "FZ":
        raise CommandError("BAD_PROTOCOL")

    verb = parts[1].upper()
    show_id: str | None = None

    try:
        command_type = CommandType(verb)
    except ValueError as exc:
        raise CommandError("UNKNOWN_COMMAND") from exc

    if command_type is CommandType.RUN:
        if len(parts) < 3:
            raise CommandError("MISSING_SHOW")
        show_id = parts[2].upper()
        trailing = parts[3:]
    else:
        trailing = parts[2:]

    sequence: int | None = None

    for token in trailing:
        if not token.upper().startswith("Q="):
            raise CommandError("UNEXPECTED_ARGUMENT")

        if sequence is not None:
            raise CommandError("DUPLICATE_SEQUENCE")

        value = token.split("=", 1)[1]
        try:
            sequence = int(value)
        except ValueError as exc:
            raise CommandError("BAD_SEQUENCE") from exc

        if sequence < 0:
            raise CommandError("BAD_SEQUENCE")

    if require_sequence_number and sequence is None:
        raise CommandError("MISSING_SEQUENCE")

    return Command(
        type=command_type,
        show_id=show_id,
        sequence=sequence,
    )
