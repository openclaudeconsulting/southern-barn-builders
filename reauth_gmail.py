#!/usr/bin/env python3
"""
One-shot Gmail OAuth re-authentication.

Use when switching the Gmail account the quote bot drafts emails into.
Deletes the existing token.json and runs the OAuth consent flow.
A browser window will open — sign in with the target Google account
(e.g. gnp-steel-trusses@gmail.com) and grant access.

Usage (from a normal terminal, not pythonw):
    python reauth_gmail.py
"""

import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "token.json"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.send",
]


def main() -> None:
    if not CREDENTIALS_PATH.exists():
        sys.exit(f"ERROR: credentials.json not found at {CREDENTIALS_PATH}")

    if TOKEN_PATH.exists():
        TOKEN_PATH.unlink()
        print(f"Deleted old token: {TOKEN_PATH}")

    print("Opening browser for Google sign-in…")
    print("Sign in with gnp-steel-trusses@gmail.com and click Allow.")
    print()

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
    creds = flow.run_local_server(port=0)
    TOKEN_PATH.write_text(creds.to_json())

    print()
    print(f"Saved new token: {TOKEN_PATH}")
    print("Done. The bot will now create drafts in the newly-authorized inbox.")


if __name__ == "__main__":
    main()
