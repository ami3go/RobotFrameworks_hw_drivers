# PyCharm and Robot Framework setup

1. Install the official Phidget22 desktop driver and verify both boards in
   Phidget Control Panel. Record their unique serial numbers.
2. Open this fixed root folder (`rf_phidget_relay`) as a PyCharm project.
3. Create a Python 3.9+ virtual environment in **Settings → Python Interpreter**.
4. In PyCharm Terminal run `python -m pip install -e ".[dev]"`.
5. Optionally install the Robot Framework Language Server or IntelliBot plugin.
6. Copy an example and replace `123456` and `654321` with the real serials.
7. Run `python -m robot --outputdir results examples/02_single_channel.robot`.

For a normal, non-editable install use `python -m pip install .`. Run Robot
through `python -m robot` to ensure it uses the same interpreter as the package.

