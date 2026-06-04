# SQ-Discovery Windows Setup and Usage

This repo builds two Windows executables:

- `sq-discovery.exe`
- `sq-discovery-tray.exe`

They support:

- normal on-demand scans
- Windows service mode
- a tray companion that shows service/device status

Network requirement:

- multicast DNS must be allowed on UDP port `5353`
- the target device's advertised service port must also be allowed through firewalls, VLAN rules, and any network ACLs
- if discovery or service checks fail, confirm multicast traffic and port restrictions are not blocking traffic

## 1. Prerequisites

Install these on the Windows machine:

- Python 3.10 or newer
- PowerShell 5.1 or PowerShell 7
- Git

Optional, if you want to build the EXE yourself:

- Visual Studio Build Tools or a normal Windows Python install with `py`

## 2. Build The EXE

From the repo root:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\build-windows.ps1
```

If you want to do the steps manually:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install ifaddr zeroconf pywin32 pyinstaller pillow pystray
.\.venv\Scripts\python.exe -m PyInstaller sq-discovery.spec
.\.venv\Scripts\python.exe -m PyInstaller sq-discovery-tray.spec
```

PyInstaller prints a lot of status output; that is normal. The build only fails if it exits with a nonzero code.
If the build fails, check `pyinstaller-build.out.log` and `pyinstaller-build.err.log` in the repo root for the full PyInstaller output.

If the script picks the wrong interpreter or `py -3` resolves to the Microsoft Store alias, pass the real Python executable explicitly:

```powershell
.\build-windows.ps1 -PythonExe "C:\Path\To\Python.exe"
```

The EXE will be in:

```powershell
.\dist\sq-discovery.exe
```

The tray app will be in:

```powershell
.\dist\sq-discovery-tray.exe
```

## 3. On-Demand Scanning

Basic scan:

```powershell
.\dist\sq-discovery.exe --find
```

Scan one or more service types:

```powershell
.\dist\sq-discovery.exe --service-type _sq._tcp
.\dist\sq-discovery.exe --service-type _sq._tcp --service-type _http._tcp
```

Useful options:

- `--duration 60` scans for 60 seconds and exits
- `--v4-only` forces IPv4
- `--v6-only` forces IPv6
- `--json` prints discovered services as JSON
- `--debug` enables debug logging

Examples:

```powershell
.\dist\sq-discovery.exe --find --duration 60
.\dist\sq-discovery.exe --service-type _sq._tcp --json
.\dist\sq-discovery.exe --find --v4-only --debug
```

## 4. Windows Service

The Windows service name is:

- `sq-discovery`

The service should be set to start automatically when Windows boots.
It scans only `_sq._tcp.local.` and repeats the discovery pass every 1 second.
It writes current status to `C:\ProgramData\sq-discovery\state\status.json` so the tray app can show the current state.

Install it:

```powershell
.\install-service.ps1
```

Start it:

```powershell
.\dist\sq-discovery.exe --service start
```

Debug it in the console:

```powershell
.\dist\sq-discovery.exe --service debug
```

This runs the service logic in the foreground and prints startup errors directly to the terminal.

Stop it:

```powershell
.\dist\sq-discovery.exe --service stop
```

Remove it:

```powershell
.\dist\sq-discovery.exe --service remove
```

Service log file:

```powershell
C:\ProgramData\sq-discovery\logs\sq-discovery-service.log
```

Live device inventory:

```powershell
C:\ProgramData\sq-discovery\state\devices.json
```

The inventory file is rewritten so each device appears once, and updates replace the existing entry.

Service status file:

```powershell
C:\ProgramData\sq-discovery\state\status.json
```

Status fields:

- `service_running`
- `device_count`
- `devices_found`

Day marker used to decide whether files should be cleared on a new calendar day:

```powershell
C:\ProgramData\sq-discovery\state\service-day.txt
```

Service log rotation:

- `C:\ProgramData\sq-discovery\logs\sq-discovery-service.log`
- rotated every 1 hour
- up to 24 hourly log files are kept

Retention rule:

- same-day restarts keep the existing log and device inventory
- the next calendar day clears the previous day’s device inventory before writing fresh files
- `ProgramData` is used instead of `Program Files` so the service can write without permission problems
- the service keeps one inventory entry per device and suppresses duplicate logs for unchanged records
- the Windows service scans IPv4 only

Tray icon behavior:

- green check: service running and devices found
- red cross: service running but no devices found
- gray cross: service stopped

Run the tray app:

```powershell
.\dist\sq-discovery-tray.exe
```

The tray app reads `C:\ProgramData\sq-discovery\state\status.json` every second and updates the icon automatically.

To install the tray app to start automatically when a user logs in, run PowerShell as Administrator from the repo root:

```powershell
.\install-tray.ps1
```

To remove it later:

```powershell
Unregister-ScheduledTask -TaskName "sq-discovery-tray" -Confirm:$false
```

## 5. OnePe Discovery Script

Run the script from the repo root:

```powershell
.\onepe-discovery-upload.ps1
```

It uses the scan engine to:

- search for `_sq._tcp`
- find the `OnePe-POS001` service
- resolve the host name and IPv4 address
- run a `/health` check
- upload `Connectify_Commands.txt` to `/upload`

The service also maintains a live device inventory at:

```powershell
C:\ProgramData\sq-discovery\state\devices.json
```

That file is rewritten so each device appears once and updates replace the existing entry.

Before running it, edit these values in the script if needed:

- `$serviceName`
- `$serviceType`
- `$filePath`
- `$squadlScanPath`

## 6. Command-Line Reference

Supported options on `sq-discovery.exe`:

- `--find`
- `--service-type <type>` repeated as needed
- `--v4-only`
- `--v6-only`
- `--duration <seconds>`
- `--json`
- `--debug`
- `--service <install|start|stop|remove>`

Examples:

```powershell
.\dist\sq-discovery.exe --find
.\dist\sq-discovery.exe --find --json
.\dist\sq-discovery.exe --service-type _sq._tcp --duration 30
.\dist\sq-discovery.exe --service install
.\dist\sq-discovery.exe --service start
```

## 7. Troubleshooting

If discovery finds nothing:

- make sure the device is on the same local network
- make sure multicast/mDNS is allowed by the network
- try `--duration 60`
- try `--v4-only` if your network does not use IPv6

If the service does not start:

- run PowerShell as Administrator
- confirm the service was installed first
- confirm the service startup type is `Automatic`
- check `C:\ProgramData\sq-discovery\logs\sq-discovery-service.log`
- run `.\dist\sq-discovery.exe --service debug` and inspect the terminal output
  - `C:\ProgramData\sq-discovery\state\devices.json`
  - `C:\ProgramData\sq-discovery\state\startup-05-background-threads-started.txt`
  - if startup stops at `startup-00-svcdorun-entered.txt`, the service reached the entrypoint but failed before the next bootstrap step

If the tray icon does not update:

- confirm `C:\ProgramData\sq-discovery\state\status.json` exists
- restart `sq-discovery-tray.exe`
- check that the service is writing `device_count` and `devices_found`
