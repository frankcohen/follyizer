from unittest.mock import MagicMock

from follyizer.fpp_client import FppClient


def test_get_status_parses_fpp_95_schema():
    client = FppClient("127.0.0.1")
    response = MagicMock()
    response.json.return_value = {
        "current_playlist": {
            "playlist": "",
        },
        "current_sequence": "",
        "current_song": "",
        "status_name": "idle",
        "time_elapsed": "00:00",
        "time_remaining": "00:00",
        "volume": 70,
        "powerBad": False,
        "version": "9.5",
        "sensors": [
            {
                "label": "CPU: ",
                "value": 36.511,
                "valueType": "Temperature",
            }
        ],
    }
    client.session.get = MagicMock(return_value=response)

    status = client.get_status()

    assert status.state == "idle"
    assert status.playlist == "-"
    assert status.elapsed == "00:00"
    assert status.remaining == "00:00"
    assert status.volume == 70
    assert status.temperature_c == 36.511
    assert status.power_bad is False
    assert status.version == "9.5"

    response.raise_for_status.assert_called_once()


def test_get_status_handles_missing_optional_fields():
    client = FppClient("127.0.0.1")
    response = MagicMock()
    response.json.return_value = {
        "status_name": "playing",
    }
    client.session.get = MagicMock(return_value=response)

    status = client.get_status()

    assert status.state == "playing"
    assert status.playlist == "-"
    assert status.sequence == "-"
    assert status.song == "-"
    assert status.volume is None
    assert status.temperature_c is None
