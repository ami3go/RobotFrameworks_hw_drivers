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
& (Join-Path (Split-Path -Parent $PSScriptRoot) "scripts/run_hardware_conformance.ps1") `
    -Port $Port -Baudrate $Baudrate -Model $Model -Address $Address -Timeout $Timeout `
    -AutoDetectBaudrate:$AutoDetectBaudrate -BaudrateCandidates $BaudrateCandidates -ProbeTimeout $ProbeTimeout `
    -AllowInputOn:$AllowInputOn -AllowPersistentWrites:$AllowPersistentWrites `
    -SettingsRegister $SettingsRegister -ListFileSlot $ListFileSlot
exit $LASTEXITCODE
