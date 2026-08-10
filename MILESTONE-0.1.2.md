# Follyizer v0.1.2 — FZ STATUS

Milestone 3 adds the first live Follyizer command.

Send this from another Meshtastic node:

```text
FZ STATUS Q=1
```

Follyizer immediately queries FPP and sends a direct reply to the requesting node:

```text
FZ STAT S=- P=IDLE T=00:00/00:00 V=70 C=35 PWR=OK Q=1
```

Ordinary Meshtastic chat continues to be logged and ignored by the command parser.

`RUN`, `STOP`, and `BLACKOUT` are recognized by the parser but intentionally return:

```text
FZ NAK Q=<n> REASON=NOT_IMPLEMENTED
```

They will be implemented in later milestones.

## Test

```bash
cd ~/follyizer
source .venv/bin/activate
python -m follyizer.app --config config.yaml
```

From another node send:

```text
FZ STATUS Q=1
```

The Pi log should show both receive and transmit lines, and the requesting node should
receive the `FZ STAT ... Q=1` reply.

Periodic local FPP polling every 10 seconds remains enabled.
