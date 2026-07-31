# rf-ngi-n83624

Robot Framework library for the **NGI N83624 24-channel battery/cell simulator**, built on the supplied typed Python SCPI driver.

Release label: **v26.01**  
Python package version: **26.1** (PEP 440 normalizes `26.01` to `26.1`).

## Capabilities

- TCP, UDP, channel-specific UDP, RS232, and deterministic emulator sessions.
- Multiple named connections with active-session switching.
- Source, charge, SOC, and sequence configuration keywords.
- Voltage/current/power/resistance/capacity measurements and assertions.
- OCP, OVP, OPP, capture-rate, heartbeat, recovery, and communication-health keywords.
- Explicit output arming gate plus finite voltage/current limit enforcement.
- Guarded raw SCPI access.
- Best-effort all-channel safe shutdown and automatic suite cleanup.
- Optional JSONL audit log for safety-relevant operations.
- Fourteen Robot Framework examples, unit tests, Robot acceptance tests, GitHub Actions, GitHub Pages, PyCharm setup guide, history, and implementation review.

## Installation

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,docs]"
```

Linux/macOS:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e '.[dev,docs]'
```

## Robot Framework import

```robot
*** Settings ***
Library    rf_ngi_n83624.library.NGI_N83624
```

## Offline smoke example

```robot
*** Settings ***
Library           rf_ngi_n83624.library.NGI_N83624    auto_close_on_suite_end=${False}
Suite Setup       Open N83624 Emulator    emu    max_voltage_v=5.0    max_current_ma=500
Suite Teardown    Close All N83624 Connections

*** Test Cases ***
Safe Source Cycle
    Configure Source Mode    1    3.7    100    AUTO    output=${False}
    Arm Channel Output       1    ENABLE OUTPUT
    Enable Channel Output    1
    Channel Output Should Be On    1
    Disable Channel Output   1
```

## Real TCP connection

```robot
Open N83624 TCP Connection
...    bench
...    host=192.168.0.123
...    port=7000
...    max_voltage_v=5.0
...    max_current_ma=500
...    audit_log_path=${OUTPUT DIR}${/}ngi_audit.jsonl
```

Output enabling is blocked until the channel has finite voltage/current limits and is explicitly armed with `Arm Channel Output    <channel>    ENABLE OUTPUT`.

## Run tests

Windows:

```powershell
.\scripts\run_tests.ps1
```

Linux/macOS:

```bash
./scripts/run_tests.sh
```

Direct commands:

```bash
python -m pytest
robot --outputdir build/robot tests/robot/acceptance.robot
ruff check .
python -m build
```

## Run examples

```powershell
.\scripts\run_example.ps1 .\examples\01_emulator_smoke.robot
```

```bash
./scripts/run_example.sh examples/01_emulator_smoke.robot
```

Hardware examples contain bench-specific IP addresses or serial ports and must be reviewed before use.

## Safety boundary

This package is a software control layer. It does not replace an emergency stop, fusing, contactors, independent voltage/current monitoring, wiring review, DUT risk analysis, or hardware interlocks. The supplied source documentation identifies several SCPI details that still require verification on the exact instrument and firmware.

**Offline verification is included. Real N83624 HIL qualification is not claimed in v26.01.** Follow [Hardware qualification](guide/HARDWARE_QUALIFICATION.md) before production deployment.

## Project layout

```text
rf_ngi_n83624/            Robot Framework library package
ngi_n83624/               inherited typed Python core driver
examples/                  14 Robot Framework examples
scripts/                   setup, test, build, and example runners
tests/                     Python and Robot acceptance tests
task/                      hardened generation/implementation task and readiness review
history/                   revision history
review/                    implementation code review and verification evidence
guide/                     PyCharm, Robot Framework, safety, and HIL guides
docs/                      GitHub Pages / MkDocs content
.github/workflows/         CI and Pages workflows
reference/                 supplied Python-driver task and documentation
```

## Release documentation

- [Final task specification](task/ROBOT_FRAMEWORK_DRIVER_TASK_v26.01.md)
- [Task readiness review](task/TASK_READINESS_REVIEW.md)
- [Implementation review](review/IMPLEMENTATION_REVIEW_v26.01.md)
- [Major fixes](review/MAJOR_FIXES_v26.01.md)
- [PyCharm and Robot Framework setup](guide/PYCHARM_ROBOT_FRAMEWORK_SETUP.md)
- [Hardware qualification](guide/HARDWARE_QUALIFICATION.md)
- [Release history](history/v26.01.md)
