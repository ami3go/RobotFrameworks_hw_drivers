# Troubleshooting


## Current verified baseline

Release 26.16 retains the v26.14 transport path that passed 56/56 physical
tests on COM12 and adds optional baud probing. A blank identity or echo-only timeout is still a real
connection failure; the passing report contained model 8500, serial
`1687710135`, and firmware `1.84`.

## No response or timeout

- Verify the instrument baud rate and selected COM/TTY port.
- Confirm the adapter is TTL-level, not a normal RS-232 cable.
- Close vendor utilities or serial terminals that may own the port.
- Inspect the error for DTR/RTS assertion failure.

## Permission denied on Linux

Add the user to the serial-device group used by the distribution, commonly
`dialout`, then sign out and back in.

## PyCharm cannot resolve BK8500Library

Confirm the project interpreter is `.venv`, run `pip install -e .`, and verify
that the root `bk8500_load/` directory is visible to the interpreter.

## Robot command not found

Use the interpreter explicitly:

```text
python -m robot --outputdir results examples/01_identity_and_limits.robot
```

## Example changes a real load unexpectedly

All delivered examples default to simulation. Hardware mode should only be
selected explicitly with `SIMULATED:False`. Keep suite teardown enabled and do
not remove `Reset Load To Safe State` or `Close All Load Connections`.

## `Log Dictionary` keyword not found

Use the v26.10 or newer shared example resource. It imports Robot Framework's
standard `Collections` library. For a copied standalone suite, add this setting:

```robotframework
*** Settings ***
Library    Collections
```


## Exact request packet received as the response

An exact copy of a write request is local adapter echo, not a BK8500
acknowledgement. A successful write must return command byte `0x12` and status
byte `0x80`.

Run:

```powershell
python .\hardware_tests\02_serial_echo_diagnostic.py --port COM12
```

The v26.14+ transport discards a write echo and waits for the actual device
response. If no status frame follows, verify the selected COM port, adapter RX
path, cable wiring, instrument address, and front-panel baud rate.

## Unknown or changed baud rate

Run with `baudrate=AUTO` or `auto_detect_baudrate=${TRUE}`. Check the
`baudrate_probe_attempts` field returned by `Get Load Connection Info`.

- Timeout at every rate: verify COM port, TTL adapter, DTR/RTS, cable and device address.
- Local echo at every rate: RX sees the adapter echo but no instrument response.
- Inconsistent identity: unstable framing or wrong address; the rate is deliberately rejected.
- Unsupported candidate: only 4800, 9600, 19200 and 38400 are accepted.
