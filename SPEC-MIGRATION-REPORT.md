# MCP 2026-07-28 migration report

## Result

`rocketmatter-mcp` now targets MCP `2026-07-28`, up from `2025-11-25`.
The direct Python SDK dependency changed from `mcp>=1.28.1,<2` (locked to
1.28.1) to the exact migration release `mcp==2.0.0`. The refreshed lock
includes the SDK v2 dependency split, including `mcp-types==2.0.0`.

The authoritative per-change analysis and official-source links are in
[`SPEC-DELTA-2026-07-28.md`](SPEC-DELTA-2026-07-28.md). No deployment, live
firm, live account, external browser flow, push, or GitHub write was performed.

## Implementation

- Replaced the v1 `FastMCP` construction with SDK v2 `MCPServer` while
  preserving all 86 tools, three resources, three prompts, and their
  registration order.
- Kept the production transport as stdio via `mcp.run()`. The repository had no
  constructor transport options to move; Streamable HTTP is constructed only
  inside offline raw-wire tests.
- Preserved the existing downstream Rocket Matter scoped-OAuth flow, token
  storage, per-tool client construction, and no-MCP-session state model.
- Kept SDK v2's dual-era compatibility: modern clients negotiate
  `2026-07-28`, while legacy mode negotiates `2025-11-25`.
- Preserved the conservative cache posture exposed by SDK v2 (`ttlMs: 0`,
  `cacheScope: private`) and added no custom cache, event store, publisher,
  extension, or server-to-client request feature.
- Added a development dependency group for the offline protocol suite and an
  explicit core Ruff policy targeting the declared Python 3.10 floor.

## Spec conformance

The offline suite proves:

- sessionless `server/discover` with exact version, identity, primitive
  capabilities, private zero-TTL cache hints, and no unused extension;
- required per-request protocol metadata and the `MCP-Protocol-Version`,
  `Mcp-Method`, and named-operation `Mcp-Name` HTTP headers;
- `resultType: complete` and cache hints on discovery, tool/prompt/resource
  lists, resource-template lists, and resource reads;
- deterministic discovery of all 86 object-schema tools;
- modern and legacy client negotiation from one `MCPServer`;
- unknown-resource Invalid Params `-32602`, header mismatch `-32020`,
  unsupported protocol `-32022`, and unknown method `-32601`;
- schema validation rejects an oversized list page before client construction;
- tool failures remain MCP error results and omit rejected input content.

## Canary sibling checks

### A. List-tool limit and order — fixed / method-verified-only

All 15 paginated registered list tools now expose a schema-enforced one-based
`page` and `page_size` in the inclusive range 1–200. The API client validates
the same bounds for direct callers, makes exactly one vendor request, and
defensively caps either envelope `items` or a bare list to the requested page
size if the upstream endpoint over-returns.

No sort/order parameter was added. The current LCS `/v1` implementation and its
earlier repository version send only `page`/`pageSize` plus the small set of
live-verified filters. The only descending-sort evidence in repository history
belongs to the different legacy `/api/v2` API. With vendor browsing outside the
task's network grant and no live-account testing authorized, inventing an LCS
parameter would risk silent rejection. Ordering is therefore honestly flagged
as method-verified-only rather than claimed clean.

### B. Silent rejections — fixed

Explicit input, credential-prerequisite, upstream-status, response-integrity,
not-found/update/delete, unsupported-capability, pagination, and transaction
scope rejection paths now emit stable PII-free reason logs. Logs contain only
fixed reasons, HTTP status numbers, and internal resource/capability names—not
request bodies, record identifiers, credential values, names, emails, or
subjects.

### C. Origin/CSP ceremony — N/A

The repository serves no browser pages or custom web routes. Its setup command
prints a vendor authorization URL for manual copy/paste, and the MCP entry point
uses stdio. Sec-Fetch-Site and CSP handoff patterns do not apply.

### D. PII in logs — fixed

Raw token responses and vendor response bodies no longer enter raised error
messages. Setup no longer prints the token-derived user name, verification no
longer dumps user records, and both CLIs avoid printing arbitrary exception
messages. Tests inject name/email/token-like sentinels and assert they do not
appear in logs, MCP error content, or CLI success output.

## Test inventory

Default-branch baseline:

- No tracked test files or protocol guard: **0/0 tests**.
- The checked-in lock targeted MCP 1.28.1; the pre-existing local `.venv` was
  stale at 1.27.2. Both report protocol `2025-11-25`.

Post-migration verification from a fresh environment installed from `uv.lock`:

- `uv sync --locked`: passed; MCP 2.0.0 and mcp-types 2.0.0 installed.
- `uv run --locked pytest -q tests/test_spec_2026_07_28.py`: **16 passed**.
- `uv run --locked pytest -q`: **16 passed** (all tracked tests).
- `tests/spec_check.py --mcp-only`: PASS, `2026-07-28`.
- `uvx ruff check .`: all checks passed.
- `uvx ruff format --check .`: all files formatted.

The tests are entirely offline. No Rocket Matter credentials were required or
read by the suite, and no live API method was exercised.

## Git sandbox handoff

The runtime permits worktree edits but denies writes to this repository's
`.git` directory. Creating `spec-2026-07-28` there failed with `Operation not
permitted`, so commits were created on that branch in a writable alternate Git
database under the authorized fan-out scratchpad. The final fan-out report
records the complete `git log --oneline` and the verified portable bundle path.
The bundle must be imported into the repository's real Git database; it must
not be treated as already installed there.

The branch uses four ordered conventional commits:

1. `docs: document MCP 2026-07-28 delta`
2. `feat: migrate server to MCP 2026-07-28`
3. `test: prove MCP 2026-07-28 conformance`
4. `docs: report MCP 2026-07-28 migration`

Every commit carries:
`Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
