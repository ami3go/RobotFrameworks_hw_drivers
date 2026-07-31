$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$PrivatePython = Join-Path $Root ".venv\Scripts\python.exe"
$Setup = Join-Path $PSScriptRoot "setup_venv.ps1"
$env:RF_BK8500_ROOT = $Root

function Test-DriverEnvironment([string]$Candidate) {
    if (-not $Candidate -or -not (Test-Path $Candidate -PathType Leaf)) {
        return $false
    }
    & $Candidate -c "import importlib.metadata as m, os, sys; sys.path.insert(0, os.environ['RF_BK8500_ROOT']); import robot, serial, bk8500_load; assert m.version('bk8500-load') == bk8500_load.__version__" 2>$null
    if ($LASTEXITCODE -ne 0) { return $false }
    $Smoke = Join-Path $Root "scripts\verify_library_import.robot"
    & $Candidate -m robot --dryrun --pythonpath $Root --output NONE --log NONE --report NONE $Smoke *> $null
    if ($LASTEXITCODE -ne 0) { return $false }
    $Examples = Join-Path $Root "examples"
    & $Candidate -m robot --dryrun --pythonpath $Root --output NONE --log NONE --report NONE $Examples *> $null
    if ($LASTEXITCODE -ne 0) { return $false }
    $HardwareSuite = Join-Path $Root "hardware_tests\01_all_library_keywords.robot"
    & $Candidate -m robot --dryrun --pythonpath $Root --output NONE --log NONE --report NONE $HardwareSuite *> $null
    return ($LASTEXITCODE -eq 0)
}

# Prefer a complete package-private environment. If the caller already has a
# suitable project environment activated, reuse it instead of requiring a
# second online installation.
$Candidates = @($PrivatePython)
if ($env:VIRTUAL_ENV) {
    $ActivePython = Join-Path $env:VIRTUAL_ENV "Scripts\python.exe"
    if ($ActivePython -ne $PrivatePython) { $Candidates += $ActivePython }
}
$SystemPython = Get-Command python -ErrorAction SilentlyContinue
if ($SystemPython) { $Candidates += $SystemPython.Source }

foreach ($Candidate in $Candidates | Select-Object -Unique) {
    if (Test-DriverEnvironment $Candidate) {
        Write-Output $Candidate
        return
    }
}

Write-Host "No complete Robot Framework environment was found. Repairing the package-private .venv..."
& $Setup | Out-Host
if (-not (Test-DriverEnvironment $PrivatePython)) {
    throw "Environment repair did not provide Robot Framework, pyserial, and bk8500_load."
}
Write-Output $PrivatePython
