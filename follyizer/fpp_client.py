from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


@dataclass(frozen=True)
class FppStatus:
    state: str
    playlist: str | None
    sequence: str | None
    elapsed_seconds: int | None
    raw: dict[str, Any]


class FppClient:
    # Thin FPP HTTP adapter. Endpoint details are isolated here because they
    # may need adjustment after testing against the Cathedral team's FPP version.

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

        return FppStatus(
            state=str(data.get("status_name") or data.get("status") or "UNKNOWN"),
            playlist=data.get("current_playlist") or data.get("playlist"),
            sequence=data.get("current_sequence") or data.get("sequence"),
            elapsed_seconds=_to_int(data.get("seconds_elapsed")),
            raw=data,
        )

    def start_playlist(self, playlist_name: str) -> None:
        response = self.session.post(
            f"{self.base_url}/api/command",
            json={"command": "Start Playlist", "args": [playlist_name]},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

    def stop_gracefully(self) -> None:
        response = self.session.post(
            f"{self.base_url}/api/command",
            json={"command": "Stop Gracefully", "args": []},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

    def blackout(self) -> None:
        response = self.session.post(
            f"{self.base_url}/api/command",
            json={"command": "Stop Now", "args": []},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
