#!/usr/bin/env python3
"""Verify Rocketmatter MCP credentials."""

import json
import sys
from rocketmatter_mcp.client import RocketMatterClient


def main():
    print("Verifying Rocketmatter MCP credentials...")
    try:
        client = RocketMatterClient()
        user = client.get_current_user()
        name = user.get("FullName", f"{user.get('FirstName', '')} {user.get('LastName', '')}".strip())
        print(f"✓ Authenticated as: {name}")
        print()
        print(json.dumps(user, indent=2))
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
