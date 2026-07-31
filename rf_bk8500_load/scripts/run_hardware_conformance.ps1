param(
    [string]$Port = "COM9",
    [int]$Baudrate = 9600,
    [string]$Model = "8500",
    [int]$Address = 0,
    [double]$Timeout = 1.0,
    [bool]$AutoDetectBaudrate = $false,
    [string]$BaudrateCandidates = "4800,9600,19200,38400",
    [double]$ProbeTimeout = 0.75,
    [bool]$AllowInputOn = $false,
    [bool]$AllowPersistentWrites = $false,
    [int]$SettingsRegister = 25,
    [int]$ListFileSlot = 8
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = [string](& (Join-Path $PSScriptRoot "ensure_environment.ps1"))
$Suite = Join-Path $Root "hardware_tests/01_all_library_keywords.robot"
$Out = Join-Path $Root "results/hardware_conformance"

Write-Host "BK8500 full keyword conformance"
Write-Host "Port=$Port PreferredBaudrate=$Baudrate AutoDetectBaudrate=$AutoDetectBaudrate Model=$Model Address=$Address"
Write-Host "AllowInputOn=$AllowInputOn AllowPersistentWrites=$AllowPersistentWrites"

New-Item -ItemType Directory -Force -Path $Out | Out-Null
$EvidenceFile = Join-Path $Out "software_versions.json"
& $Python -c "import datetime,importlib.metadata,json,platform,robot,sys; print(json.dumps({'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bk8500_load_distribution':importlib.metadata.version('bk8500-load'),'robot_framework':robot.__version__,'python':platform.python_version(),'platform':platform.platform()}, indent=2))" | Set-Content -Encoding UTF8 $EvidenceFile
Write-Host "Software evidence: $EvidenceFile"

& $Python -m robot --pythonpath $Root --outputdir $Out `
    --variable "PORT:$Port" `
    --variable "BAUDRATE:$Baudrate" `
    --variable "MODEL:$Model" `
    --variable "ADDRESS:$Address" `
    --variable "TIMEOUT:$Timeout" `
    --variable "AUTO_DETECT_BAUDRATE:$AutoDetectBaudrate" `
    --variable "BAUDRATE_CANDIDATES:$BaudrateCandidates" `
    --variable "PROBE_TIMEOUT:$ProbeTimeout" `
    --variable "ALLOW_INPUT_ON:$AllowInputOn" `
    --variable "ALLOW_PERSISTENT_WRITES:$AllowPersistentWrites" `
    --variable "SETTINGS_REGISTER:$SettingsRegister" `
    --variable "LIST_FILE_SLOT:$ListFileSlot" `
    $Suite
exit $LASTEXITCODE
