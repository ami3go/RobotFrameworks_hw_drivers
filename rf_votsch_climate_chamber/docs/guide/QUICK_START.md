# Quick Start

## 1. Create the environment

Windows PowerShell:

```powershell
.\scripts\setup_dev_environment.ps1
```

Linux:

```bash
./scripts/setup_dev_environment.sh
```

## 2. Validate without hardware

```powershell
.\scripts\run_all_examples_dryrun.ps1
```

or:

```bash
./scripts/run_all_examples_dryrun.sh
```

## 3. Run one example

List examples:

```bash
python scripts/run_example.py --list
```

Dry-run example 1:

```bash
python scripts/run_example.py 1 --dryrun
```

Run a configured example:

```bash
python scripts/run_example.py 1 --variable CHAMBER_IP:192.168.1.50
```

Examples that control real hardware must be reviewed and supplied with appropriate temperature limits and safety variables.
