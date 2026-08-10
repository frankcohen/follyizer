# Follyizer v0.1.1 — FPP Status Integration

Milestone 2 adds one capability to the working persistent Meshtastic process:

- Follyizer polls `http://127.0.0.1/api/fppd/status`.
- It logs a compact FPP summary immediately at startup and every 10 seconds.
- Meshtastic remains connected through the same long-lived process.
- Temporary FPP errors are logged but do not terminate Follyizer.

It still does **not** parse or reply to `FZ` commands.

## Expected output

```text
Follyizer connected: node=!043a241c name=Meshtastic 241c hardware=HELTEC_V3
FPP STATUS state=idle playlist=- elapsed=00:00 remaining=00:00 volume=70 temp=36.5 powerBad=False version=9.5
Listening for Meshtastic text. Press Ctrl-C to stop.
```

Every 10 seconds another `FPP STATUS` line should appear.

While it is running, send a normal Meshtastic message from another node. You should
still see:

```text
MESHTASTIC RX from=!be49a244 text='Good evening from Brisbane'
```

This proves the persistent Meshtastic connection and FPP polling can run together.
