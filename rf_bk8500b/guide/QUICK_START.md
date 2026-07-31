# Quick Start

## Windows 11

```powershell
cd rf_bk8500b
.\scripts\setup_venv.ps1
$env:BK8500B_PORT = "COM5"
.\scripts\run_example.ps1 01
```

Command Prompt alternative:

```bat
cd rf_bk8500b
scripts\setup_venv.bat
scripts\run_example.bat 01 COM5
```

## Linux

```bash
cd rf_bk8500b
./scripts/setup_venv.sh
export BK8500B_PORT=/dev/ttyUSB0
./scripts/run_example.sh 01
```

## First safe test

Start with `01_identify.robot`. It performs identification and capability reads
without enabling the electronic-load input. Proceed to active-load examples only
after checking the supply, wiring, polarity, current limit, power limit, and DUT
safe operating area.
