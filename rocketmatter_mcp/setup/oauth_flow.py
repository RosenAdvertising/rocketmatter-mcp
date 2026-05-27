#!/usr/bin/env python3
"""Setup for rocketmatter-mcp — fetches and saves a user token via the LCS API."""

import json
import os
import sys
import time
from getpass import getpass
from pathlib import Path

import requests

BASE_URL = os.environ.get("ROCKETMATTER_BASE_URL", "https://app.rocketmatter.net")
API_KEY = os.environ.get("ROCKETMATTER_API_KEY", "")
CONFIG_DIR = Path.home() / ".rocketmatter-mcp"


def main():
    print("=== rocketmatter-mcp Setup ===\n")

    api_key = API_KEY
    if not api_key:
        api_key = input("LCS API Key: ").strip()
        if not api_key:
            print("Error: API key required.")
            sys.exit(1)

    username = os.environ.get("ROCKETMATTER_USERNAME", "").strip()
    if not username:
        username = input("Rocketmatter username (email): ").strip()

    password = os.environ.get("ROCKETMATTER_PASSWORD", "").strip()
    if not password:
        password = getpass("Rocketmatter password: ")

    print("\nFetching user token...")
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    )

    resp = session.post(
        f"{BASE_URL}/v1/lookups/user-token",
        json={
            "username": username,
            "password": password,
        },
    )

    if resp.status_code != 200:
        print(f"Error: Token request failed ({resp.status_code}): {resp.text[:200]}")
        sys.exit(1)

    data = resp.json()
    token = data.get("access_token", "")
    if not token:
        print(f"Error: No access_token in response: {data}")
        sys.exit(1)

    tokens = {
        "access_token": token,
        "expires_at": time.time() + data.get("expires_in", 17999),
    }

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    token_file = CONFIG_DIR / "tokens.json"
    with open(token_file, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(token_file, 0o600)

    print(f"\nToken saved to {token_file}")
    print("Run 'rocketmatter-mcp-verify' to test the connection.")


if __name__ == "__main__":
    main()
