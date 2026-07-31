# Installation

## Base installation

```bash
python -m venv .venv
python -m pip install -e .
```

## Hardware extras

```bash
python -m pip install -e ".[visa]"    # VISA/GPIB
python -m pip install -e ".[serial]"  # RS-232
```

PyVISA is an API layer. Install a compatible vendor VISA runtime separately for physical GPIB/USB/VXI-11 access.
