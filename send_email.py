#!/usr/bin/env python3
"""
Send or draft an email from southern.barn.services@gmail.com.

Uses OAuth credentials in <project_root>/credentials.json for the first-run
browser auth flow, then caches a refresh token in <project_root>/token.json.

Usage:
    python send_email.py --to "foo@example.com" --subject "..." --body "..."
    python send_email.py --to "..." --subject "..." --body "..." --send
    python send_email.py --to "..." --subject "..." --body "..." --attachment "path/to/file.pdf"

By default creates a draft (safer for review). Pass --send to actually send.
"""

import argparse
import base64
import mimetypes
import os
import sys
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/gmail.compose", "https://www.googleapis.com/auth/gmail.send"]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CREDENTIALS_PATH = PROJECT_ROOT / "credentials.json"
TOKEN_PATH = PROJECT_ROOT / "token.json"


def get_service():
    """Authenticate and return a Gmail API service. First run opens a browser."""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                sys.exit(f"ERROR: credentials.json not found at {CREDENTIALS_PATH}")
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
        print(f"Saved refreshable token to {TOKEN_PATH}")
    return build("gmail", "v1", credentials=creds)


def build_message(to, subject, body, attachments=None, sender=None):
    msg = EmailMessage()
    msg["To"] = to
    msg["Subject"] = subject
    if sender:
        msg["From"] = sender
    msg.set_content(body)

    for attachment in (attachments or []):
        path = Path(attachment)
        if not path.exists():
            sys.exit(f"ERROR: attachment not found: {attachment}")
        ctype, encoding = mimetypes.guess_type(str(path))
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(path, "rb") as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=path.name)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--to", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--body", required=True)
    ap.add_argument("--attachment", default=[], action="append", help="Path to a file to attach (can be repeated for multiple attachments)")
    ap.add_argument("--send", action="store_true", help="Actually send (default: save as draft)")
    ap.add_argument("--from", dest="sender", default=None, help="Override From header")
    args = ap.parse_args()

    service = get_service()
    message_body = build_message(args.to, args.subject, args.body, args.attachment, args.sender)


    try:
        if args.send:
            result = service.users().messages().send(userId="me", body=message_body).execute()
            print(f"SENT. Message id: {result.get('id')}")
        else:
            result = service.users().drafts().create(userId="me", body={"message": message_body}).execute()
            print(f"DRAFT created. Draft id: {result.get('id')}")
            print("Review at: https://mail.google.com/mail/u/0/#drafts")
    except HttpError as e:
        sys.exit(f"ERROR from Gmail API: {e}")


if __name__ == "__main__":
    main()
