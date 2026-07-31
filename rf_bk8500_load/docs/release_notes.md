# Release notes — release 16 (`rf_bk8500_load_v26.16`)

Package: `rf_bk8500_load_v26.16.zip`, unpacking to `rf_bk8500_load/`.  
Python distribution: **`bk8500-load==26.16.0`**.  
Lifecycle: Phase 1, Gate 5 maintenance revision 11.

## Main change: automatic baud-rate detection

`Open Load Connection` can now discover the BK8500 front-panel baud rate when
the configured rate does not respond.

Two equivalent forms are supported:

```robotframework
Open Load Connection    port=COM12    baudrate=AUTO
```

```robotframework
Open Load Connection    port=COM12    baudrate=9600
...    auto_detect_baudrate=${TRUE}
...    baudrate_candidates=4800,9600,19200,38400
```

The requested numeric rate is always tried first. Remaining unique candidates
are then tried in the provided order. Only the read-only product-information
query (`0x6A`) is sent during probing.

A candidate rate is accepted only when:

- a complete, checksum-valid response frame is received;
- the frame is not merely a local echo;
- model and serial number are non-empty;
- two consecutive identities match, unless confirmation is explicitly disabled.

Every failed candidate closes its serial handle before the next rate is opened.
The successful connection remains open and normal transaction timeout/retry
settings are restored.

## New connection evidence

`Get Load Connection Info` now includes:

- `baudrate`;
- `baudrate_auto_detected`;
- `baudrate_probe_attempts`.

Each attempt records the baud rate, PASS/FAIL result, error details, and the
accepted identity where applicable.

## Backward compatibility

The default remains deterministic:

```robotframework
Open Load Connection    port=COM12    baudrate=9600
```

With `auto_detect_baudrate=${FALSE}`, no fallback probing occurs. Simulation
mode bypasses serial probing. The public keyword count remains 55.

## Hardware runner

PowerShell:

```powershell
.\scripts\run_hardware_conformance.ps1 -Port COM12 `
    -Baudrate 9600 -AutoDetectBaudrate:$true
```

Linux/macOS:

```bash
./scripts/run_hardware_conformance.sh /dev/ttyUSB0 9600 true
```

A new Robot example is delivered as
`examples/13_automatic_baud_detection.robot`.

## Verification

The release passes 114 pytest checks and includes automated coverage for:

- preferred rate success;
- fallback to another supported rate;
- de-duplication and ordering;
- unsupported-rate rejection before opening a port;
- echo/timeout/inconsistent-identity rejection;
- closing every failed candidate;
- restoring normal timeout and retry settings on success;
- Robot Framework `baudrate=AUTO` integration;
- simulation bypass.

The preserved v26.14 physical report remains the verified protocol baseline:
56/56 tests passed on model 8500, serial `1687710135`, firmware `1.84`, COM12 at
9600 baud. Physical confirmation of fallback probing at a deliberately changed
front-panel baud rate remains recommended for final feature closure.
