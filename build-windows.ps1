param(
    [string]$PythonExe = "",
    [switch]$SkipInstall,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

if ($Clean) {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue .\build, .\dist
    Remove-Item -Force -ErrorAction SilentlyContinue .\pyinstaller-build.out.log, .\pyinstaller-build.err.log
}

if (-not (Test-Path .\.venv)) {
    $resolvedPython = $PythonExe
    if (-not $resolvedPython) {
        $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonCmd -and $pythonCmd.Source -and (Test-Path $pythonCmd.Source)) {
            $resolvedPython = $pythonCmd.Source
        }
    }
    if (-not $resolvedPython -and (Get-Command py -ErrorAction SilentlyContinue)) {
        $resolvedPython = "py -3"
    }
    if (-not $resolvedPython) {
        throw "No usable Python interpreter found. Pass -PythonExe with a full path to python.exe."
    }
    if ($resolvedPython -eq "py -3") {
        py -3 -m venv .venv
    } else {
        & $resolvedPython -m venv .venv
    }
}

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    throw "Virtual environment python not found at $python"
}

& $python -m pip install --upgrade pip

if (-not $SkipInstall) {
    & $python -m pip install ifaddr zeroconf pywin32 pyinstaller pillow pystray
}

& $python scripts\make_icon.py

$pyinstallerOutLog = Join-Path $repoRoot "pyinstaller-build.out.log"
$pyinstallerErrLog = Join-Path $repoRoot "pyinstaller-build.err.log"
foreach ($logPath in @($pyinstallerOutLog, $pyinstallerErrLog)) {
    if (Test-Path $logPath) {
        Remove-Item $logPath -Force
    }
}

foreach ($spec in @("sq-discovery.spec", "sq-discovery-tray.spec")) {
    $pyinstallerArgs = @("-m", "PyInstaller", $spec)
    $process = Start-Process -FilePath $python -ArgumentList $pyinstallerArgs -WorkingDirectory $repoRoot -NoNewWindow -PassThru -Wait -RedirectStandardOutput $pyinstallerOutLog -RedirectStandardError $pyinstallerErrLog
    if ($process.ExitCode -ne 0) {
        foreach ($logPath in @($pyinstallerOutLog, $pyinstallerErrLog)) {
            if (Test-Path $logPath) {
                Get-Content $logPath
            }
        }
        throw "PyInstaller failed with exit code $($process.ExitCode) for $spec"
    }
}

foreach ($logPath in @($pyinstallerOutLog, $pyinstallerErrLog)) {
    if (Test-Path $logPath) {
        Get-Content $logPath
    }
}

Write-Host "Build complete. Output is in .\dist\sq-discovery.exe"
