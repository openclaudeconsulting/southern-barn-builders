@echo off
REM Double-click this to remove the bot's auto-start entry and stop it.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall-autostart.ps1"
echo.
pause
