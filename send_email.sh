#!/bin/bash
# Thin bash wrapper around send_email.py.
# By default creates a Gmail draft in southern.barn.services@gmail.com.
# Pass --send to actually send (otherwise it's draft-only so Carson can review).
#
# Examples:
#   ./send_email.sh --to "foo@example.com" --subject "Quote" --body "Hi..."
#   ./send_email.sh --to "foo@example.com" --subject "Quote" --body "..." \
#                   --attachment "../INVOICE Nathan Bloom.pdf"
#   ./send_email.sh --to "..." --subject "..." --body "..." --send

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python "$SCRIPT_DIR/send_email.py" "$@"
