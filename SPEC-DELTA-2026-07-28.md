# MCP protocol migration notes

The server targets MCP `2026-07-28` with Python SDK requirement `mcp>=2.2,<3`.
`uv.lock` resolves `mcp` and its `mcp-types` companion to `2.2.0`. The
application constructs `MCPServer` and runs it over stdio. SDK compatibility
also permits legacy `2025-11-25` negotiation.

| Protocol area | Mapping in this server |
| --- | --- |
| Lifecycle | Modern requests carry protocol and client metadata per request; `server/discover` advertises identity and primitive capabilities. Application state is downstream Rocket Matter OAuth material, with no MCP session state. |
| Results | Discovery, list, read, and tool results expose `resultType`; SDK cache hints use `ttlMs: 0` and `cacheScope: private`. Tool schemas and registration order remain stable. |
| HTTP routing | The production entry point is stdio. In-process Streamable HTTP checks cover `Mcp-Method`, named-operation `Mcp-Name`, and protocol version headers without exposing a production HTTP endpoint. |
| Errors | Checks cover header mismatch `-32020`, unsupported version `-32022`, unknown method `-32601`, and unknown resource `-32602`. Malformed `fields_json` is an explicit safe `ToolError`. |
| Capabilities | The server adds no custom extension, event store, publisher, sampling, elicitation, MCP logging notification, or MCP client authorization flow. Downstream Rocket Matter OAuth is separate. |

The [protocol changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
and [Python SDK migration guide](https://py.sdk.modelcontextprotocol.io/migration/)
describe the underlying protocol and SDK surfaces. See
[SPEC-MIGRATION-REPORT.md](SPEC-MIGRATION-REPORT.md) for reproducible checks and
testing scope.
