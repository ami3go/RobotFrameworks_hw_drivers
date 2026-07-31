param(
    [switch]$ForceRecreate
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv"
$Python = Join-Path $Venv "Scripts\python.exe"

if ($ForceRecreate -and (Test-Path $Venv)) {
    Write-Host "Removing existing virtual environment: $Venv"
    Remove-Item -Recurse -Force $Venv
}

if (-not (Test-Path $Python)) {
    Write-Host "Creating driver virtual environment: $Venv"
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv $Venv
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $Venv
    }
    else {
        throw "Python 3 was not found. Install Python and ensure 'py' or 'python' is on PATH."
    }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $Python)) {
        throw "Failed to create the virtual environment at '$Venv'."
    }
}

Write-Host "Installing or repairing driver dependencies..."
& $Python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Failed to upgrade pip in '$Venv'." }

Push-Location $Root
try {
    & $Python -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) { throw "Failed to install the driver and its dependencies." }
}
finally {
    Pop-Location
}

& $Python -c "import robot, serial, bk8500_load"
if ($LASTEXITCODE -ne 0) {
    throw "Environment verification failed: Robot Framework, pyserial, or bk8500_load is unavailable."
}

Write-Host "Environment ready: $Python"
