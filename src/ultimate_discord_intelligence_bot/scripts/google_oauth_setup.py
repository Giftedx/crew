#!/usr/bin/env python3
"""
Generate a Google Drive OAuth token (user account) for the bot to use.

Prerequisites:
- Create OAuth 2.0 Client ID (Desktop app) in Google Cloud Console.
- Download the client secret JSON and place it at: $CONFIG_DIR/google-oauth-client.json
  or provide path via --client-secrets.
- Scopes: https://www.googleapis.com/auth/drive

This script opens a local browser to authorize and writes the token JSON to:
$CONFIG_DIR/google-oauth-token.json (default) or --token-path.

Usage:
  python -m ultimate_discord_intelligence_bot.scripts.google_oauth_setup \
    [--client-secrets /path/to/client.json] [--token-path /path/to/token.json]

Env toggles:
  GOOGLE_OAUTH_TOKEN_PATH  # overrides default token path

After success, set GOOGLE_AUTH_METHOD=oauth and restart the bot.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from ultimate_discord_intelligence_bot.settings import CONFIG_DIR

# Lazy imports to keep runtime light if user never uses OAuth
try:
    # isort: off - keep grouped Google auth imports
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    # isort: on
except Exception as exc:  # pragma: no cover - env dependent
    print("Missing google OAuth libraries. Install with: pip install google-auth-oauthlib google-api-python-client")
    print(f"Details: {exc}")
    sys.exit(1)

SCOPES = ["https://www.googleapis.com/auth/drive"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Google Drive OAuth token")
    parser.add_argument(
        "--client-secrets",
        type=Path,
        default=CONFIG_DIR / "google-oauth-client.json",
        help="Path to OAuth client secrets JSON (Desktop app)",
    )
    parser.add_argument(
        "--token-path",
        type=Path,
        default=Path(os.getenv("GOOGLE_OAUTH_TOKEN_PATH", str(CONFIG_DIR / "google-oauth-token.json"))),
        help="Where to write the OAuth token JSON",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Use console-based OAuth flow (for headless servers)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.client_secrets.exists():
        print(f"Client secrets not found at: {args.client_secrets}")
        print("Create an OAuth 2.0 Client ID (Desktop app) and download JSON.")
        return 2

    creds = None
    if args.token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(args.token_path), SCOPES)
        except Exception:
            creds = None

    if not creds or not creds.valid:
        if creds and getattr(creds, "expired", False) and getattr(creds, "refresh_token", None):
            try:
                creds.refresh(Request())
            except Exception as exc:
                print(f"Refresh failed: {exc}. Falling back to interactive flow…")
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(str(args.client_secrets), SCOPES)
            if args.console:
                print("Starting console-based OAuth flow…")
                if hasattr(flow, "run_console"):
                    creds = flow.run_console()
                else:
                    # Manual console flow for environments without run_console
                    auth_url, _ = flow.authorization_url(
                        prompt="consent", access_type="offline", include_granted_scopes="true"
                    )
                    print("Open this URL in a browser, approve access, then paste the authorization code below:\n")
                    print(auth_url)
                    code = input("Authorization code: ").strip()
                    flow.fetch_token(code=code)
                    creds = flow.credentials
            else:
                print("Starting local-server OAuth flow on a random port…")
                creds = flow.run_local_server(port=0)

        # Save token
        args.token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(args.token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        print(f"✅ Saved OAuth token to {args.token_path}")

    # Quick sanity: print the associated email if available
    try:
        data = json.loads(creds.to_json())
        email = data.get("id_token") or "<user>"
        print("Token generated for:", email)
    except Exception:
        pass

    print("Next steps:")
    print("  1) export GOOGLE_AUTH_METHOD=oauth")
    print(f'  2) export GOOGLE_OAUTH_TOKEN_PATH="{args.token_path}"')
    print("  3) Restart the bot and retry the upload")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
