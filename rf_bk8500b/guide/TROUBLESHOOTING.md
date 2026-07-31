# Troubleshooting

## `No module named BK8500BLibrary`

Activate the project environment and install the repository in editable mode:

```bash
python -m pip install -e ".[dev]"
```

## Environment variable not found

Set `BK8500B_PORT` before running examples. Example on PowerShell:

```powershell
$env:BK8500B_PORT = "COM5"
```

## COM port access denied

Close vendor tools, serial terminals, or other processes using the same port.
Disconnect and reconnect the adapter if Windows retained a stale handle.

## Linux permission denied

Check the port owner and group:

```bash
ls -l /dev/ttyUSB0
```

Add the user to the appropriate serial group, commonly `dialout`, then sign out
and back in. Do not solve persistent permission issues by running the test suite
as root.

## Robot keyword not found

Regenerate Libdoc and confirm the active interpreter:

```bash
python scripts/generate_libdoc.py
python -m robot.libdoc BK8500BLibrary list
```

## Input remains enabled after a failed test

Use an independent bench-safe shutdown procedure. Software teardown is a
secondary safeguard, not a substitute for source current limiting and accessible
hardware shutdown controls.
