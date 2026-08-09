#!/usr/bin/env python3
"""Offline guard for the MCP protocol revision used by this repository."""

from __future__ import annotations

import argparse

from mcp.types import LATEST_PROTOCOL_VERSION


EXPECTED_MCP_PROTOCOL_VERSION = "2026-07-28"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mcp-only",
        action="store_true",
        help="Check only the installed MCP protocol revision.",
    )
    parser.parse_args()

    if LATEST_PROTOCOL_VERSION != EXPECTED_MCP_PROTOCOL_VERSION:
        print("Spec check: FAIL")
        print(
            "Installed MCP SDK targets the wrong revision: "
            f"expected {EXPECTED_MCP_PROTOCOL_VERSION}, "
            f"got {LATEST_PROTOCOL_VERSION}"
        )
        return 1

    print("Spec check: PASS")
    print(f"MCP protocol: {LATEST_PROTOCOL_VERSION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
