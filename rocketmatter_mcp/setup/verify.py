#!/usr/bin/env python3
"""Verify Rocketmatter MCP credentials."""

import json
import sys
from rocketmatter_mcp.client import LCSClient


def main():
    print("Verifying Rocketmatter MCP credentials...")
    try:
        client = LCSClient()
        # A lightweight authenticated call confirms the user token is valid.
        matters = client.list_matters(page=1, page_size=1)
        print("✓ Authenticated — Rocketmatter API reachable")
        print()
        print(json.dumps(matters, indent=2))
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
