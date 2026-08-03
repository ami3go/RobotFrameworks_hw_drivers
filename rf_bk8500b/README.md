# RF BK8500B — Robot Framework Driver

Robot Framework library and bundled Python driver for B&K Precision 8500B
Series DC electronic loads. The Robot adapter exposes readable, safety-aware
keywords while keeping transport, SCPI framing, verification, state handling,
and safety policy in the underlying `bk8500b` driver.

| Item | Value |
|---|---|
| Release | **v26.04** |
| Release archive | `rf_bk8500b_v26.04.zip` |
| Fixed extracted root | `rf_bk8500b/` |
| Python distribution | `robotframework-bk8500b` 26.4.0 |
| Python | 3.10–3.13 |
| Robot Framework | 7.x |
| License | MIT |
| Hardware qualification | Pending real-instrument validation |

## Package standard

Every release uses a versioned outer archive and a stable inner folder:

```text
rf_bk8500b_v26.04.zip
└── rf_bk8500b/
```

This allows a newer release to replace the current extracted project directory
without changing IDE, CI, or test-suite paths.

## Quick start

Windows PowerShell:

```powershell
cd rf_bk8500b
.\scripts\setup_venv.ps1
$env:BK8500B_PORT = "COM5"
.\scripts\run_example.ps1 01
```

Windows Command Prompt:

```bat
cd rf_bk8500b
scripts\setup_venv.bat
scripts\run_example.bat 01 COM5
```

Linux:

```bash
cd rf_bk8500b
./scripts/setup_venv.sh
export BK8500B_PORT=/dev/ttyUSB0
./scripts/run_example.sh 01
```

Start with example `01`, which identifies the load without intentionally
enabling its input.

## Minimal Robot Framework suite

```robot
*** Settings ***
Library           rf_bk8500b.BK8500BLibrary
Suite Setup       Connect To Electronic Load    %{BK8500B_PORT}
Suite Teardown    Disconnect All Electronic Loads
Test Teardown     Disable Electronic Load Input

*** Test Cases ***
Sink One Ampere And Verify Supply Voltage
    Configure And Enable Load    CC    1.0    current_limit=1.2    power_limit=20
    Voltage Should Be Within Range    11.5    12.5
    Current Should Be Within Range    0.95    1.05
```

The bare `Library    BK8500BLibrary` import also still works for backward
compatibility, but `rf_bk8500b.BK8500BLibrary` is the recommended form — it
matches the `rf_<device>.<Device>Library` convention used across this
repository's drivers.

## Main keyword groups

| Group | Representative keywords |
|---|---|
| Connection | `Connect To Electronic Load`, `Switch Electronic Load`, `Disconnect All Electronic Loads` |
| Safety | `Configure And Enable Load`, `Disable Electronic Load Input`, `Clear Electronic Load Protection` |
| Fixed modes | `Set Electronic Load Mode`, `Set Current Setpoint`, `Set Voltage Setpoint`, `Set Power Setpoint`, `Set Resistance Setpoint` |
| Measurements | `Measure Voltage`, `Get Measurement Snapshot`, `Wait Until Measurement Is Within Range` |
| Assertions | `Voltage Should Be Within Range`, `Current Should Be Within Range`, `Power Should Be Within Range` |
| Logging | `Log Measurements To CSV`, `Export Diagnostic Snapshot` |
| Advanced | `Configure Transient Load`, `Trigger Electronic Load`, `Read Peak Measurements` |
| Diagnostics | `Run Electronic Load Health Check`, `Drain Electronic Load Error Queue`, `Run Electronic Load Self Test` |
| Expert | `Query Raw SCPI`, `Write Raw SCPI` |

The generated keyword reference is available at
[`docs/BK8500BLibrary.html`](docs/BK8500BLibrary.html), and the categorized
summary is in [`docs/KEYWORDS.md`](docs/KEYWORDS.md).

## AI planning contracts

The package includes a canonical RFDS-017 contract for automatic test planning:

- [`ai/bk8500b_ai_contract.yaml`](ai/bk8500b_ai_contract.yaml) describes all 74 public Robot keywords, exact signatures, states, resources, risks, errors, safety constraints, recovery sequences, verification oracles, and setup/teardown behavior.
- [`ai/bk8500b_ai_contract.lock`](ai/bk8500b_ai_contract.lock) is the SHA-256 lock for the public keyword surface.
- [`ai/rfds017.schema.json`](ai/rfds017.schema.json) is the project-local validation schema.
- [`bench/system_ai_contract.yaml`](bench/system_ai_contract.yaml) is an RFDS-018 bench-integration template. It remains `TEMPLATE_INCOMPLETE` until actual wiring, resources, DUT limits, and emergency procedures are reviewed for a specific bench.

Validate both contracts and detect interface drift:

```bash
python scripts/verify_ai_contract.py
```

See [`docs/AI_CONTRACT.md`](docs/AI_CONTRACT.md) and
[`docs/RFDS018_BENCH_TEMPLATE.md`](docs/RFDS018_BENCH_TEMPLATE.md).

## Examples

The `examples/` folder contains at least ten Robot Framework suites:

1. Instrument identification and capability inspection.
2. Constant-current operation.
3. Constant-voltage operation.
4. Constant-power operation.
5. Constant-resistance operation.
6. Waiting for a stable measurement range.
7. CSV measurement logging.
8. Dynamic/transient load operation.
9. Multiple loads using aliases.
10. Diagnostics and reviewed raw SCPI access.

Validate every example without hardware:

```bash
python scripts/run_all_examples.py
```

Run one example:

```bash
python scripts/run_example.py 01 --port COM5
```

The all-example runner uses Robot dry-run by default. Hardware execution requires
an explicit `--execute` option and all required port environment variables.

## Safety behavior

- Disconnect disables the electronic-load input by default.
- Driver write verification is enabled by default.
- Reconfiguration is blocked while input is active when required by driver policy.
- `Configure And Enable Load` validates configuration before enabling input and
  attempts input-off rollback if configuration fails.
- Short-circuit mode is disabled by default and requires explicit policy plus a
  confirmation phrase.
- Raw SCPI keywords can bypass high-level intent and should be isolated in
  reviewed Robot resource files.
- Software shutdown is not a substitute for source current limiting, correct
  wiring, suitable power ratings, or accessible hardware emergency shutdown.

Read [`docs/SAFETY.md`](docs/SAFETY.md) and
[`guide/HARDWARE_SETUP.md`](guide/HARDWARE_SETUP.md) before active-load tests.

## Development and validation

```bash
python -m pip install -e ".[dev]"
python scripts/verify_project_structure.py
python scripts/verify_ai_contract.py
python -m pytest
python -m robot --outputdir results/acceptance tests/robot/adapter_acceptance.robot
python -m robot --dryrun --outputdir results/dryrun examples
python -m ruff check BK8500BLibrary tests/test_robot_library.py tests/robot/FakeBK8500BLibrary.py scripts/build_release.py scripts/run_example.py scripts/run_all_examples.py scripts/verify_project_structure.py scripts/verify_ai_contract.py scripts/verify_release_artifacts.py scripts/generate_libdoc.py tests/test_ai_contract.py
python scripts/generate_libdoc.py
python -m build
python -m twine check dist/*
```

Real-hardware qualification is specified in
[`docs/HARDWARE_VALIDATION.md`](docs/HARDWARE_VALIDATION.md).

## Build the project-standard release ZIP

```bash
python scripts/build_release.py
```

For release v26.04, this creates:

```text
../rf_bk8500b_v26.04.zip
```

The builder verifies the required project structure, checks the example count,
excludes caches and local environments, and confirms that the ZIP has exactly one
root folder named `rf_bk8500b`.

## Repository layout

```text
rf_bk8500b/
├── BK8500BLibrary/       Robot Framework adapter
├── bk8500b/              Bundled Python driver
├── ai/                   RFDS-017 AI driver contract, schema, and interface lock
├── bench/                RFDS-018 system-contract template
├── history/              Revision-specific change descriptions
├── review/               Revision-specific code and package reviews
├── examples/             Robot Framework examples (10 minimum)
├── scripts/              Setup, test, example, build, and release scripts
├── guide/                PyCharm, Robot Framework, hardware, and troubleshooting guides
├── docs/                 Technical docs, Libdoc, and GitHub Pages site
├── tests/                Python and Robot acceptance tests
├── .github/workflows/    CI and GitHub Pages automation
├── CHANGELOG.md          Consolidated release history
├── PACKAGE_CONTENTS.md   Complete release-file manifest
├── release.json          Machine-readable release metadata
└── VERSION               Archive release number in YY.NN form
```

## Release records

- [`history/v26.04.md`](history/v26.04.md) — current change description.
- [`review/v26.04_ai_contract_review.md`](review/v26.04_ai_contract_review.md) — current AI-contract review.
- [`review/rfds017_rfds018_traceability.md`](review/rfds017_rfds018_traceability.md) — contract requirement traceability.
- [`CHANGELOG.md`](CHANGELOG.md) — consolidated changelog.
