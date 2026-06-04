param(
    [string]$ExePath = "",
    [string]$ServiceName = "sq-discovery"
)

$ErrorActionPreference = "Stop"

if (-not $ExePath) {
    $ExePath = (Resolve-Path ".\dist\sq-discovery.exe").Path
} else {
    $ExePath = (Resolve-Path $ExePath).Path
}

if (-not (Test-Path $ExePath)) {
    throw "Service executable not found at $ExePath. Build the service app first."
}

& $ExePath --service install
sc.exe config $ServiceName start= auto | Out-Host
sc.exe start $ServiceName | Out-Host

Write-Host "Installed '$ServiceName' as Automatic and started it."
