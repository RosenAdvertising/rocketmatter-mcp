# rocketmatter-mcp

[![PyPI version](https://img.shields.io/pypi/v/rocketmatter-mcp.svg)](https://pypi.org/project/rocketmatter-mcp/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
- Rocketmatter account at app.rocketmatter.net

## Installation

```bash
pip install rocketmatter-mcp
```

## Setup

```bash
rocketmatter-mcp-setup
```

This opens your browser to authorize via Rocketmatter OAuth. Log in, click Allow, and the script captures the callback and saves tokens automatically. No manual credential entry required.

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

Rocketmatter uses OAuth 2.0. Tokens are stored at `~/.rocketmatter-mcp/tokens.json` (chmod 600) and refreshed automatically. Access tokens expire in ~5 hours; the MCP handles refresh silently. If the refresh token expires, re-run `rocketmatter-mcp-setup`.

## Example usage in Claude

> "Search my matters for Smith"
>
> "Log 2 hours on matter 456 for drafting the complaint"
>
> "Get all upcoming calendar events for matter 789"
>
> "Run an invoice for matter 123"
>
> "Show me the trust account balance for matter 456"
>
> "Calculate court deadlines for rule 12 from 2026-06-01"

## License

MIT
