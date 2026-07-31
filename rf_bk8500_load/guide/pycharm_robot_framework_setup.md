# PyCharm and Robot Framework setup


**Current wheel:** `bk8500_load-26.16.0-py3-none-any.whl`.

## 1. Open the project

Extract the package so the project root remains exactly
`rf_bk8500_load/`, then open that folder in PyCharm.

## 2. Create the virtual environment

In **Settings → Project → Python Interpreter**, add a new virtual environment
using Python 3.9 or newer. Keep the environment inside the project as `.venv`.

From the PyCharm terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e ".[dev]"
```

Linux/macOS:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e '.[dev]'
```

The editable install exposes `BK8500Library` while keeping source changes live.

## 3. Configure Robot Framework support

Install the **Robot Framework Language Server** or another maintained Robot
Framework plugin from PyCharm's Plugins page. Point the plugin to the same
`.venv` interpreter used by the project.

The package uses a flat source layout. PyCharm should resolve `bk8500_load/`
after the editable install. Optionally right-click `bk8500_load/` and select
**Mark Directory As → Sources Root** to improve direct source navigation.

## 4. Run a simulated example

Windows PowerShell:

```powershell
.\scripts\run_example.ps1 01_identity_and_limits
```

Linux/macOS:

```bash
./scripts/run_example.sh 01_identity_and_limits
```

Open `results/examples/01_identity_and_limits/report.html` after the run.

## 5. Create a PyCharm run configuration

Create a **Python** run configuration:

- Module name: `robot`
- Parameters: `--outputdir results/pycharm examples/02_constant_current.robot`
- Working directory: project root
- Interpreter: project `.venv`

For hardware, add parameters such as:

```text
--variable SIMULATED:False --variable PORT:COM4
```

## 6. Run automated checks

```powershell
.\.venv\Scripts\python -m pytest -q
.\.venv\Scripts\python -m robot --outputdir results/atest atest
```

Do not run hardware examples until the connection guide and bench safety limits
have been reviewed.
