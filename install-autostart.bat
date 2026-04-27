@echo off
REM Double-click this to install auto-start for the GNP quote bot.
REM Runs install-autostart.ps1 with the right ExecutionPolicy bypass so
REM Windows doesn't block it.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-autostart.ps1"
echo.
pause
