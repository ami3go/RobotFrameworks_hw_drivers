<#
.SYNOPSIS
  Single-command installer for every RobotFrameworks_hw_drivers package.

.EXAMPLE
  .\install.ps1                # create .\.venv, install all packages (runtime only)
.EXAMPLE
  .\install.ps1 -Dev           # also install each package's dev/test/docs extras
.EXAMPLE
  .\install.ps1 -NoVenv        # install into the currently active Python env
.EXAMPLE
  .\install.ps1 -VenvDir .venv311 -Python python3.11

  Requires Python 3.11+ so that every package (rf_votsch_climate_chamber needs
  >=3.11) can be installed into the same environment.
#>

param(
    [switch]$Dev,
    [switch]$NoVenv,
    [string]$VenvDir = ".venv",
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

$Packages = @(
    "rf_agilent33220a",
    "rf_agilent34411a",
    "rf_bk8500b",
    "rf_bk8500_load",
    "rf_ea_ps9000t",
    "rf_eresistor",
    "rf_hp34401a",
    "rf_keysight_n6700",
    "rf_ngi_n83624",
    "rf_phidget_relay",
    "rf_picoscope_scope",
    "rf_slcan",
    "rf_tbs1000c",
    "rf_votsch_climate_chamber"
)

$DevExtras = @{
    rf_agilent33220a         = "dev"
    rf_agilent34411a         = "dev"
    rf_bk8500b                = "dev"
    rf_bk8500_load            = "dev"
    rf_ea_ps9000t             = "dev"
    rf_eresistor              = "test,yaml"
    rf_hp34401a               = "dev,hardware"
    rf_keysight_n6700         = "dev,docs"
    rf_ngi_n83624             = "dev,docs"
    rf_phidget_relay          = "dev"
    rf_picoscope_scope         = "dev"
    rf_slcan                  = "dev"
    rf_tbs1000c               = "dev"
    rf_votsch_climate_chamber = "dev,docs"
}

if (-not $NoVenv) {
    if (-not (Test-Path $VenvDir)) {
        Write-Host "==> Creating virtual environment at $VenvDir"
        & $Python -m venv $VenvDir
    }
    $ActivateScript = Join-Path $VenvDir "Scripts\Activate.ps1"
    . $ActivateScript
}

Write-Host "==> Using $((Get-Command python).Source) ($(python --version))"
python -m pip install --upgrade pip

foreach ($pkg in $Packages) {
    if ($Dev) {
        $target = "./$pkg[$($DevExtras[$pkg])]"
    } else {
        $target = "./$pkg"
    }
    Write-Host "==> Installing $target"
    python -m pip install -e "$target"
}

Write-Host ""
Write-Host "==> All $($Packages.Count) packages installed."
if (-not $NoVenv) {
    Write-Host "    Activate with: $ActivateScript"
}
