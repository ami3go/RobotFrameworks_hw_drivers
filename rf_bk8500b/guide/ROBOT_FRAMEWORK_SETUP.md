# Robot Framework Setup

## 1. Install Python

Install Python 3.10–3.13. On Windows, enable **Add Python to PATH** during setup.
Verify:

```bash
python --version
```

## 2. Create the project environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 3. Verify Robot Framework and keyword discovery

```bash
python -m robot --version
python -m robot.libdoc BK8500BLibrary list
```

Generate the complete HTML keyword reference:

```bash
python scripts/generate_libdoc.py
```

Open `docs/BK8500BLibrary.html` in a browser.

## 4. Configure the instrument port

Windows PowerShell:

```powershell
$env:BK8500B_PORT = "COM5"
```

Windows Command Prompt:

```bat
set BK8500B_PORT=COM5
```

Linux:

```bash
export BK8500B_PORT=/dev/ttyUSB0
```

For the two-load example, also set `BK8500B_PORT_A` and `BK8500B_PORT_B`.

## 5. Run tests

Read-only identification example:

```bash
python scripts/run_example.py 01 --port COM5
```

Robot dry-run of every example, without hardware access:

```bash
python scripts/run_all_examples.py
```

Library acceptance tests using a fake instrument:

```bash
python -m robot tests/robot/adapter_acceptance.robot
```

Complete automated checks:

```bash
python -m pytest
python -m robot --dryrun examples
python -m ruff check BK8500BLibrary tests/test_robot_library.py tests/robot/FakeBK8500BLibrary.py scripts/build_release.py scripts/run_example.py scripts/run_all_examples.py scripts/verify_project_structure.py scripts/verify_release_artifacts.py scripts/generate_libdoc.py
```
