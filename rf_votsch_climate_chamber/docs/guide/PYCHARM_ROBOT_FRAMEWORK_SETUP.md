# PyCharm and Robot Framework Setup

This guide configures PyCharm to edit, run, and debug the library and Robot Framework suites.

## 1. Open the fixed project folder

Open this folder in PyCharm:

```text
rf_votsch_climate_chamber/
```

Do not open only the inner Python package folder. The repository root contains `pyproject.toml`, examples, tests, scripts, and documentation.

## 2. Create the project interpreter

1. Open **File → Settings → Project → Python Interpreter**.
2. Choose **Add Interpreter → Add Local Interpreter**.
3. Select **Virtualenv Environment**.
4. Create the environment as `.venv` inside the project root.
5. Use a supported Python version, preferably Python 3.13 or 3.12.
6. Open the PyCharm terminal and run:

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev,docs]"
```

Editable installation is important: changes in `votsch_climate_chamber/` become available immediately without reinstalling the package.

## 3. Install Robot Framework IDE support

Open **File → Settings → Plugins → Marketplace** and install a maintained Robot Framework language-support plugin. Restart PyCharm when requested.

The plugin should provide:

- `.robot` syntax highlighting;
- keyword completion;
- variable navigation;
- suite/test discovery;
- run configurations.

Plugin availability and names can change. Use a plugin compatible with your installed PyCharm version and Robot Framework 7.

## 4. Configure source and test paths

The project uses no `src/` folder. The Python package is directly in the repository root:

```text
rf_votsch_climate_chamber/
└── votsch_climate_chamber/
```

Normally the editable installation is sufficient. If PyCharm cannot resolve imports:

1. right-click the repository root;
2. select **Mark Directory As → Sources Root**;
3. confirm that the selected interpreter is `.venv`.

## 5. Create a Robot run configuration

1. Open **Run → Edit Configurations**.
2. Add a **Python** configuration if the Robot plugin does not provide a dedicated Robot configuration.
3. Set module name to:

```text
robot
```

4. Set parameters for acceptance tests:

```text
--pythonpath . --outputdir results tests/robot
```

5. Set the working directory to the repository root.
6. Select the `.venv` interpreter.

For example dry-run validation, use:

```text
--dryrun --pythonpath . --outputdir results/examples examples
```

## 6. Configure pytest

1. Open **File → Settings → Tools → Python Integrated Tools**.
2. Select `pytest` as the default test runner.
3. Right-click `tests/unit` and run the tests.

Command-line equivalent:

```bash
python -m pytest --cov=votsch_climate_chamber --cov-report=term-missing
```

## 7. Generate keyword documentation

Run:

```bash
python -m robot.libdoc \
  votsch_climate_chamber.robot_library.VotschClimateChamberLibrary \
  docs/VotschClimateChamberLibrary.html
```

Open the generated HTML file in a browser. Generation must succeed without a connected chamber.

## 8. Use the simulator before real hardware

Run the unit and acceptance suites first:

```bash
python -m pytest
python -m robot --pythonpath . --outputdir results tests/robot
```

The acceptance suite uses the fake chamber support code and does not require network access to real equipment.

## 9. Configure a real-chamber test safely

Use Robot variables instead of hardcoding site-specific addresses:

```robot
*** Variables ***
${CHAMBER_IP}      192.168.1.50
${TEMP_MIN}        -40
${TEMP_MAX}        180
```

Run control-changing hardware tests only with the explicit safety variable:

```bash
robot --pythonpath . \
  --variable CHAMBER_IP:192.168.1.50 \
  --variable ALLOW_CHAMBER_CONTROL:True \
  --outputdir results/hardware \
  tests/hardware/smoke_test.robot
```

Before running, verify independent chamber limits, an operator-approved setpoint, DUT condition, and emergency-stop access.

## 10. Debugging notes

- A normal Python debugger can step through `robot_library.py` and `driver.py` when Robot is launched as the `robot` Python module.
- Enable Robot `DEBUG` log level with `--loglevel DEBUG` for reconnect and protocol diagnostics.
- Do not commit chamber IP addresses, operator names, or site-specific limits unless they are intentionally public.
- Keep generated output under `results/`; it is excluded by `.gitignore`.
