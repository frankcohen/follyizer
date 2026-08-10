# Follyizer v0.1.3 — FZ RUN

Milestone 4 adds one command:

```text
FZ RUN TEST01 Q=2
```

`TEST01` is sent directly to Falcon Player as the playlist name.

There is intentionally:

- no alias file;
- no playlist translation table;
- no command-handler refactor.

For this experiment, use an FPP playlist name without spaces.

On success, Follyizer replies directly to the requesting node:

```text
FZ ACK Q=2 RUN TEST01
```

If FPP rejects or cannot execute the command:

```text
FZ NAK Q=2 REASON=FPP_ERROR
```

`FZ STATUS` from Milestone 3 remains enabled.

`STOP` and `BLACKOUT` remain unimplemented.

## Bench test

First create a playlist in the FPP web interface named:

```text
TEST01
```

It can contain a short audio/media item or other test content.

Run Follyizer:

```bash
cd ~/follyizer
source .venv/bin/activate
python -m follyizer.app --config config.yaml
```

From SPL3 send:

```text
FZ RUN TEST01 Q=2
```

Expected Pi log:

```text
MESHTASTIC RX from=!be49a244 text='FZ RUN TEST01 Q=2'
FPP RUN playlist=TEST01 requested_by=!be49a244
MESHTASTIC TX to=!be49a244 text='FZ ACK Q=2 RUN TEST01'
```

Then send:

```text
FZ STATUS Q=3
```

If the playlist is still running, the returned status should report `P=PLAYING`
and `S=TEST01`.


## Case handling

Follyizer commands are case-insensitive.

All of these are equivalent:

```text
FZ RUN TEST01 Q=2
fz run TEST01 q=2
Fz Run TEST01 Q=2
```

The playlist name itself is preserved exactly as typed.

For example:

```text
fz run Test01 q=2
```

passes this exact playlist name to FPP:

```text
Test01
```

and replies:

```text
FZ ACK Q=2 RUN Test01
```

This allows easy command entry from a phone without changing the case of FPP playlist names.
