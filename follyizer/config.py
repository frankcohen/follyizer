from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class MeshtasticConfig:
    serial_device: str
    status_interval_seconds: int
    channel_index: int
    destination_node: str | None
    authorized_senders: tuple[str, ...]


@dataclass(frozen=True)
class FppConfig:
    host: str
    port: int
    timeout_seconds: int


@dataclass(frozen=True)
class CommandConfig:
    require_sequence_number: bool
    allow_broadcast_commands: bool


@dataclass(frozen=True)
class AppConfig:
    meshtastic: MeshtasticConfig
    fpp: FppConfig
    commands: CommandConfig
    shows: dict[str, str]
    logging_level: str


def _required(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise ValueError(f"Missing required configuration key: {key}")
    return mapping[key]


def load_config(path: str | Path) -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    raw = yaml.safe_load(config_path.read_text()) or {}
    mesh = _required(raw, "meshtastic")
    fpp = _required(raw, "fpp")
    commands = _required(raw, "commands")
    shows = _required(raw, "shows")
    logging_config = raw.get("logging", {})

    return AppConfig(
        meshtastic=MeshtasticConfig(
            serial_device=str(_required(mesh, "serial_device")),
            status_interval_seconds=int(mesh.get("status_interval_seconds", 120)),
            channel_index=int(mesh.get("channel_index", 0)),
            destination_node=mesh.get("destination_node"),
            authorized_senders=tuple(str(x) for x in mesh.get("authorized_senders", [])),
        ),
        fpp=FppConfig(
            host=str(fpp.get("host", "127.0.0.1")),
            port=int(fpp.get("port", 80)),
            timeout_seconds=int(fpp.get("timeout_seconds", 5)),
        ),
        commands=CommandConfig(
            require_sequence_number=bool(commands.get("require_sequence_number", True)),
            allow_broadcast_commands=bool(commands.get("allow_broadcast_commands", False)),
        ),
        shows={str(k).upper(): str(v) for k, v in shows.items()},
        logging_level=str(logging_config.get("level", "INFO")).upper(),
    )
