# MCP 2026-07-28 migration

This server targets MCP protocol revision `2026-07-28`. The Python package
requires `mcp>=2.2,<3`; `uv.lock` resolves both `mcp` and `mcp-types` to
`2.2.0`. The server uses `MCPServer` and keeps its production transport on
stdio. The SDK also supports legacy `2025-11-25` negotiation.

The protocol changes and their application to this server are summarized in
[SPEC-DELTA-2026-07-28.md](SPEC-DELTA-2026-07-28.md).

## Server behavior

- The registered tools, resources, and prompts retain their existing order.
  Modern discovery exposes their schemas and capabilities. The server adds no
  application cache, event store, or MCP authorization flow.
- The SDK supplies sessionless modern requests, `server/discover`, per-request
  protocol metadata, `resultType`, and conservative private cache hints with
  `ttlMs: 0`.
- In-process HTTP tests exercise routing headers, version negotiation, error
  codes, resource reads, and tool failures. No HTTP transport is configured for
  the production entry point.
- Paginated list tools enforce one-based page numbers and page sizes of 1–200.
  The client requests one vendor page and caps overlong results. It does not
  request a vendor sort order; ordering is only verified at the method level.
- Rejection logs use fixed reasons and omit submitted fields and vendor bodies.
  Malformed or non-object `fields_json` raises `ToolError` with fixed, safe
  messages, which the SDK exposes as tool errors.

## Reproduce the local checks

With development dependencies installed from the lockfile, run the following
from the repository root. Set fake configuration and disable keyring access so
the suite does not read local credential stores or call a vendor:

```bash
ROCKETMATTER_MCP_USE_KEYRING=0 ROCKETMATTER_API_KEY=unused \
ROCKETMATTER_CLIENT_ID=unused ROCKETMATTER_CLIENT_SECRET=unused \
ROCKETMATTER_BASE_URL=https://example.invalid \
ROCKETMATTER_API_BASE_URL=https://example.invalid \
ROCKETMATTER_REDIRECT_URI=https://example.invalid/callback \
./.venv/bin/pytest -q
./.venv/bin/python tests/spec_check.py --mcp-only
uv tool run --offline ruff check rocketmatter_mcp/client.py rocketmatter_mcp/server.py rocketmatter_mcp/setup/oauth_flow.py rocketmatter_mcp/setup/verify.py tests/spec_check.py tests/test_spec_2026_07_28.py
uv lock --check --offline
```

The tests use mocked vendor behavior and in-process protocol transports; they
do not establish live vendor or deployed transport behavior.

## Open product decision

MCP 2.2.0 masks exception messages other than `ToolError` and `ResourceError`
from tool clients. Retaining that masking limits information leakage; explicitly
safe `ToolError` messages can give clients more actionable feedback. Toby should
decide whether any other error paths warrant safe client-facing messages.
Existing exception handling is unchanged by this documentation cleanup.
