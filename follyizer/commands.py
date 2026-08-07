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
    show_id = None
    sequence = None

    if verb == "RUN":
        if len(parts) < 3:
            raise CommandError("MISSING_SHOW")
        show_id = parts[2].upper()
        trailing = parts[3:]
    else:
        trailing = parts[2:]

    for token in trailing:
        if token.upper().startswith("Q="):
            try:
                sequence = int(token.split("=", 1)[1])
            except ValueError as exc:
                raise CommandError("BAD_SEQUENCE") from exc

    if require_sequence_number and sequence is None:
        raise CommandError("MISSING_SEQUENCE")

    try:
        command_type = CommandType(verb)
    except ValueError as exc:
        raise CommandError("UNKNOWN_COMMAND") from exc

    return Command(type=command_type, show_id=show_id, sequence=sequence)
