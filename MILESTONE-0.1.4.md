# Follyizer v0.1.4 — FZ STOP

Milestone 5 adds:

```text
FZ STOP Q=5
```

Protocol keywords remain case-insensitive, so this also works:

```text
Fz stop q=5
```

Follyizer sends FPP the `Stop Now` command and replies directly:

```text
FZ ACK Q=5 STOP
```

If FPP returns an HTTP error:

```text
FZ NAK Q=5 REASON=FPP_ERROR
```

`STATUS` and `RUN` continue to work. `BLACKOUT` remains unimplemented.

## Test

Start the 60-second Test01 playlist:

```text
Fz run Test01 q=4
```

While it is running, send:

```text
Fz stop q=5
```

Expected Pi log:

```text
MESHTASTIC RX from=!be49a244 text='Fz stop q=5'
FPP STOP requested_by=!be49a244
MESHTASTIC TX to=!be49a244 text='FZ ACK Q=5 STOP'
```

FPP's web UI should immediately return to Idle.

Then send:

```text
Fz status q=6
```

The returned status should contain `P=IDLE`.
