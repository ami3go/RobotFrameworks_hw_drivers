# Robot Framework examples

Release 26.16 retains the same 55-keyword functional API that passed the preserved
physical v26.14 conformance run. These examples remain simulator-first and do
not enable hardware unless explicitly requested.

The examples are numbered in learning order and default to the built-in
simulator. Hardware mode must be selected explicitly and requires a reviewed
bench setup.

## Run from this folder on Windows PowerShell

```powershell
.\run_example.ps1 01_identity_and_limits
.\run_example.ps1 01_identity_and_limits -Simulated:$false -Port COM9
.\run_all_examples.ps1
```

## Run from the package root

```powershell
.\scripts\run_example.ps1 01_identity_and_limits
.\scripts\run_all_examples.ps1
```

The runners reuse a compatible activated project environment first, then create
or repair the package-private `.venv` when necessary. They
verify the availability of Robot Framework, pyserial, and `bk8500_load`, then
dry-run all delivered examples to validate keyword and standard-library
dependencies before starting a suite. If package installation is unavailable because the computer
is offline, run `scripts\setup_venv.ps1` after restoring package-index access.

Linux/macOS wrappers with the same names and `.sh` extension are also provided.
Examples 06–08 configure advanced functions but remain simulator-safe by
default.

## Example 13 — automatic baud detection

`13_automatic_baud_detection.robot` is hardware-only and skips in simulation.
Run it with:

```powershell
.\scripts\run_example.ps1 13_automatic_baud_detection `
    -Simulated:$false -Port COM12 -Baudrate 9600
```

The preferred rate is tried first; the suite logs the selected baud and
`baudrate_probe_attempts`.
