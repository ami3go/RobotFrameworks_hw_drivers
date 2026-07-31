# Installation Guide

## Supported environment

- Python 3.10–3.13
- Robot Framework 7.4.x
- Windows 11 or current Linux distributions
- Vötsch/SimServ-compatible chamber reachable over TCP, normally port 2049

## Install from the repository

```bash
python -m venv .venv
```

Activate the environment:

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

```bash
# Linux
source .venv/bin/activate
```

Install the project:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"
```

## Install from the included wheel

```bash
python -m pip install dist/robotframework_votsch_climate_chamber-26.2-py3-none-any.whl
```

## Verify installation

```bash
python -c "from votsch_climate_chamber import RELEASE_VERSION; print(RELEASE_VERSION)"
robot --version
python -m robot.libdoc votsch_climate_chamber.robot_library.VotschClimateChamberLibrary docs/VotschClimateChamberLibrary.html
```

Expected release output is `v26.02`.
