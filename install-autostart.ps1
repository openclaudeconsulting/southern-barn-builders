# install-autostart.ps1
# Registers bot_supervisor.py as a Windows scheduled task so the Discord
# quote bot + local HTTP server start silently at every user logon.
#
# Run once per machine. Use uninstall-autostart.ps1 to remove.
#
# Easiest way to run: double-click install-autostart.bat (which calls this
# script with the right ExecutionPolicy bypass).

$ErrorActionPreference = 'Stop'

$TaskName    = 'GPSteelTrussesQuoteBot'
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Supervisor  = Join-Path $ScriptDir 'bot_supervisor.py'

if (-not (Test-Path $Supervisor)) {
  Write-Host "ERROR: bot_supervisor.py not found at $Supervisor" -ForegroundColor Red
  exit 1
}

# Locate Python. Prefer pythonw.exe (no console window) when available so the
# task runs completely invisibly.
$PythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
  Write-Host "ERROR: python.exe not found in PATH. Install Python or add it to PATH first." -ForegroundColor Red
  exit 1
}
$PythonDir = Split-Path -Parent $PythonCmd.Source
$Pythonw   = Join-Path $PythonDir 'pythonw.exe'
if (-not (Test-Path $Pythonw)) {
  Write-Host "WARN: pythonw.exe not found alongside python.exe; using python.exe (may briefly flash a console window)." -ForegroundColor Yellow
  $Pythonw = $PythonCmd.Source
}

Write-Host "Project dir : $ScriptDir"
Write-Host "Supervisor  : $Supervisor"
Write-Host "Python      : $Pythonw"
Write-Host ""

# Tear down any prior registration so reinstalls are idempotent
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Write-Host "Removing existing scheduled task '$TaskName'..."
  Stop-ScheduledTask  -TaskName $TaskName -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# Build the task
$Action = New-ScheduledTaskAction `
  -Execute $Pythonw `
  -Argument ('"{0}"' -f $Supervisor) `
  -WorkingDirectory $ScriptDir

$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Settings: keep it lean. Auto-restart if it fails. Don't kill on battery.
# Don't impose an execution time limit (the bot is meant to run forever).
$Settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RestartCount 3 `
  -RestartInterval (New-TimeSpan -Minutes 1) `
  -ExecutionTimeLimit (New-TimeSpan -Days 0)

$Principal = New-ScheduledTaskPrincipal `
  -UserId $env:USERNAME `
  -LogonType Interactive `
  -RunLevel Limited

Register-ScheduledTask `
  -TaskName    $TaskName `
  -Action      $Action `
  -Trigger     $Trigger `
  -Settings    $Settings `
  -Principal   $Principal `
  -Description 'Auto-starts the G&P Steel Trusses Discord quote bot + local HTTP server at user logon.' | Out-Null

Write-Host "Registered task '$TaskName' (trigger: at user logon)." -ForegroundColor Green
Write-Host ""
Write-Host "Starting it now so you don't have to log out and back in..."
Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 5

# Show state
$Task = Get-ScheduledTask -TaskName $TaskName
Write-Host ("Task state  : {0}" -f $Task.State)

# Quick health check on the HTTP server it should have brought up
try {
  $resp = Invoke-WebRequest -Uri 'http://localhost:8080/invoice-generator.html' -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
  Write-Host ("HTTP server : up (HTTP {0})" -f $resp.StatusCode) -ForegroundColor Green
} catch {
  Write-Host "HTTP server : not yet responding (give it a few more seconds, then check bot.log)." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================================"
Write-Host "Done. The bot will now auto-start at every login."
Write-Host ""
Write-Host "Useful commands:"
Write-Host "  Tail logs   : Get-Content '$ScriptDir\bot.log' -Wait -Tail 50"
Write-Host "  Stop bot    : Stop-ScheduledTask  -TaskName $TaskName"
Write-Host "  Start bot   : Start-ScheduledTask -TaskName $TaskName"
Write-Host "  Uninstall   : .\uninstall-autostart.ps1"
Write-Host "================================================================"
