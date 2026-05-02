# rocketmatter-mcp

MCP server for [Rocketmatter](https://rocketmatter.com) — full API coverage for legal practice management. Use Rocketmatter from Claude Desktop with natural language.

## What you can do

- **Matters** — create, update, search, manage billing info, budgets, status, custom fields, court rules
- **Clients & Contacts** — full CRUD, search, custom fields, contact data
- **Tasks** — create, assign, complete, filter by matter or user
- **Time & Expenses** — log billable time and expenses, manage activity types, LEDES codes
- **Timers** — start, pause, bill running timers
- **Invoices** — generate invoices, record payments, process refunds, manage templates
- **Calendar** — appointments linked to matters, availability checks, date range queries
- **Documents** — manage document records, folders, versions, download keys, templates
- **Trust Accounting** — view trust balances per matter
- **Rates** — custom matter rates, tax rates, discounts, surcharges, interest rates
- **Workflow** — matter workflow statuses, apply transitions
- **Reports** — run and retrieve firm reports
- **Search** — global search across all entities
- **Internal Messaging** — direct messages, channels
- **Court Rules** — apply court rules, calculate deadlines
- **Matter Templates** — create matters from templates
- **Recurring Billing** — payment plans

## Requirements

- Python 3.10+
- Claude Desktop (or any MCP-compatible client)
- Rocketmatter credentials (domain, install path, username, password)

## Installation

```bash
pip install rocketmatter-mcp
```

## Setup

```bash
rocketmatter-mcp-setup
```

This prompts for your Rocketmatter domain, install path, username and password, then saves credentials to `~/.rocketmatter-mcp/`.

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

## Authentication Notes

Rocketmatter uses a username/password token flow via the `GrantToken` endpoint — no browser or OAuth redirect required. Tokens are refreshed automatically. Your credentials are stored locally at `~/.rocketmatter-mcp/.env` with 600 permissions.

The base URL is constructed from your domain and install path:
```
{DOMAIN}/{INSTALL}/API_V2
```

For example: `https://app.rocketmatter.com/myfirm123/API_V2`

## Example usage in Claude

> "Search my matters for Smith"

> "Log 2 hours on matter 456 for drafting the complaint"

> "Get all upcoming calendar events for matter 789"

> "Run an invoice for matter 123"

> "Show me the trust account balance for matter 456"

> "Calculate court deadlines for rule 12 from 2026-06-01"

## License

MIT
