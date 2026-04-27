#!/usr/bin/env python3
"""
Supervisor for the G&P Steel Trusses Discord quote bot.

Starts (and keeps alive) two long-running processes:

  1. The local HTTP server on :8080 — needed by generate_quote.sh so the
     headless Chrome PDF render can fetch the invoice template.
  2. discord_bot.py — listens to the #to-do Discord channel and dispatches
     each new message to full_quote.sh.

Designed to run via pythonw.exe from a Windows scheduled task at user logon
(see install-autostart.ps1) so the bot is always available without anyone
keeping a terminal open. All output is appended to bot.log alongside this
script. The bot is auto-restarted with a 10-second backoff if it exits.

Run manually for debugging:
    python bot_supervisor.py
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
LOG_FILE = SCRIPT_DIR / "bot.log"
HTTP_PORT = 8080
RESTART_DELAY_SECONDS = 10
HTTP_STARTUP_TIMEOUT_SECONDS = 10

# CREATE_NO_WINDOW: hide the console window for any subprocess we launch on
# Windows (otherwise a black cmd window would flash for the HTTP server etc.)
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def log(msg: str) -> None:
    line = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def http_port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            return s.connect_ex(("127.0.0.1", port)) == 0
        except OSError:
            return False


def start_http_server() -> subprocess.Popen | None:
    """Bring up the local HTTP server if it isn't already listening."""
    if http_port_is_open(HTTP_PORT):
        log(f"HTTP server already up on :{HTTP_PORT}, reusing it.")
        return None

    log(f"Starting HTTP server on :{HTTP_PORT}...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(HTTP_PORT)],
        cwd=str(SCRIPT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=CREATE_NO_WINDOW,
    )
    # Poll until the server accepts connections (max ~10s)
    deadline = time.monotonic() + HTTP_STARTUP_TIMEOUT_SECONDS
    while time.monotonic() < deadline:
        time.sleep(0.5)
        if http_port_is_open(HTTP_PORT):
            log(f"HTTP server ready on :{HTTP_PORT} (pid {proc.pid}).")
            return proc
    log("WARNING: HTTP server didn't accept connections within "
        f"{HTTP_STARTUP_TIMEOUT_SECONDS}s; bot will start anyway.")
    return proc


def run_bot_loop() -> None:
    """Run discord_bot.py in a forever-loop, restarting on any exit."""
    bot_script = SCRIPT_DIR / "discord_bot.py"
    if not bot_script.exists():
        log(f"FATAL: {bot_script} not found.")
        sys.exit(1)

    while True:
        log("Launching discord_bot.py ...")
        try:
            with LOG_FILE.open("a", encoding="utf-8") as f:
                proc = subprocess.run(
                    [sys.executable, str(bot_script)],
                    cwd=str(SCRIPT_DIR),
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    creationflags=CREATE_NO_WINDOW,
                )
            log(f"discord_bot.py exited with code {proc.returncode}. "
                f"Restarting in {RESTART_DELAY_SECONDS}s ...")
        except Exception as e:  # pragma: no cover — defensive
            log(f"discord_bot.py crashed: {type(e).__name__}: {e}")
        time.sleep(RESTART_DELAY_SECONDS)


def main() -> None:
    log("=" * 60)
    log(f"Supervisor starting up (Python {sys.version.split()[0]}).")
    start_http_server()
    run_bot_loop()


if __name__ == "__main__":
    main()
