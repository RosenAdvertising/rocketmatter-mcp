# rocketmatter-mcp

[![PyPI version](https://img.shields.io/pypi/v/rocketmatter-mcp.svg)](https://pypi.org/project/rocketmatter-mcp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

MCP server for [Rocketmatter](https://rocketmatter.com) — legal practice management
from Claude Desktop in natural language, over the official **ProfitSolv LCS `/v1`
Integration API** with a **scoped OAuth** integration.

No password login: the server authorizes once in the browser, then refreshes its own
token forever. It never trips Rocket Matter's single-session-per-user limit, so it
won't log you out of your Rocket Matter browser session while it runs.

## What you can do

The LCS `/v1` Integration API covers the core practice-management entities:

- **Matters** — list, get, create, update, delete
- **Clients & Contacts** — full CRUD
- **Time entries & Expenses** — full CRUD (log and edit billable time and costs)
- **Invoices** — list, get, create, update, delete
- **Payments** — list and record
- **Transactions** — list (by matter or bank), get, create, update, delete
- **Documents** — list (read-only)
- **Users / timekeepers** — list, get
- **UTBMS codes** — per matter

### Not covered by the `/v1` API

The `/v1` Integration API is narrower than Rocket Matter's internal UI. These are
**not available** and their tools fail loudly (rather than returning nothing): firm
financial summary, timekeeper time summaries, bank/chart-of-accounts enumeration,
the two-step invoice-generation flow, accounts payable, lookup/defaults endpoints,
and tasks, timers, calendar, tags, trust, rates, firm roles, tax/discount, phone
messages, internal chat, workflow, reports, recurring billing, matter templates, and
court rules.

## Requirements

- Python 3.10+
- Python MCP SDK >=2.3,<3 (protocol revision 2026-07-28)
- Claude Desktop (or any MCP-compatible client)
- A Rocket Matter account **and** a registered OAuth integration (API key + OAuth
  client ID/secret) for the ProfitSolv LCS Integration API

## Installation

```bash
pip install rocketmatter-mcp
```

## Setup

```bash
rocketmatter-mcp-setup
```

Before setup, the firm must register **`http://127.0.0.1:8771/callback`** as an
OAuth redirect with Rocket Matter / ProfitSolv. To use another port, set
`ROCKETMATTER_REDIRECT_URI` to the exact registered HTTP loopback URI (`127.0.0.1`,
explicit port and callback path). `localhost`, IPv6 and external callbacks are rejected.

The wizard:

1. Stores the integration's API key, OAuth client ID, and client secret in the OS
   keyring (with a private file fallback).
2. Binds the configured local callback before printing the authorization URL.
   Open that URL in your browser and click **Allow**.
3. Receives the callback locally and checks the session's random `state` before
   exchanging the code. It stops if the port is occupied or consent times out.
4. Atomically caches access and refresh tokens in `~/.rocketmatter-mcp/tokens.json`,
   created with mode `0600` before writing any secret bytes.

Authorization codes are never accepted in command-line arguments or environment
variables. The callback handles them automatically.

After that, the client refreshes its own access token with the long-lived refresh
token — no browser, no password — so you won't be prompted again unless the refresh
token is revoked.

Verify:

```bash
rocketmatter-mcp-verify
```

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "rocketmatter": {
      "command": "rocketmatter-mcp"
    }
  }
}
```

## HTTP mode

Stdio is the default. Set `ROCKETMATTER_MCP_TRANSPORT=streamable-http` to serve
stateless Streamable HTTP at `/mcp`. The SDK supports both protocol 2026-07-28
single-request calls and earlier clients on this endpoint. SSE stays enabled so
disconnecting a client cancels its request.

> **Security: this endpoint has no authentication and no TLS.** Anyone who can reach the port can run every tool, including write and delete tools, with this server's vendor credentials. Keep the default loopback bind (`127.0.0.1`), or put the server behind an authenticating TLS proxy on a private network. `ROCKETMATTER_MCP_ALLOWED_HOSTS` and `ROCKETMATTER_MCP_ALLOWED_ORIGINS` protect against browser DNS rebinding, not against direct callers. A proxy in front of it needs connection and idle timeouts: a legacy-style `GET /mcp` with `Accept: text/event-stream` holds a stream open until the client disconnects.

| Environment variable | Default / purpose |
| --- | --- |
| `ROCKETMATTER_MCP_TRANSPORT` | `stdio`; choose `streamable-http` for HTTP. |
| `ROCKETMATTER_MCP_HOST` | `127.0.0.1`; address to bind. |
| `PORT` | `8080`; integer listening port. |
| `ROCKETMATTER_MCP_ALLOWED_HOSTS` | Comma-separated Host values, required outside `127.0.0.1`, `localhost`, and `::1`. Include the port, e.g. `mcp.example:8080`, or allow any port with `mcp.example:*`. |
| `ROCKETMATTER_MCP_ALLOWED_ORIGINS` | Optional comma-separated browser origins, e.g. `https://client.example`. Outside loopback, an omitted list rejects every supplied Origin; requests without Origin remain allowed. The SDK validates loopback Hosts and Origins automatically. |
| `ROCKETMATTER_API_KEY` | Existing integration API key (`X-Api-Key`). |
| `ROCKETMATTER_CLIENT_ID` | Existing OAuth client ID, used for token refresh. |
| `ROCKETMATTER_CLIENT_SECRET` | Existing OAuth client secret, used for token refresh. |
| `ROCKETMATTER_BASE_URL` | `https://app.rocketmatter.net`; approved OAuth host. |
| `ROCKETMATTER_API_BASE_URL` | Existing approved ProfitSolv LCS data host; see Endpoint configuration below. |
| `ROCKETMATTER_REDIRECT_URI` | `http://127.0.0.1:8771/callback`; existing setup callback. |
| `ROCKETMATTER_MCP_USE_KEYRING` | `1`; set `0` to disable OS keyring storage. |

HTTP uses the same credential resolution and cached OAuth tokens from
`rocketmatter-mcp-setup` as stdio. Vendor credentials come from the server's
environment or existing credential store, never from HTTP requests.

After the existing setup:

```bash
ROCKETMATTER_MCP_TRANSPORT=streamable-http \
ROCKETMATTER_MCP_HOST=127.0.0.1 PORT=8080 rocketmatter-mcp
```

The endpoint is `http://127.0.0.1:8080/mcp`.

## Credential storage

By default credentials are stored in your operating system's native secret store
via the cross-platform [`keyring`](https://github.com/jaraco/keyring) library:

| OS      | Backend                                  |
| ------- | ---------------------------------------- |
| macOS   | Keychain                                 |
| Windows | Credential Manager                       |
| Linux   | Secret Service (GNOME Keyring / KWallet) |

With a working keyring backend, secrets are saved under the service name
`rocketmatter-mcp` and are not written to the fallback file.

**File fallback.** On a host with no keyring backend (e.g. a headless Linux box
without Secret Service), or if you set `ROCKETMATTER_MCP_USE_KEYRING=0`, credentials
fall back to a `~/.rocketmatter-mcp/.env` file with `0600` permissions.

On Windows, the file is stored in the user's profile and protected by Windows'
default per-user access rules. On POSIX, files are created with `0600` permissions
and writes fail closed if private permissions cannot be established.

**Read order.** Credentials resolve in the order OS keyring → process environment
→ `.env` file.

## Authentication notes

The server uses the **ProfitSolv LCS `/v1` Integration API** with a scoped OAuth
integration:

- **Consent once** (`/OAuth/authorize` → `Allow`) to obtain an authorization code.
- **Exchange** the code at `{base}/api/ext/auth/token` (`grant_type=authorization_code`)
  for an `access_token` (~5h) + a long-lived `refresh_token`.
- **Data calls** go to the LCS `/v1` host with two headers: `X-Api-Key: <app key>`
  and `X-User-Token: <access token>`.
- **Refresh** (`grant_type=refresh_token`) renews the access token without a password
  login, so the user's Rocket Matter browser session is never bumped.

Hosts are overridable via `ROCKETMATTER_BASE_URL` (OAuth host — Rocket Matter
`app.rocketmatter.net`, CosmoLex `law.cosmolex.com`) and `ROCKETMATTER_API_BASE_URL`
(the LCS `/v1` data host).

## Example usage in Claude

> "List my matters"
>
> "Create a client named Acme Holdings"
>
> "Log a time entry on matter <id>"
>
> "Show open invoices and recent payments"
>
> "List the firm's users"

## License

MIT — see [LICENSE](LICENSE).

## Endpoint configuration

OAuth accepts only `https://app.rocketmatter.net`. The data endpoint accepts only
the two exact ProfitSolv LCS production/sandbox hosts listed in
`rocketmatter_mcp/endpoint_validation.py`; arbitrary Azure tenants are rejected.
Both endpoint settings reject userinfo, paths, query strings, fragments and ports
other than 443. A new vendor endpoint requires an allowlist update after verification.
The [public LCS sandbox Swagger document](https://lcs-developer-api-profi-sandbox-gncndgfccdgxdtff.centralus-01.azurewebsites.net/swagger/v1/swagger.json)
identifies the ProfitSolv LCS gateway. The [legacy Rocket Matter reference](https://developer.rocketmatter.com/)
describes a different API; it does not establish additional LCS hosts.
