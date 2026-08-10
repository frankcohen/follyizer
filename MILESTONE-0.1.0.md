# Follyizer v0.1.0 — Persistent Meshtastic Connection

This milestone intentionally does one thing:

- opens `/dev/ttyUSB0` once;
- keeps that serial connection open;
- logs each received Meshtastic text message;
- shuts down cleanly on Ctrl-C, SIGTERM, or service stop.

It does **not** parse `FZ` commands or control FPP yet.

## Run manually on FPP

```bash
cd ~/follyizer
source .venv/bin/activate
cp -n config.example.yaml config.yaml
vi config.yaml
python -m follyizer.app --config config.yaml
```

Expected startup resembles:

```text
Connecting to Meshtastic node at /dev/ttyUSB0
Meshtastic serial connection established
Follyizer connected: node=!043a241c name=Meshtastic 241c hardware=HELTEC_V3
Listening for Meshtastic text. Press Ctrl-C to stop.
```

A received message resembles:

```text
MESHTASTIC RX from=!be49a244 text='Hi'
```

Only one process may own `/dev/ttyUSB0`. Stop `meshtastic --info`,
`002_receive.py`, or other serial tests before running Follyizer.
