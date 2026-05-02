#!/usr/bin/env python3
"""Rocketmatter MCP setup — username/password token configuration."""

import getpass
import json
import os
import sys
import time
import requests
from pathlib import Path

CONFIG_DIR = Path.home() / ".rocketmatter-mcp"


def prompt(label, default="", secret=False):
    suffix = f" [{default}]" if default else ""
    if secret:
        val = getpass.getpass(f"{label}{suffix}: ").strip()
    else:
        val = input(f"{label}{suffix}: ").strip()
    return val or default


def grant_token(domain, install, username, password):
    base_url = f"{domain.rstrip('/')}/{install}/API_V2"
    url = f"{base_url}/Authentication.svc/json/GrantToken"
    resp = requests.post(url, json={"UserName": username, "Password": password})
    if resp.status_code == 200:
        return resp.json()
    raise RuntimeError(f"GrantToken failed ({resp.status_code}): {resp.text}")


def main():
    print("Rocketmatter MCP Setup")
    print("======================")
    print()
    print("You'll need your Rocketmatter domain, install path, username and password.")
    print("Example domain: https://app.rocketmatter.com")
    print("Example install: myfirm123")
    print()

    domain = prompt("Domain (e.g. https://app.rocketmatter.com)")
    install = prompt("Install (your firm path segment)")
    username = prompt("Username (email)")
    password = prompt("Password", secret=True)

    if not all([domain, install, username, password]):
        print("All fields are required.")
        sys.exit(1)

    print()
    print("Testing credentials...")
    try:
        tokens = grant_token(domain, install, username, password)
        tokens["expires_at"] = time.time() + 86400
        access_token = tokens.get("AccessToken", "")
        if not access_token:
            print(f"✗ No AccessToken in response: {tokens}")
            sys.exit(1)
        print("✓ Token obtained successfully.")
    except RuntimeError as e:
        print(f"✗ Failed: {e}")
        sys.exit(1)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    env_file = CONFIG_DIR / ".env"
    env_content = f"""# Rocketmatter MCP configuration
ROCKETMATTER_DOMAIN={domain}
ROCKETMATTER_INSTALL={install}
ROCKETMATTER_USERNAME={username}
ROCKETMATTER_PASSWORD={password}
"""
    env_file.write_text(env_content)
    os.chmod(env_file, 0o600)

    token_file = CONFIG_DIR / "tokens.json"
    token_file.write_text(json.dumps(tokens, indent=2))
    os.chmod(token_file, 0o600)

    print(f"✓ Config saved to {CONFIG_DIR}")
    print()
    print("Add to your Claude Desktop config:")
    print(json.dumps({
        "mcpServers": {
            "rocketmatter": {
                "command": "rocketmatter-mcp"
            }
        }
    }, indent=2))


if __name__ == "__main__":
    main()
