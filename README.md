<p align="center"><a href="https://rosenadvertising.com/datalink/?utm_source=github&utm_medium=readme-banner&utm_campaign=rocketmatter-mcp"><img src="https://image.rosenadvertising.com/datalink/readme-banner-v2.png" alt="DataLink by Rosen Advertising: don't want to install and run this yourself? Get it hosted." width="100%"></a></p>

# Rocket Matter MCP server

[![CI](https://github.com/RosenAdvertising/rocketmatter-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/RosenAdvertising/rocketmatter-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP 2026-07-28](https://img.shields.io/badge/MCP-2026--07--28-7C3AED.svg)](https://modelcontextprotocol.io)
[![PyPI version](https://img.shields.io/pypi/v/rocketmatter-mcp.svg)](https://pypi.org/project/rocketmatter-mcp/)

Connect Claude and other MCP clients to Rocket Matter to manage matters, clients, time entries, invoices and payments.

Rocket Matter MCP server is a [Model Context Protocol](https://modelcontextprotocol.io) server for [Rocket Matter](https://rocketmatter.com), the legal practice management platform. It registers 86 tools that read and write Rocket Matter data through the ProfitSolv LCS `/v1` Integration API; 43 of them cover capabilities that API does not expose and return an error saying so (see [Tools](#tools)). It runs over stdio by default, for desktop clients such as Claude Desktop, and offers an opt-in stateless Streamable HTTP mode that implements MCP specification 2026-07-28. Rocket Matter credentials stay on the machine that runs the server: they come from the setup command and your operating system's keyring, never from the client. The server signs in with scoped OAuth rather than a password, so it never trips Rocket Matter's single-session-per-user limit and does not log you out of your Rocket Matter browser session while it runs.

## Features

- **Matters**: list, get, create, update and delete matters.
- **Clients and contacts**: create, read, update and delete clients and contacts.
- **Time entries and expenses**: log, edit and delete billable time and costs.
- **Invoices**: list, get, create, update and delete invoices.
- **Payments**: list payments and record new ones.
- **Transactions**: list by matter or bank, get, create, update and delete.
- **Documents**: list documents (read-only).
- **Users**: list and get firm users.
- **UTBMS codes**: get the codes for a matter.

## Tools

The server registers 86 tools. 43 of them work against the LCS `/v1` Integration API. The other 43 cover capabilities that API does not expose; they stay registered and return the error "This capability is not available in the Rocket Matter LCS /v1 API." instead of an empty result (see [Limits of the LCS /v1 API](#limits-of-the-lcs-v1-api)).

<details>
<summary>All 86 tools</summary>

Working tools (43):

- `create_client`
- `create_contact`
- `create_expense`
- `create_invoice`
- `create_matter`
- `create_payment`
- `create_time_entry`
- `create_transaction`
- `delete_client`
- `delete_contact`
- `delete_expense`
- `delete_invoice`
- `delete_matter`
- `delete_time_entry`
- `delete_transaction`
- `get_client`
- `get_codes`
- `get_contact`
- `get_expense`
- `get_invoice`
- `get_matter`
- `get_text_shortcut`
- `get_time_entry`
- `get_transaction`
- `get_user`
- `list_clients`
- `list_contacts`
- `list_documents`
- `list_expenses`
- `list_invoices`
- `list_matters`
- `list_payments`
- `list_text_shortcuts`
- `list_time_entries`
- `list_transactions`
- `list_users`
- `update_client`
- `update_contact`
- `update_expense`
- `update_invoice`
- `update_matter`
- `update_time_entry`
- `update_transaction`

Registered but not available in the `/v1` API (43):

- `approve_invoice`
- `create_ap_bill`
- `create_ap_payment`
- `create_ap_vendor`
- `delete_ap_bill`
- `delete_document`
- `generate_invoice`
- `get_activity_codes`
- `get_ap_bill`
- `get_ap_payment_status`
- `get_ap_vendor`
- `get_client_labels`
- `get_client_suggestions`
- `get_document_default_app`
- `get_document_download_url`
- `get_document_upload_url`
- `get_ebilling_defaults`
- `get_expense_lookups`
- `get_firm_summary`
- `get_hard_cost_expense_lookups`
- `get_invoice_allocations`
- `get_invoice_lookups`
- `get_invoice_payment_lookups`
- `get_matter_labels`
- `get_matter_type_workflow`
- `get_new_contact_defaults`
- `get_new_expense_lookups`
- `get_new_invoice_lookups`
- `get_new_matter_defaults`
- `get_new_matter_definition`
- `get_task_codes`
- `get_time_entry_lookups`
- `get_time_grid_lookups`
- `get_transaction_lookups`
- `list_ap_bills`
- `list_ap_payments`
- `list_ap_vendors`
- `list_banks`
- `list_billable_items`
- `list_chart_of_accounts`
- `list_timekeepers`
- `update_ap_bill`
- `update_ap_vendor`

</details>

### Prompts and resources

The server also registers three prompts and three resources.

| Prompt | What it does |
| --- | --- |
| `accounts_receivable_review` | Reviews outstanding invoices and recent payments for the firm's receivables. |
| `matter_billing_review` | Reviews unbilled time and outstanding invoices for one matter. Takes `matter_id`. |
| `new_matter_intake` | Walks through creating a new matter for an existing client. Takes `client_id`. |

| Resource | What it provides |
| --- | --- |
| `rocketmatter://clients` | The firm's clients (first page): names, balances and contact details. |
| `rocketmatter://users` | All firm users and timekeepers with email, roles, default rate and status. |
| `rocketmatter://security-notes` | Security notes for the server. |

## Requirements

- Python 3.10 or later.
- A Rocket Matter account and a registered OAuth integration for the ProfitSolv LCS Integration API: an API key, an OAuth client ID and a client secret.
- An MCP client such as Claude Desktop.

## Installation

Install [uv](https://docs.astral.sh/uv/), then clone the repository and install its locked dependencies:

```bash
git clone https://github.com/RosenAdvertising/rocketmatter-mcp.git
cd rocketmatter-mcp
uv sync --locked
```

Releases are also published to PyPI: `pip install rocketmatter-mcp` installs version 0.5.0, which predates the HTTP mode described below. Install from source to use HTTP mode.

## Configuration

Before setup, the firm must register `http://127.0.0.1:8771/callback` as an OAuth redirect with Rocket Matter / ProfitSolv. To use another port, set `ROCKETMATTER_REDIRECT_URI` to the exact registered HTTP loopback URI (`127.0.0.1`, explicit port and callback path). `localhost`, IPv6 and external callbacks are rejected. Then run the setup command:

```bash
uv run rocketmatter-mcp-setup
```

The wizard:

1. Stores the integration's API key, OAuth client ID and client secret in your operating system's keyring (with a private file fallback).
2. Binds the configured local callback before printing the authorization URL. Open that URL in your browser and click Allow.
3. Receives the callback locally and checks the session's random `state` before exchanging the code. It stops if the port is occupied or consent times out.
4. Atomically caches access and refresh tokens in `~/.rocketmatter-mcp/tokens.json`, created with mode `0600` before any secret bytes are written.

Authorization codes are never accepted in command-line arguments or environment variables. The callback handles them automatically.

After that, the server refreshes its own access token with the long-lived refresh token, with no browser and no password, so you are not prompted again unless the refresh token is revoked.

Check the connection:

```bash
uv run rocketmatter-mcp-verify
```

Server messages that say to run `rocketmatter-mcp-setup` mean `uv run rocketmatter-mcp-setup` from your clone.

The server reads these variables, which you can also set in its environment:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `ROCKETMATTER_API_KEY` | Yes (saved by setup) | Credential store | Integration API key, sent as the `X-Api-Key` header. |
| `ROCKETMATTER_CLIENT_ID` | Yes (saved by setup) | Credential store | OAuth client ID, used for the code exchange and token refresh. |
| `ROCKETMATTER_CLIENT_SECRET` | Yes (saved by setup) | Credential store | OAuth client secret, used for the code exchange and token refresh. |
| `ROCKETMATTER_BASE_URL` | No | `https://app.rocketmatter.net` | OAuth host. Only this host is accepted. |
| `ROCKETMATTER_API_BASE_URL` | No | The approved ProfitSolv LCS data host | The LCS `/v1` data host. See [Endpoint configuration](#endpoint-configuration). |
| `ROCKETMATTER_REDIRECT_URI` | No | `http://127.0.0.1:8771/callback` | OAuth redirect URI used by setup; must match the redirect registered with the vendor. |
| `ROCKETMATTER_MCP_USE_KEYRING` | No | `1` | Set to `0` to skip the operating system keyring and use the environment and the `.env` file fallback. |

## Usage with Claude Desktop

Add the server to Claude Desktop's configuration file (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS, `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "rocketmatter": {
      "command": "uv",
      "args": ["run", "--locked", "--directory", "/absolute/path/to/rocketmatter-mcp", "rocketmatter-mcp"]
    }
  }
}
```

Replace `/absolute/path/to/rocketmatter-mcp` with the path of your clone, then restart Claude Desktop. Any other stdio MCP client uses the same command and arguments.

## HTTP mode

Stdio is the default. Set `ROCKETMATTER_MCP_TRANSPORT=streamable-http` to serve the stateless Streamable HTTP transport from MCP specification 2026-07-28 at `/mcp`. Each request stands alone: no initialization handshake and no `Mcp-Session-Id`. Clients on earlier protocol versions are served on the same endpoint.

> **Security: this endpoint has no authentication and no TLS.** Anyone who can reach the port can run every tool, including write and delete tools, with this server's vendor credentials. Keep the default loopback bind (`127.0.0.1`), or put the server behind an authenticating TLS proxy on a private network. `ROCKETMATTER_MCP_ALLOWED_HOSTS` and `ROCKETMATTER_MCP_ALLOWED_ORIGINS` protect against browser DNS rebinding, not against direct callers. A proxy in front of it needs connection and idle timeouts: a legacy-style `GET /mcp` with `Accept: text/event-stream` holds a stream open until the client disconnects.

| Variable | Default | Purpose |
| --- | --- | --- |
| `ROCKETMATTER_MCP_TRANSPORT` | `stdio` | `stdio` or `streamable-http`. |
| `ROCKETMATTER_MCP_HOST` | `127.0.0.1` | Bind address. `127.0.0.1`, `localhost` and `::1` use the SDK's built-in Host and Origin checks; any other value requires `ROCKETMATTER_MCP_ALLOWED_HOSTS`. |
| `PORT` | `8080` | Port; must be an integer. |
| `ROCKETMATTER_MCP_ALLOWED_HOSTS` | unset | Comma-separated `Host` header values accepted on a non-loopback bind, such as `mcp.example.com:8080` or `mcp.example.com:*`. |
| `ROCKETMATTER_MCP_ALLOWED_ORIGINS` | unset | Comma-separated `Origin` values accepted on a non-loopback bind, such as `https://client.example.com`. Requests without an `Origin` header are accepted. |

Rocket Matter credentials come from the same configuration as stdio (see [Configuration](#configuration)), never from the request.

```bash
ROCKETMATTER_MCP_TRANSPORT=streamable-http PORT=8080 uv run --locked rocketmatter-mcp
```

Point the MCP client at `http://127.0.0.1:8080/mcp`. Responses use the SDK's default streaming mode, so a client that disconnects cancels its request.

## Error handling

A failed tool call returns an MCP error result (`isError`) with a fixed message. The server never passes a Rocket Matter response body, a request URL or a credential back to the client.

| Situation | What the tool returns |
| --- | --- |
| Setup missing or incomplete | "Missing ROCKETMATTER_API_KEY. Run rocketmatter-mcp-setup, then restart the MCP server." (naming whichever of `ROCKETMATTER_API_KEY`, `ROCKETMATTER_CLIENT_ID` and `ROCKETMATTER_CLIENT_SECRET` is missing). |
| HTTP 401 (after one automatic token refresh) | "Rocket Matter authorization was rejected or expired. Re-authorize with rocketmatter-mcp-setup." |
| HTTP 403 | "HTTP 403: Rocket Matter access denied: the connected account lacks permission for this action (or the authorization expired; re-run rocketmatter-mcp-setup if so)." |
| HTTP 404 | "The requested Rocket Matter record was not found." |
| HTTP 429 | "HTTP 429: Rate limit reached. Retry after N seconds." where N comes from the `Retry-After` header, or "HTTP 429: Rate limit reached. Wait briefly, then retry." when the header is missing or unusable. |
| Other HTTP error statuses | "HTTP" and the status followed by a fixed sentence, such as "HTTP 400: The request did not pass vendor validation." or "HTTP 409: The request conflicts with the current record state." |
| Timeout or connection failure on a read | "The Rocket Matter read could not complete because of a timeout or connection failure. You may retry." |
| Timeout or connection failure on a write | "The operation outcome is unknown because the connection failed. Check whether it completed before retrying." |
| A tool the `/v1` API does not support | "This capability is not available in the Rocket Matter LCS /v1 API." |
| Invalid arguments | A message such as "Invalid arguments: page must be a whole number of at least 1." or "Invalid fields_json: malformed JSON". |
| Anything else | "Error executing tool list_matters" (the tool name) with no detail. |

Every Rocket Matter request has a 30-second timeout. The server does not retry failed requests and does not follow redirects. On HTTP 401 it refreshes the OAuth access token once and repeats the request.

At startup the server exits with a message on stderr and a non-zero status when `ROCKETMATTER_MCP_TRANSPORT` is neither `stdio` nor `streamable-http`, when `PORT` is not an integer, or when a non-loopback `ROCKETMATTER_MCP_HOST` is set without `ROCKETMATTER_MCP_ALLOWED_HOSTS`.

## Limits of the LCS /v1 API

The ProfitSolv LCS `/v1` Integration API is narrower than Rocket Matter's own application. The 43 tools listed as unavailable under [Tools](#tools) cover firm financial summaries, timekeeper billable-time summaries, bank and chart-of-accounts listings, the two-step invoice generation flow, invoice allocations, document upload, download and delete actions, accounts payable, lookup and default-value endpoints, and the separate task and activity code lists (only the combined `get_codes` is available). Rocket Matter features the API does not expose at all, such as tasks, timers, calendar, tags, trust, rates, firm roles, tax and discount settings, phone messages, internal chat, workflow, reports, recurring billing, matter templates and court rules, have no tools.

Transaction listing needs a matter or bank scope, and the code lookup needs a matter ID.

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

**Read order.** A credential already set in the process environment wins. Otherwise the server reads the OS keyring, then the `.env` file fallback.

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

Hosts are overridable via `ROCKETMATTER_BASE_URL` (the OAuth host; only `https://app.rocketmatter.net` is accepted) and `ROCKETMATTER_API_BASE_URL` (the LCS `/v1` data host; only the two approved ProfitSolv LCS hosts are accepted, see [Endpoint configuration](#endpoint-configuration)).

## Example usage in Claude

> "List my matters"
>
> "Create a client named Acme Holdings"
>
> "Log a time entry on matter `<id>`"
>
> "Show open invoices and recent payments"
>
> "List the firm's users"

## Endpoint configuration

OAuth accepts only `https://app.rocketmatter.net`. The data endpoint accepts only
the two exact ProfitSolv LCS production/sandbox hosts listed in
`rocketmatter_mcp/endpoint_validation.py`; arbitrary Azure tenants are rejected.
Both endpoint settings reject userinfo, paths, query strings, fragments and ports
other than 443. A new vendor endpoint requires an allowlist update after verification.
The [public LCS sandbox Swagger document](https://lcs-developer-api-profi-sandbox-gncndgfccdgxdtff.centralus-01.azurewebsites.net/swagger/v1/swagger.json)
identifies the ProfitSolv LCS gateway. The [legacy Rocket Matter reference](https://developer.rocketmatter.com/)
describes a different API; it does not establish additional LCS hosts.

## Testing

The test suite runs offline and needs no Rocket Matter account: every Rocket Matter API call is replaced by an in-process test double. It covers path-identifier validation, error handling, OAuth callback and redirect validation, credential file handling, the setup and verify commands, the stdio server, and the Streamable HTTP transport including the 2026-07-28 wire format, Host and Origin checks and stateless requests.

```bash
uv sync --locked
uv run --locked pytest -q
```

CI runs the suite on every push and pull request to `main`.

## License

MIT. See [LICENSE](LICENSE).
