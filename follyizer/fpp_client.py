from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class FppStatus:
    state: str
    playlist: str
    sequence: str
    song: str
    elapsed: str
    remaining: str
    volume: int | None
    temperature_c: float | None
    power_bad: bool
    version: str
    raw: dict[str, Any]


class FppClient:
    """Small HTTP client for the FPP status API."""

    def __init__(self, host: str, port: int = 80, timeout_seconds: int = 5):
        self.base_url = f"http://{host}:{port}"
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()

    def get_status(self) -> FppStatus:
        response = self.session.get(
            f"{self.base_url}/api/fppd/status",
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()

        playlist_data = data.get("current_playlist") or {}
        playlist = str(playlist_data.get("playlist") or "-")

        return FppStatus(
            state=str(data.get("status_name") or "unknown"),
            playlist=playlist,
            sequence=str(data.get("current_sequence") or "-"),
            song=str(data.get("current_song") or "-"),
            elapsed=str(data.get("time_elapsed") or "00:00"),
            remaining=str(data.get("time_remaining") or "00:00"),
            volume=_to_int(data.get("volume")),
            temperature_c=_find_cpu_temperature(data.get("sensors") or []),
            power_bad=bool(data.get("powerBad", False)),
            version=str(data.get("version") or "unknown"),
            raw=data,
        )

    def close(self) -> None:
        self.session.close()


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _find_cpu_temperature(sensors: list[dict[str, Any]]) -> float | None:
    for sensor in sensors:
        label = str(sensor.get("label") or "").strip().lower()
        value_type = str(sensor.get("valueType") or "").strip().lower()

        if "cpu" in label and value_type == "temperature":
            try:
                return float(sensor.get("value"))
            except (TypeError, ValueError):
                return None

    return None
