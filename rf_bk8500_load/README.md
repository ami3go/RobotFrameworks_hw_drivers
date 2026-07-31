# BK8500Library — Robot Framework driver for B&K Precision 8500 series DC loads

RFDS-oriented Robot Framework driver for B&K Precision 8500-series DC
electronic loads, with serial hardware transport, automatic baud detection,
an in-process simulator, safety interlocks, verification keywords, AI-readable
contracts, examples, hardware conformance tests, and preserved evidence.

**Package release 16:** `rf_bk8500_load_v26.16.zip`  
**Internal root:** `rf_bk8500_load/`  
**Python distribution:** `bk8500-load==26.16.0`  
**Lifecycle:** Phase 1, Gate 5 maintenance revision 11

## Automatic baud-rate detection

The driver supports the BK8500 firmware rates 4800, 9600, 19200, and 38400.
A deterministic numeric connection remains the default:

```robotframework
Open Load Connection    port=COM12    baudrate=9600
```

Enable fallback probing with either form:

```robotframework
Open Load Connection    port=COM12    baudrate=AUTO
```

```robotframework
Open Load Connection    port=COM12    baudrate=9600
...    auto_detect_baudrate=${TRUE}
...    baudrate_candidates=4800,9600,19200,38400
...    probe_timeout=0.75
```

The requested numeric baud is tried first. Detection sends only the read-only
product-information query. A rate is accepted after a valid, non-empty identity
is received twice consistently by default. Exact local echoes, malformed
frames, empty identities, and timeouts are rejected. Failed port handles are
closed before the next rate is tried.

Inspect the result:

```robotframework
${connection}=    Get Load Connection Info
Log    Detected baud: ${connection}[baudrate]
Log    Probe attempts: ${connection}[baudrate_probe_attempts]
```

## Verified physical baseline

The preserved Robot Framework report for driver `26.14.0` passed **56/56**
tests on a physical B&K Precision 8500:

| Field | Evidence |
|---|---|
| Public keyword tests | 55 passed, 0 failed |
| Persistence workflow | 1 passed, 0 failed |
| Device | Model 8500, serial `1687710135`, firmware `1.84` |
| Link | COM12, 9600 baud, address 0 |
| Robot / Python | Robot Framework 7.4.2 / Python 3.13.5 |
| Safe teardown | PASS |

The original report and machine-readable indexes are under
[`evidence/hardware_conformance/v26.14_com12_2026-07-28/`](evidence/hardware_conformance/v26.14_com12_2026-07-28/).
Release v26.16 adds baud detection on top of that verified protocol path.
Fallback probing has automated simulator/unit coverage; a physical run at a
non-9600 front-panel rate is the remaining feature-specific confirmation.

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -e ".[dev]"
.\scripts\run_example.ps1 01_identity_and_limits
```

Hardware identity at a fixed baud:

```powershell
.\scripts\run_example.ps1 01_identity_and_limits -Simulated:$false -Port COM12
```

Automatic baud example from the package root:

```powershell
.\scripts\run_example.ps1 13_automatic_baud_detection `
    -Simulated:$false -Port COM12 -Baudrate 9600
```

## Complete hardware keyword test

Fixed baud:

```powershell
.\scripts\run_hardware_conformance.ps1 -Port COM12 -Baudrate 9600
```

Automatic fallback:

```powershell
.\scripts\run_hardware_conformance.ps1 -Port COM12 `
    -Baudrate 9600 -AutoDetectBaudrate:$true
```

Full profile, including input enable and persistent writes:

```powershell
.\scripts\run_hardware_conformance.ps1 -Port COM12 `
    -AutoDetectBaudrate:$true `
    -AllowInputOn:$true `
    -AllowPersistentWrites:$true
```

Persistent mode overwrites settings register 25 and list file slot 8 by
default. Expected complete result: **56 passed, 0 failed**.

## Package contents

| Path | Purpose |
|---|---|
| `bk8500_load/` | Protocol, transports, driver, and Robot keyword library |
| `ai/` | RFDS-017 contract/lock, RFDS-018 example, RFDS-019 specification, lifecycle documents |
| `examples/` | Thirteen safe-by-default Robot examples |
| `hardware_tests/` | 55 keyword tests, persistence workflow, and serial diagnostic |
| `evidence/` | Preserved physical conformance evidence and machine-readable indexes |
| `scripts/` | Cross-platform setup and execution launchers |
| `history/` | Release-by-release change descriptions |
| `review/` | Code, evidence, compliance, and readiness reviews |
| `guide/` | PyCharm, Robot Framework, hardware, and troubleshooting guides |
| `docs/` | GitHub Pages and user/developer documentation |

The package uses a flat source layout: `rf_bk8500_load/bk8500_load/`. There is
no intermediate `src/` directory.

## Driver capabilities

The library exposes 55 keywords covering connection management, remote
ownership, protection, CC/CV/CW/CR regulation, transient/list/battery
functions, triggering, settings storage, measurement, stability polling,
and pass/fail oracles.

The machine contract is `ai/ai_contract.yaml` and can also be located through:

```python
import bk8500_load
print(bk8500_load.contract_path())
print(bk8500_load.lock_path())
```

## Hardware warning

The rear DB9 carries TTL-level signalling, not standard RS-232 levels. Use the
intended USB-to-TTL adapter or an electrically equivalent interface. The driver
asserts DTR and RTS before and after opening, waits one second, and rejects
exact local echoes while waiting for the real device response.

## Documentation

- [Release notes](RELEASE_NOTES.md)
- [User guide](docs/user_guide.md)
- [Hardware setup](guide/hardware_connection.md)
- [Troubleshooting](guide/troubleshooting.md)
- [Examples](examples/README.md)
- [AI integration](ai/README.md)
- [Keyword reference](docs/BK8500Library.html)
- [Release history](history/release_v26.16.md)
- [Baud-detection review](review/release_v26.16_baud_detection_review.md)
- [Release readiness](review/release_v26.16_release_readiness.md)

## Licence

MIT. See [LICENSE](LICENSE). This project is not affiliated with or endorsed by
B&K Precision.
