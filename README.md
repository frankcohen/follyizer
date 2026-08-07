# Follyizer

**Meshtastic Remote Control and Monitoring for Falcon Player (FPP)**

[![The Gothic Folly Cathedral](doc/images/gothic_folly.jpg)](https://thegothicfolly.com/)

Follyizer is an open-source bridge between **Meshtastic** and **Falcon Player (FPP)**. It allows a lighting installation to be monitored and controlled over a long-range LoRa mesh network without requiring Wi-Fi, cellular service, or Internet connectivity.

The project was created for the [**Gothic Folly Cathedral**](https://thegothicfolly.com) installation at [**Burning Man 2026**](https://burningman.org/), but it is intended to be useful for any installation using [**Falcon Player**](https://github.com/FalconChristmas/fpp), including holiday light displays, public art, museums, festivals, and other distributed lighting systems, including [xLights](https://xlights.org/).

The project acknowledges the great support from [**Burners Without Borders** (BWB)](https://burnerswithoutborders.org/) and [Burning Mesh](https://www.burningmesh.org/).

## Principal Maintainer

**Frank Cohen**

Creator and principal maintainer of Follyizer

---

## Goals

- Start and stop approved FPP playlists over Meshtastic
- Monitor the current show and playback status
- Send periodic health and status updates
- Operate reliably without Internet access
- Run as a lightweight service on Raspberry Pi
- Require no modifications to Falcon Player itself

---

## Architecture

```text
                 Meshtastic Network

          Operator Node
                │
         LoRa Mesh Network
                │
         Meshtastic Node
                │ USB
                ▼
      Raspberry Pi running FPP
      ┌───────────────────────────┐
      │        Follyizer          │
      │                           │
      │ • Receives commands       │
      │ • Validates requests      │
      │ • Controls FPP            │
      │ • Reports status          │
      └─────────────┬─────────────┘
                    │
            Falcon Player (FPP)
                    │
           Falcon Controller(s)
                    │
                 LED Pixels
```

---

## Initial Prototype

The first prototype is intentionally simple.

**Hardware**

- Raspberry Pi 400
- HDMI monitor with built-in speakers
- Heltec T114 Meshtastic node
- Heltec V3 Meshtastic node
- Falcon Player
- Python 3

The first experiment does **not** require LEDs or a Falcon controller.

Success is defined as:

1. Receiving a Meshtastic command.
2. Starting an approved FPP playlist.
3. Playing synchronized audio.
4. Returning status to the operator.

---

## Command Protocol

Commands use the `FZ` Follyizer text protocol designed for Meshtastic.

Example:

```text
FZ RUN TEST01 Q=42
```

Supported commands:

```text
FZ RUN <show> Q=<sequence>
FZ STOP Q=<sequence>
FZ STATUS Q=<sequence>
FZ BLACKOUT Q=<sequence>
```

Responses:

```text
FZ ACK Q=42 RUN TEST01

FZ NAK Q=42 REASON=UNKNOWN_SHOW

FZ STAT S=TEST01 P=PLAY T=01:24 Q=42
```

Only approved playlist identifiers may be executed.

---

## Safety

Follyizer intentionally does **not** execute arbitrary commands received over the radio.

Remote commands are translated through a local configuration file:

```yaml
shows:
  TEST01: Cathedral Test
  MAIN: Saturday Night Show
  AMBIENT: Ambient Loop
```

If a received show identifier is not present in the configuration, the command is rejected.

Additional protections include:

- Duplicate command detection
- Optional sender authorization
- Sequence number validation
- Direct-message support
- Periodic heartbeat/status messages

---

## Repository Layout

```text
follyizer/
├── follyizer/
│   ├── app.py
│   ├── commands.py
│   ├── config.py
│   ├── fpp_client.py
│   └── meshtastic_link.py
│
├── tests/
│
├── install.sh
├── uninstall.sh
├── follyizer.service
├── config.example.yaml
├── requirements.txt
└── README.md
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/frankcohen/follyizer.git
cd follyizer
```

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the example configuration:

```bash
cp config.example.yaml config.yaml
```

Edit the configuration for your installation.

Run:

```bash
python -m follyizer.app --config config.yaml
```

---

## Planned Features

- Falcon Player playlist control
- Meshtastic command interface
- Automatic status reports
- Web dashboard
- Playlist scheduling
- Health monitoring
- Logging and diagnostics
- Remote software updates
- Support for multiple installations
- MQTT integration

---

## Project Status

Follyizer is currently an experimental proof-of-concept under active development.

The initial target platform is:

- Raspberry Pi 400
- Raspberry Pi 4
- Falcon Player
- Meshtastic
- Heltec T114
- Heltec V3

---

## Contributing

Contributions, bug reports, feature requests, and deployment experiences are welcome.

If you deploy Follyizer on an art installation, festival, museum exhibit, or holiday display, we'd love to hear how you used it.

---

## License

GPL version 3
