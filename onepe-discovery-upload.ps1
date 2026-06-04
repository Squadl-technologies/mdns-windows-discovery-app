param(
    [string]$ServiceName = "OnePe-POS001",
    [string]$ServiceType = "_sq._tcp",
    [string]$FilePath = "Connectify_Commands.txt",
    [string]$ExePath = ".\dist\sq-discovery.exe",
    [int]$DurationSeconds = 30
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $ExePath)) {
    throw "Executable not found at $ExePath. Build it first with .\build-windows.ps1"
}

$scanOutput = & $ExePath --service-type $ServiceType --duration $DurationSeconds --json 2>$null
if (-not $scanOutput) {
    throw "No services were discovered for $ServiceType"
}

$services = $scanOutput | ForEach-Object { $_ | ConvertFrom-Json }
$target = $services | Where-Object { $_.name -eq $ServiceName } | Select-Object -First 1
if (-not $target) {
    throw "Service '$ServiceName' was not found for type '$ServiceType'"
}

Write-Host "Discovered service:"
$target | ConvertTo-Json -Depth 6

if (-not (Test-Path $FilePath)) {
    throw "File not found: $FilePath"
}

Write-Host "This script is a placeholder for your HTTP workflow."
Write-Host "Target host: $($target.server)"
Write-Host "Target port: $($target.port)"
Write-Host "Resolved addresses: $($target.addresses -join ', ')"
Write-Host "Health check path: /health"
Write-Host "Upload path: /upload"
Write-Host "Upload file: $FilePath"
Write-Host ""
Write-Host "Use these details to perform the actual health check and upload in your environment."
