$ErrorActionPreference = "Stop"
python -m robot --pythonpath . --outputdir results-hardware @args tests/hardware/smoke_test.robot
