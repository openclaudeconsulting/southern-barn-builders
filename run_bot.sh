#!/bin/bash
# Launcher for the Southern Barn Quote Bot.
# Ensures the local HTTP server is running (needed by generate_quote.sh), then starts the bot.
# Run this in a terminal and leave it open. Ctrl+C to stop.

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Start the quote HTML server in the background if it isn't already up
if ! curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/invoice-generator.html | grep -q "^2"; then
  echo "Starting local HTTP server on :8080..."
  nohup python -m http.server 8080 >/dev/null 2>&1 &
  sleep 2
fi

echo "Starting Discord bot (Ctrl+C to stop)..."
python discord_bot.py
