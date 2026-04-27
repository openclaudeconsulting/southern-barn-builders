@echo off
REM Double-click this to re-authenticate the quote bot's Gmail account.
REM A browser will open. Sign in with gnp-steel-trusses@gmail.com and Allow.
REM This is a one-time step when you want to switch which inbox the bot
REM creates drafts in.

cd /d "%~dp0"
python reauth_gmail.py
echo.
pause
