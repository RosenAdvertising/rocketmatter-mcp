#!/usr/bin/env python3
"""One-command OAuth setup for rocketmatter-mcp.
Opens the browser, captures the callback, exchanges the code, saves tokens.

PREREQUISITE: The Rocketmatter OAuth app must have this redirect URI registered:
  http://127.0.0.1:8769/callback
Update it at app.rocketmatter.net under Integrations > OAuth App settings.
"""

import json
import os
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs

import requests

BASE_URL = os.environ.get("ROCKETMATTER_BASE_URL", "https://app.rocketmatter.net")
CLIENT_ID = os.environ.get("ROCKETMATTER_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ROCKETMATTER_CLIENT_SECRET", "")
REDIRECT_URI = os.environ.get("ROCKETMATTER_REDIRECT_URI", "http://127.0.0.1:8769/callback")
AUTHORIZE_URL = f"{BASE_URL}/OAuth/authorize"
TOKEN_URL = f"{BASE_URL}/api/ext/auth/token"
CONFIG_DIR = Path.home() / ".rocketmatter-mcp"

_auth_code: str | None = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            _auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorization complete. You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h2>No code received. Please try again.</h2>")

    def log_message(self, *args):
        pass


def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Error: ROCKETMATTER_CLIENT_ID and ROCKETMATTER_CLIENT_SECRET must be set.")
        sys.exit(1)

    print("=== rocketmatter-mcp OAuth Setup ===\n")

    auth_params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
    }
    auth_url = f"{AUTHORIZE_URL}?{urlencode(auth_params)}"

    print("Opening browser for Rocketmatter authorization...")
    print(f"If the browser doesn't open, visit:\n{auth_url}\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("127.0.0.1", 8769), _CallbackHandler)
    print("Waiting for Rocketmatter to redirect back (port 8769)...")
    server.handle_request()

    if not _auth_code:
        print("Error: No authorization code received.")
        sys.exit(1)

    print("Exchanging code for tokens...")
    resp = requests.post(TOKEN_URL, data={
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": _auth_code,
        "redirect_uri": REDIRECT_URI,
    })

    if resp.status_code != 200:
        print(f"Token exchange failed ({resp.status_code}): {resp.text}")
        sys.exit(1)

    tokens = resp.json()
    tokens["expires_at"] = time.time() + tokens.get("expires_in", 17999)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    token_file = CONFIG_DIR / "tokens.json"
    with open(token_file, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(token_file, 0o600)

    print(f"\n✓ Tokens saved to {token_file}")
    print("\nRun 'rocketmatter-mcp-verify' to test the connection.")


if __name__ == "__main__":
    main()
