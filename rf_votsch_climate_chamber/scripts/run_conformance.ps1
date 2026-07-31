$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
python "$Root\scripts\run_conformance.py"
exit $LASTEXITCODE
