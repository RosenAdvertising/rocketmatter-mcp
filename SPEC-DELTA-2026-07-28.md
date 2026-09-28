# MCP specification delta: 2025-11-25 to 2026-07-28

Research date: 2026-08-09. Sources are limited to the official MCP
specification and official MCP Python SDK documentation.

## Current target and migration release

This repository currently targets MCP `2025-11-25`:

- `pyproject.toml` declares `mcp>=1.28.1,<2`, and `uv.lock` resolves MCP Python
  SDK 1.28.1.
- `rocketmatter_mcp/server.py` constructs the v1 `FastMCP` class and relies on
  its default protocol negotiation. The only configured entry point calls
  `mcp.run()` with the default stdio transport.
- There are no tracked tests or MCP protocol-version guards on the default
  branch.

The [official changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
says `2026-07-28` follows `2025-11-25`. The implementation release is MCP
Python SDK `2.0.0`; its
[official release notes](https://github.com/modelcontextprotocol/python-sdk/releases/tag/v2.0.0)
say it supports `2026-07-28` and every earlier revision from the same server.
The SDK's
[v1-to-v2 migration guide](https://py.sdk.modelcontextprotocol.io/migration/)
is the source for the Python API changes below.

Verdicts mean:

- **AFFECTS-US**: this server exposes or relies on the changed surface. The SDK
  may implement the wire behavior, but this migration must pin, configure, or
  test it.
- **NOT-APPLICABLE**: the feature or protocol direction is absent here. It is
  not added only because the new revision permits it.

## Protocol negotiation and lifecycle

| Normative change                                                                                                                             | Verdict            | Repository-specific reason                                                                                                                                           |
| -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Protocol-level sessions and `Mcp-Session-Id` are removed for modern requests.                                                                | **AFFECTS-US**     | The stdio server must accept independent modern requests. Its only application state is Rocket Matter OAuth material loaded per client; it has no MCP-session state. |
| Modern requests remove `initialize` and carry the version/capabilities in `_meta`; version mismatches use `UnsupportedProtocolVersionError`. | **AFFECTS-US**     | SDK v2's dual-era dispatcher must serve modern requests while retaining legacy negotiation.                                                                          |
| Servers implement `server/discover` with versions, capabilities, and identity.                                                               | **AFFECTS-US**     | This is required for every modern server and must reflect this server's tools, resources, and prompts.                                                               |
| Every result carries `resultType` (`complete` or `input_required`).                                                                          | **AFFECTS-US**     | Tool, resource, prompt, discovery, and list results are all exposed.                                                                                                 |
| Server-initiated requests are replaced by Multi Round-Trip Requests.                                                                         | **NOT-APPLICABLE** | No tool, resource, or prompt uses sampling, roots, elicitation, or another server-to-client request.                                                                 |
| `ping`, `logging/setLevel`, and `notifications/roots/list_changed` are removed; protocol logs require per-request opt-in.                    | **NOT-APPLICABLE** | None is implemented and the repository emits no MCP logging notifications.                                                                                           |

## Transports and notifications

| Normative change                                                                                                                                         | Verdict            | Repository-specific reason                                                                                                                                                                                          |
| -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Streamable HTTP POST requests require `Mcp-Method` and, for named operations, `Mcp-Name`; `x-mcp-header` can map selected tool inputs to custom headers. | **AFFECTS-US**     | The CLI stays stdio-only, but `MCPServer` exposes the SDK Streamable HTTP app/run surface. Raw-wire tests cover the required routing behavior without enabling or deploying HTTP. No tool opts into `x-mcp-header`. |
| HTTP GET and resource subscribe/unsubscribe are replaced by `subscriptions/listen`.                                                                      | **AFFECTS-US**     | The SDK-managed high-level server advertises list-change/resource-subscription capability. That dual-era behavior is preserved without adding an event store, publisher, or custom subscription bus.                |
| SSE resumability and redelivery are removed.                                                                                                             | **NOT-APPLICABLE** | The server has no event store and exposes no configured HTTP transport.                                                                                                                                             |
| Legacy HTTP+SSE is deprecated.                                                                                                                           | **NOT-APPLICABLE** | The entry point exposes stdio only.                                                                                                                                                                                 |

## Capabilities and extensions

| Normative change                                                               | Verdict            | Repository-specific reason                                                                               |
| ------------------------------------------------------------------------------ | ------------------ | -------------------------------------------------------------------------------------------------------- |
| Client/server capabilities gain an `extensions` field.                         | **AFFECTS-US**     | Discovery exposes the capability shape; the migration must prove no unused extension is advertised.      |
| Experimental core tasks move to `io.modelcontextprotocol/tasks`.               | **NOT-APPLICABLE** | There are no MCP task handlers or task-augmented tools, and SDK v2.0.0 does not implement the extension. |
| Roots, Sampling, and Logging are deprecated.                                   | **NOT-APPLICABLE** | None is declared or used.                                                                                |
| Sampling `includeContext` values `thisServer` and `allServers` are deprecated. | **NOT-APPLICABLE** | Sampling is not used.                                                                                    |

## Tools, resources, prompts, and cache semantics

| Normative change                                                                                            | Verdict            | Repository-specific reason                                                                                                                            |
| ----------------------------------------------------------------------------------------------------------- | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tool, prompt, resource, resource-template list results and resource reads require `ttlMs` and `cacheScope`. | **AFFECTS-US**     | The server exposes all three primitives. SDK v2's conservative `ttlMs: 0`, `cacheScope: private` defaults preserve the existing no-cache posture.     |
| `tools/list` should be deterministic.                                                                       | **AFFECTS-US**     | The server registers 86 tools in source order; repeated discovery must retain that order.                                                             |
| Tool schemas accept JSON Schema 2020-12 and structured content may be any JSON value.                       | **AFFECTS-US**     | Decorators generate every tool schema. Existing string results need no widening, but schema generation and error results require regression coverage. |
| Resource-not-found changes from `-32002` to Invalid Params `-32602`.                                        | **AFFECTS-US**     | Three static resources are registered; an unknown URI must use the new code.                                                                          |
| URL elicitation completion fields are removed.                                                              | **NOT-APPLICABLE** | The server performs no elicitation.                                                                                                                   |
| Generated schema numeric limits/defaults use numbers rather than only integers.                             | **NOT-APPLICABLE** | The repository neither vendors nor directly validates against the generated MCP meta-schema. SDK v2 absorbs the correction.                           |

## Authorization and security

| Normative change                                                                    | Verdict            | Repository-specific reason                                                                                                                                                 |
| ----------------------------------------------------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Authorization responses should include RFC 9207 `iss`, and MCP clients validate it. | **NOT-APPLICABLE** | This is not an MCP authorization server or MCP OAuth client. Its separate downstream Rocket Matter OAuth flow is application behavior outside MCP transport authorization. |
| Dynamic Client Registration sends `application_type`.                               | **NOT-APPLICABLE** | The server does not dynamically register an MCP client.                                                                                                                    |
| Persisted MCP client credentials are keyed to authorization-server issuer.          | **NOT-APPLICABLE** | The repository stores downstream Rocket Matter tokens, not MCP client registrations.                                                                                       |
| Dynamic Client Registration is deprecated in favor of Client ID Metadata Documents. | **NOT-APPLICABLE** | Neither MCP DCR nor MCP client registration is implemented.                                                                                                                |

## Errors, metadata, and observability

| Normative change                                                                                                                                                   | Verdict            | Repository-specific reason                                                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MCP reserves `-32020..-32099`; header mismatch, missing capability, and unsupported version become `-32020`, `-32021`, and `-32022`; unknown methods use `-32601`. | **AFFECTS-US**     | SDK v2 must produce the modern codes. Tests cover the reachable routing, version, unknown-method, and invalid-resource cases without inventing an optional capability. |
| `_meta` carries W3C `traceparent`, `tracestate`, and `baggage`.                                                                                                    | **NOT-APPLICABLE** | The server has no custom MCP `_meta` tracing integration. SDK-provided propagation requires no application change.                                                     |

The changelog's governance and SEP workflow changes impose no wire/runtime
requirement and are therefore omitted. The migration does not adopt deprecated
Roots, Sampling, Logging, HTTP+SSE, or DCR.

## SDK v2 surface mapping

- Replace `mcp.server.fastmcp.FastMCP` with
  `mcp.server.mcpserver.MCPServer`; decorators remain unchanged.
- Keep `mcp.run()` as stdio. There are no constructor transport arguments to
  move; raw-wire tests pass Streamable HTTP options to
  `streamable_http_app()` as required by v2.
- Pin `mcp==2.0.0`; let the lock resolve the exact matching
  `mcp-types==2.0.0` split and v2 dependency floors.
- No direct MCP model construction, client helper, auth middleware, custom
  `call_tool()` override, or transport exception type needs porting in the
  application code.
