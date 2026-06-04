param(
    [string]$TaskName = "sq-discovery-tray"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$trayPath = (Resolve-Path (Join-Path $repoRoot "dist\sq-discovery-tray.exe")).Path

if (-not (Test-Path $trayPath)) {
    throw "Tray executable not found at $trayPath. Build the tray app first."
}

$action = New-ScheduledTaskAction -Execute $trayPath
$trigger = New-ScheduledTaskTrigger -AtLogOn
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger $trigger -Principal $principal
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force

Write-Host "Registered scheduled task '$TaskName' for $trayPath"
