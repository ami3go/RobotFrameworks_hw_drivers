# PyCharm Setup for Robot Framework and BK8500B

## 1. Open the repository

Open the extracted `rf_bk8500b` folder as the PyCharm project. Do not open its
parent directory; the repository root contains `pyproject.toml`.

## 2. Configure the interpreter

1. Open **File > Settings > Project > Python Interpreter**.
2. Select **Add Interpreter > Add Local Interpreter**.
3. Choose **Virtualenv Environment**.
4. Use `<project>/.venv` as the location.
5. Select a Python 3.10–3.13 base interpreter.
6. Open the PyCharm terminal and run:

```powershell
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 3. Install Robot Framework editor support

In **File > Settings > Plugins > Marketplace**, install a maintained Robot
Framework language-support plugin compatible with your PyCharm version. Restart
PyCharm after installation. Plugin availability and names can change; verify that
the selected plugin supports `.robot` syntax, keyword navigation, and the active
Python interpreter.

## 4. Mark the project correctly

The project intentionally has no `src/` directory. Keep both Python packages at
the repository root:

- `BK8500BLibrary/`
- `bk8500b/`

Do not mark either package as a separate Sources Root. Installing the project in
editable mode gives Robot Framework and PyCharm the same import behavior.

## 5. Add a Robot run configuration

Create **Run > Edit Configurations > Python**:

- **Name:** `Robot - Identify BK8500B`
- **Module name:** `robot`
- **Parameters:** `--outputdir results examples/01_identify.robot`
- **Working directory:** project root
- **Python interpreter:** project `.venv`
- **Environment variables:** `BK8500B_PORT=COM5`

For dry-run validation, use:

```text
--dryrun --outputdir results/dryrun examples
```

## 6. Add a pytest run configuration

Create a Pytest configuration with the project root as working directory and
`tests` as target. Hardware-marked tests must not be run unless the test bench is
prepared.

## 7. Useful files

- `examples/` — executable Robot suites.
- `docs/BK8500BLibrary.html` — generated keyword reference.
- `docs/SAFETY.md` — safety behavior and dangerous-operation policy.
- `guide/HARDWARE_SETUP.md` — bench preparation checklist.
