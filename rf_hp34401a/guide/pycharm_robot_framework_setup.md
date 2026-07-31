# PyCharm and Robot Framework setup

## 1. Install Python

Install Python 3.10–3.13 and verify:

```powershell
py -3.13 --version
```

Linux:

```bash
python3 --version
```

## 2. Open the project

Unpack `rf_hp34401a_v26.01.zip` and open the fixed internal folder `rf_hp34401a` in PyCharm.

## 3. Create the virtual environment

In PyCharm, open **Settings → Project → Python Interpreter → Add Interpreter → Add Local Interpreter → Virtualenv**. Use `.venv` inside the project.

Equivalent Windows command:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev,hardware]"
```

Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e '.[dev,hardware]'
```

## 4. Install a Robot Framework editor plugin

Install a maintained Robot Framework language-server plugin from **Settings → Plugins**. Restart PyCharm and confirm `.robot` files receive syntax highlighting, keyword completion, and navigation.

## 5. Configure a run configuration

Create a Python run configuration:

- Module name: `robot`
- Parameters: `--outputdir results examples/02_dc_voltage_limits.robot`
- Working directory: project root
- Interpreter: project `.venv`

For hardware VISA:

```text
--variable VISA_RESOURCE:GPIB0::22::INSTR examples/12_visa_gpib_connection.robot
```

For serial:

```text
--variable SERIAL_PORT:COM3 examples/11_rs232_connection.robot
```

## 6. Run and inspect results

Run the simulated example first. Open `results/log.html` and `results/report.html` in a browser.

## 7. Debug Python library code

Set a breakpoint in `rf_hp34401a/library.py`, use the Python run configuration above, and launch it in Debug mode. Robot calls will stop in the adapter before delegation to the core driver.

## Troubleshooting

- **Library not found:** verify PyCharm uses `.venv` and run `python -m pip install -e .`.
- **PyVISA backend missing:** install a vendor VISA runtime and the `visa` optional dependency.
- **GPIB resource absent:** verify the adapter and instrument in the vendor connection utility, then run `List VISA Resources`.
- **COM access denied:** close other terminal applications and confirm Device Manager port assignment.
- **Keyword not recognized by editor:** invalidate PyCharm caches after selecting the correct interpreter.
