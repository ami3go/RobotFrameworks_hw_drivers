# PyCharm and Robot Framework Setup

1. Open the fixed project root `rf_votsch_climate_chamber`.
2. Create `.venv` with Python 3.11+.
3. Select `.venv` as the project interpreter.
4. Run `.venv/Scripts/python.exe -m pip install -e .[dev,docs]` on Windows or
   `.venv/bin/python -m pip install -e .[dev,docs]` on Linux.
5. Install the Robot Framework Language Server or IntelliBot plugin.
6. Set the plugin interpreter to the same `.venv`.
7. Verify `python -m robot --version` and run example 01.
