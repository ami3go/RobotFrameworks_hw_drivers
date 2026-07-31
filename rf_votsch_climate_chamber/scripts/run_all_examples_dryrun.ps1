$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
python -m robot --dryrun --pythonpath . --outputdir results/examples examples
exit $LASTEXITCODE
