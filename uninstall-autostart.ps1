# uninstall-autostart.ps1
# Removes the auto-start scheduled task and stops the running supervisor/bot.

$ErrorActionPreference = 'Continue'
$TaskName = 'GPSteelTrussesQuoteBot'

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Write-Host "Stopping and removing scheduled task '$TaskName'..."
  Stop-ScheduledTask  -TaskName $TaskName -ErrorAction SilentlyContinue
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  Write-Host "Scheduled task removed." -ForegroundColor Green
} else {
  Write-Host "No scheduled task '$TaskName' is registered."
}

# Kill any lingering supervisor / bot / http.server pythonw processes so the
# uninstall is complete (the scheduled task above only stops itself; child
# processes can keep running otherwise).
$matches = Get-CimInstance Win32_Process -Filter "Name='pythonw.exe' OR Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'bot_supervisor|discord_bot|http\.server' }

if ($matches) {
  Write-Host "Stopping running supervisor / bot processes..."
  foreach ($p in $matches) {
    Write-Host ("  pid {0}: {1}" -f $p.ProcessId, $p.CommandLine.Substring(0, [Math]::Min(80, $p.CommandLine.Length)))
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
  }
} else {
  Write-Host "No supervisor / bot processes are running."
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
