#!/usr/bin/env python3
"""Rocketmatter MCP server — LCS Integration API tools."""

import json
from functools import wraps
from mcp.server.fastmcp import FastMCP
from rocketmatter_mcp.client import LCSClient

mcp = FastMCP(
    "rocketmatter",
    instructions=(
        "Rocketmatter legal practice management via the ProfitSolv LCS Integration API. "
        "Manage matters, clients, contacts, time entries, expenses, invoices, "
        "payments, transactions, and documents. "
        "Matters are the core entity — most resources link to a matter ID."
    ),
)

_raw_tool = mcp.tool


def _safe_tool(*args, **kwargs):
    def decorator(fn):
        @wraps(fn)
        def wrapped(*fn_args, **fn_kwargs):
            try:
                return fn(*fn_args, **fn_kwargs)
            except Exception as e:
                return json.dumps({"error": str(e)})

        return _raw_tool(*args, **kwargs)(wrapped)

    return decorator


mcp.tool = _safe_tool


def _c():
    return LCSClient()


def _fields(fields_json: str) -> dict:
    if not fields_json:
        return {}
    try:
        fields = json.loads(fields_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid fields_json: {e}") from e
    if not isinstance(fields, dict):
        raise ValueError("fields_json must be a JSON object")
    return fields


# ── Matters ────────────────────────────────────────────────────────────────────


@mcp.tool()
def list_matters(
    page: int = 1,
    page_size: int = 25,
    active_only: bool = None,
    search_text: str = None,
    matter_owner_id: int = None,
) -> str:
    """List matters. Supports pagination, search, and active-only filter."""
    return json.dumps(
        _c().list_matters(
            page=page,
            page_size=page_size,
            active_only=active_only,
            search_text=search_text,
            matter_owner_id=matter_owner_id,
        ),
        indent=2,
    )


@mcp.tool()
def get_matter(matter_id: int) -> str:
    """Get a matter by ID."""
    return json.dumps(_c().get_matter(matter_id), indent=2)


@mcp.tool()
def create_matter(fields_json: str) -> str:
    """Create a matter. fields_json: JSON object with matter fields.
    Required: clientId. Optional: billingMethod, dateOpened, matterOwnerId,
    areaOfLawId, matterName, matterFileNumber, notes, matterTypeId."""
    return json.dumps(_c().create_matter(**_fields(fields_json)), indent=2)


@mcp.tool()
def update_matter(matter_id: int, fields_json: str) -> str:
    """Update a matter by ID. fields_json: JSON object with fields to update."""
    return json.dumps(_c().update_matter(matter_id, **_fields(fields_json)), indent=2)


@mcp.tool()
def delete_matter(matter_id: int) -> str:
    """Delete a matter by ID."""
    return json.dumps(_c().delete_matter(matter_id), indent=2)


# ── Clients ────────────────────────────────────────────────────────────────────


@mcp.tool()
def list_clients(
    page: int = 1,
    page_size: int = 25,
    active_only: bool = None,
    display_name: str = None,
    name: str = None,
) -> str:
    """List clients. Supports search by display_name or name."""
    return json.dumps(
        _c().list_clients(
            page=page,
            page_size=page_size,
            active_only=active_only,
            display_name=display_name,
            name=name,
        ),
        indent=2,
    )


@mcp.tool()
def get_client(client_id: int) -> str:
    """Get a client by ID."""
    return json.dumps(_c().get_client(client_id), indent=2)


@mcp.tool()
def create_client(fields_json: str) -> str:
    """Create a client. fields_json: JSON object. Required: name.
    Optional: displayName, contactSalutation, contactTitle, entityName,
    address1, clientAsEntity, email, secondaryEmail, cellPhoneNumber."""
    return json.dumps(_c().create_client(**_fields(fields_json)), indent=2)


@mcp.tool()
def update_client(client_id: int, fields_json: str) -> str:
    """Update a client by ID. fields_json: JSON object with fields to update."""
    return json.dumps(_c().update_client(client_id, **_fields(fields_json)), indent=2)


@mcp.tool()
def delete_client(client_id: int) -> str:
    """Delete a client by ID."""
    return json.dumps(_c().delete_client(client_id), indent=2)


# ── Contacts ───────────────────────────────────────────────────────────────────


@mcp.tool()
def list_contacts(page: int = 1, page_size: int = 25) -> str:
    """List contacts with pagination."""
    return json.dumps(_c().list_contacts(page=page, page_size=page_size), indent=2)


@mcp.tool()
def get_contact(contact_id: int) -> str:
    """Get a contact by ID."""
    return json.dumps(_c().get_contact(contact_id), indent=2)


@mcp.tool()
def create_contact(fields_json: str) -> str:
    """Create a contact. fields_json: JSON object with contact fields."""
    return json.dumps(_c().create_contact(**_fields(fields_json)), indent=2)


@mcp.tool()
def update_contact(contact_id: int, fields_json: str) -> str:
    """Update a contact by ID."""
    return json.dumps(_c().update_contact(contact_id, **_fields(fields_json)), indent=2)


@mcp.tool()
def delete_contact(contact_id: int) -> str:
    """Delete a contact by ID."""
    return json.dumps(_c().delete_contact(contact_id), indent=2)


# ── Time Entries ───────────────────────────────────────────────────────────────


@mcp.tool()
def list_time_entries(
    matter_id: int = None,
    rate_type: str = None,
    billing_status: str = None,
    card_status: str = None,
    page: int = 1,
    page_size: int = 25,
) -> str:
    """List time entries. Filter by matter_id, rate_type, billing_status, card_status."""
    return json.dumps(
        _c().list_time_entries(
            matter_id=matter_id,
            rate_type=rate_type,
            billing_status=billing_status,
            card_status=card_status,
            page=page,
            page_size=page_size,
        ),
        indent=2,
    )


@mcp.tool()
def get_time_entry(time_entry_id: int) -> str:
    """Get a time entry by ID."""
    return json.dumps(_c().get_time_entry(time_entry_id), indent=2)


@mcp.tool()
def create_time_entry(fields_json: str) -> str:
    """Create a time entry. fields_json: JSON object. Required: matterId."""
    return json.dumps(_c().create_time_entry(**_fields(fields_json)), indent=2)


@mcp.tool()
def update_time_entry(time_entry_id: int, fields_json: str) -> str:
    """Update a time entry by ID."""
    return json.dumps(
        _c().update_time_entry(time_entry_id, **_fields(fields_json)), indent=2
    )


@mcp.tool()
def delete_time_entry(time_entry_id: int) -> str:
    """Delete a time entry by ID."""
    return json.dumps(_c().delete_time_entry(time_entry_id), indent=2)


# ── Expenses ───────────────────────────────────────────────────────────────────


@mcp.tool()
def list_expenses(
    billing_type_id: int = None,
    billing_status_id: int = None,
    page: int = 1,
    page_size: int = 25,
) -> str:
    """List expense cards."""
    return json.dumps(
        _c().list_expenses(
            billing_type_id=billing_type_id,
            billing_status_id=billing_status_id,
            page=page,
            page_size=page_size,
        ),
        indent=2,
    )


@mcp.tool()
def get_expense(expense_id: int) -> str:
    """Get an expense card by ID."""
    return json.dumps(_c().get_expense(expense_id), indent=2)


@mcp.tool()
def create_expense(fields_json: str) -> str:
    """Create an expense card. fields_json: JSON object. Required: matterId."""
    return json.dumps(_c().create_expense(**_fields(fields_json)), indent=2)


@mcp.tool()
def update_expense(expense_id: int, fields_json: str) -> str:
    """Update an expense card by ID."""
    return json.dumps(_c().update_expense(expense_id, **_fields(fields_json)), indent=2)


@mcp.tool()
def delete_expense(expense_id: int) -> str:
    """Delete an expense card by ID."""
    return json.dumps(_c().delete_expense(expense_id), indent=2)


# ── Invoices ───────────────────────────────────────────────────────────────────


@mcp.tool()
def list_invoices(page: int = 1, page_size: int = 25) -> str:
    """List invoices with pagination."""
    return json.dumps(_c().list_invoices(page=page, page_size=page_size), indent=2)


@mcp.tool()
def get_invoice(invoice_id: int) -> str:
    """Get an invoice by ID."""
    return json.dumps(_c().get_invoice(invoice_id), indent=2)


@mcp.tool()
def create_invoice(fields_json: str) -> str:
    """Create an invoice. fields_json: JSON object.
    Required: matterId, dueDate, invoiceDate, includeTimecardsToDate."""
    return json.dumps(_c().create_invoice(**_fields(fields_json)), indent=2)


@mcp.tool()
def update_invoice(invoice_id: int, fields_json: str) -> str:
    """Update an invoice by ID."""
    return json.dumps(_c().update_invoice(invoice_id, **_fields(fields_json)), indent=2)


@mcp.tool()
def delete_invoice(invoice_id: int) -> str:
    """Delete an invoice by ID."""
    return json.dumps(_c().delete_invoice(invoice_id), indent=2)


@mcp.tool()
def approve_invoice(invoice_id: int, invoice_number: str) -> str:
    """Approve a draft invoice for posting."""
    return json.dumps(_c().approve_invoice(invoice_id, invoice_number), indent=2)


# ── Payments ───────────────────────────────────────────────────────────────────


@mcp.tool()
def list_payments(page: int = 1, page_size: int = 25) -> str:
    """List invoice payments with pagination."""
    return json.dumps(_c().list_payments(page=page, page_size=page_size), indent=2)


@mcp.tool()
def create_payment(fields_json: str) -> str:
    """Create an invoice payment and allocate to invoices/trust."""
    return json.dumps(_c().create_payment(**_fields(fields_json)), indent=2)


@mcp.tool()
def get_invoice_allocations(fields_json: str = None) -> str:
    """Get invoice allocation suggestions for a payment."""
    return json.dumps(_c().get_invoice_allocations(**_fields(fields_json)), indent=2)


# ── Transactions ───────────────────────────────────────────────────────────────


@mcp.tool()
def list_transactions(page: int = 1, page_size: int = 25) -> str:
    """List transactions with pagination."""
    return json.dumps(_c().list_transactions(page=page, page_size=page_size), indent=2)


@mcp.tool()
def get_transaction(transaction_id: int) -> str:
    """Get a transaction by ID."""
    return json.dumps(_c().get_transaction(transaction_id), indent=2)


@mcp.tool()
def create_transaction(fields_json: str) -> str:
    """Create a transaction."""
    return json.dumps(_c().create_transaction(**_fields(fields_json)), indent=2)


@mcp.tool()
def update_transaction(transaction_id: int, fields_json: str) -> str:
    """Update a transaction by ID."""
    return json.dumps(
        _c().update_transaction(transaction_id, **_fields(fields_json)), indent=2
    )


@mcp.tool()
def delete_transaction(transaction_id: int) -> str:
    """Delete a transaction by ID."""
    return json.dumps(_c().delete_transaction(transaction_id), indent=2)


# ── Documents ──────────────────────────────────────────────────────────────────


@mcp.tool()
def list_documents(matter_id: int = None, path: str = None, doc_id: str = None) -> str:
    """List documents and folders. Filter by matter_id, path, or doc_id."""
    return json.dumps(
        _c().list_documents(matter_id=matter_id, path=path, doc_id=doc_id), indent=2
    )


@mcp.tool()
def get_document_default_app() -> str:
    """Get the default document gateway application configured in NextGen."""
    return json.dumps(_c().get_document_default_app(), indent=2)


@mcp.tool()
def get_document_download_url(fields_json: str) -> str:
    """Generate a signed download URL for a document."""
    return json.dumps(_c().get_document_download_url(**_fields(fields_json)), indent=2)


@mcp.tool()
def get_document_upload_url(fields_json: str) -> str:
    """Generate a signed upload URL for a document."""
    return json.dumps(_c().get_document_upload_url(**_fields(fields_json)), indent=2)


@mcp.tool()
def delete_document(path: str, doc_id: str) -> str:
    """Delete a document by gateway path and ID."""
    return json.dumps(_c().delete_document(path=path, doc_id=doc_id), indent=2)


# ── Users / Timekeepers ────────────────────────────────────────────────────────


@mcp.tool()
def list_users(page: int = 1, page_size: int = 25) -> str:
    """List users/timekeepers with pagination."""
    return json.dumps(_c().list_users(page=page, page_size=page_size), indent=2)


@mcp.tool()
def get_user(user_id: int) -> str:
    """Get a user/timekeeper by ID."""
    return json.dumps(_c().get_user(user_id), indent=2)


# ── Text Shortcuts ─────────────────────────────────────────────────────────────


@mcp.tool()
def list_text_shortcuts(page: int = 1, page_size: int = 25) -> str:
    """List text shortcuts/shorthands."""
    return json.dumps(
        _c().list_text_shortcuts(page=page, page_size=page_size), indent=2
    )


@mcp.tool()
def get_text_shortcut(shortcut_id: int) -> str:
    """Get a text shortcut by ID."""
    return json.dumps(_c().get_text_shortcut(shortcut_id), indent=2)


# ── Codes ──────────────────────────────────────────────────────────────────────


@mcp.tool()
def get_codes(matter_id: int) -> str:
    """Get all UTBMS task and activity codes for a matter in one call."""
    return json.dumps(_c().get_codes(matter_id), indent=2)


@mcp.tool()
def get_task_codes(matter_id: int) -> str:
    """Get UTBMS task codes for an eBilling-enabled matter."""
    return json.dumps(_c().get_task_codes(matter_id), indent=2)


@mcp.tool()
def get_activity_codes(matter_id: int) -> str:
    """Get UTBMS activity codes for an eBilling-enabled matter."""
    return json.dumps(_c().get_activity_codes(matter_id), indent=2)


# ── Lookups ────────────────────────────────────────────────────────────────────


@mcp.tool()
def get_new_matter_defaults() -> str:
    """Get global defaults for creating a new matter (billing methods, owners, types)."""
    return json.dumps(_c().get_new_matter_defaults(), indent=2)


@mcp.tool()
def get_new_matter_definition(matter_id: int = None) -> str:
    """Get NextGen defaults for a new or existing matter form."""
    return json.dumps(_c().get_new_matter_definition(matter_id=matter_id), indent=2)


@mcp.tool()
def get_ebilling_defaults() -> str:
    """Get eBilling defaults for enabling electronic billing on a matter."""
    return json.dumps(_c().get_ebilling_defaults(), indent=2)


@mcp.tool()
def get_matter_type_workflow(matter_type_id: int) -> str:
    """Get workflow statuses for a given matter type."""
    return json.dumps(_c().get_matter_type_workflow(matter_type_id), indent=2)


@mcp.tool()
def get_client_labels() -> str:
    """Get active client labels."""
    return json.dumps(_c().get_client_labels(), indent=2)


@mcp.tool()
def get_matter_labels() -> str:
    """Get active matter labels."""
    return json.dumps(_c().get_matter_labels(), indent=2)


@mcp.tool()
def get_client_suggestions(search: str = None) -> str:
    """Get client suggestions for the matter client selector."""
    return json.dumps(_c().get_client_suggestions(search=search), indent=2)


@mcp.tool()
def get_new_contact_defaults() -> str:
    """Get defaults and lookup lists for creating or editing a contact."""
    return json.dumps(_c().get_new_contact_defaults(), indent=2)


@mcp.tool()
def get_expense_lookups() -> str:
    """Get all lookup data required to create expense cards."""
    return json.dumps(_c().get_expense_lookups(), indent=2)


@mcp.tool()
def get_new_expense_lookups(matter_id: int = None) -> str:
    """Get lookup values for creating a soft cost expense card."""
    return json.dumps(_c().get_new_expense_lookups(matter_id=matter_id), indent=2)


@mcp.tool()
def get_invoice_lookups() -> str:
    """Get all lookup data required to create invoices."""
    return json.dumps(_c().get_invoice_lookups(), indent=2)


@mcp.tool()
def get_new_invoice_lookups(matter_id: int = None) -> str:
    """Get lookup values for creating an invoice."""
    return json.dumps(_c().get_new_invoice_lookups(matter_id=matter_id), indent=2)


@mcp.tool()
def get_invoice_payment_lookups() -> str:
    """Get lookup lists for invoice payment dropdowns."""
    return json.dumps(_c().get_invoice_payment_lookups(), indent=2)


@mcp.tool()
def get_time_entry_lookups(matter_id: int = None) -> str:
    """Get lookup values for creating or editing a time entry."""
    return json.dumps(_c().get_time_entry_lookups(matter_id=matter_id), indent=2)


@mcp.tool()
def get_time_grid_lookups() -> str:
    """Get lookup values for creating time entries from the time grid."""
    return json.dumps(_c().get_time_grid_lookups(), indent=2)


@mcp.tool()
def get_transaction_lookups() -> str:
    """Get lookup values for creating a new transaction."""
    return json.dumps(_c().get_transaction_lookups(), indent=2)


@mcp.tool()
def get_hard_cost_expense_lookups(matter_id: int = None) -> str:
    """Get matter-specific lookup values for creating a hard cost expense."""
    return json.dumps(_c().get_hard_cost_expense_lookups(matter_id=matter_id), indent=2)


# ── Accounts Payable ───────────────────────────────────────────────────────────


@mcp.tool()
def list_ap_bills(page: int = 1, page_size: int = 25) -> str:
    """List accounts payable bills."""
    return json.dumps(_c().list_ap_bills(page=page, page_size=page_size), indent=2)


@mcp.tool()
def get_ap_bill(bill_id: int) -> str:
    """Get an accounts payable bill by ID."""
    return json.dumps(_c().get_ap_bill(bill_id), indent=2)


@mcp.tool()
def create_ap_bill(fields_json: str) -> str:
    """Create an accounts payable bill."""
    return json.dumps(_c().create_ap_bill(**_fields(fields_json)), indent=2)


@mcp.tool()
def update_ap_bill(bill_id: int, fields_json: str) -> str:
    """Update an accounts payable bill by ID."""
    return json.dumps(_c().update_ap_bill(bill_id, **_fields(fields_json)), indent=2)


@mcp.tool()
def delete_ap_bill(bill_id: int) -> str:
    """Delete an accounts payable bill by ID."""
    return json.dumps(_c().delete_ap_bill(bill_id), indent=2)


@mcp.tool()
def list_ap_payments(page: int = 1, page_size: int = 25) -> str:
    """List accounts payable payments."""
    return json.dumps(_c().list_ap_payments(page=page, page_size=page_size), indent=2)


@mcp.tool()
def create_ap_payment(fields_json: str) -> str:
    """Trigger an accounts payable payment request."""
    return json.dumps(_c().create_ap_payment(**_fields(fields_json)), indent=2)


@mcp.tool()
def get_ap_payment_status(fields_json: str = None) -> str:
    """Get payment status information for AP bills or credits."""
    return json.dumps(_c().get_ap_payment_status(**_fields(fields_json)), indent=2)


@mcp.tool()
def list_ap_vendors(page: int = 1, page_size: int = 25) -> str:
    """List accounts payable vendors."""
    return json.dumps(_c().list_ap_vendors(page=page, page_size=page_size), indent=2)


@mcp.tool()
def get_ap_vendor(vendor_id: int) -> str:
    """Get an accounts payable vendor by ID."""
    return json.dumps(_c().get_ap_vendor(vendor_id), indent=2)


@mcp.tool()
def create_ap_vendor(fields_json: str) -> str:
    """Create an accounts payable vendor."""
    return json.dumps(_c().create_ap_vendor(**_fields(fields_json)), indent=2)


@mcp.tool()
def update_ap_vendor(vendor_id: int, fields_json: str) -> str:
    """Update an accounts payable vendor by ID."""
    return json.dumps(
        _c().update_ap_vendor(vendor_id, **_fields(fields_json)), indent=2
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
