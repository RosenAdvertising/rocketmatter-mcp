#!/usr/bin/env python3
"""Rocketmatter MCP server — FastMCP tools for the Rocketmatter API."""

import json
from mcp.server.fastmcp import FastMCP
from rocketmatter_mcp.client import RocketMatterClient

mcp = FastMCP(
    "rocketmatter",
    instructions=(
        "Rocketmatter legal practice management. "
        "Manage matters, clients, tasks, time entries, invoices, calendar, documents, and more. "
        "Matters are the core entity — most resources link to a matter ID."
    ),
)


def _c():
    return RocketMatterClient()


def _fields(fields_json: str) -> dict:
    if not fields_json:
        return {}
    return json.loads(fields_json)


# ── Matters ────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_matter(matter_id: int) -> str:
    """Get a matter by ID."""
    return json.dumps(_c().get_matter(matter_id), indent=2)


@mcp.tool()
def save_matter(
    name: str = "",
    client_matter: str = "",
    matter_type_id: int = 0,
    status_id: int = 0,
    client_id: int = 0,
    fields_json: str = "",
) -> str:
    """Create or update a matter. Omit ID to create; include ID to update."""
    data = _fields(fields_json)
    if name:
        data["Name"] = name
    if client_matter:
        data["ClientMatter"] = client_matter
    if matter_type_id:
        data["MatterTypeID"] = matter_type_id
    if status_id:
        data["MatterStatusTypeId"] = status_id
    if client_id:
        data.setdefault("Client", {})["ContactID"] = client_id
    return json.dumps(_c().save_matter(**data), indent=2)


@mcp.tool()
def search_matters(search_term: str, page: int = 1, page_size: int = 50) -> str:
    """Search matters by name, client name, or matter number."""
    return json.dumps(_c().search_matters(search_term, page, page_size), indent=2)


@mcp.tool()
def get_matter_billing_info(matter_id: int) -> str:
    """Get billing information for a matter."""
    return json.dumps(_c().get_matter_billing_info(matter_id), indent=2)


@mcp.tool()
def get_matter_budget_info(matter_id: int) -> str:
    """Get budget information for a matter."""
    return json.dumps(_c().get_matter_budget_info(matter_id), indent=2)


@mcp.tool()
def get_matter_budget(matter_id: int) -> str:
    """Get the budget settings for a matter."""
    return json.dumps(_c().get_matter_budget(matter_id), indent=2)


@mcp.tool()
def update_matter_budget(matter_id: int, fields_json: str = "") -> str:
    """Update budget settings for a matter. fields_json is a JSON object."""
    data = _fields(fields_json)
    return json.dumps(_c().update_matter_budget(matter_id, **data), indent=2)


@mcp.tool()
def update_matter_status(matter_id: int, status_id: int) -> str:
    """Update the status of a matter."""
    return json.dumps(_c().update_matter_status(matter_id, status_id), indent=2)


@mcp.tool()
def delete_matter(matter_id: int) -> str:
    """Delete a matter by ID."""
    return json.dumps(_c().delete_matter(matter_id), indent=2)


@mcp.tool()
def get_matter_details(matter_id: int) -> str:
    """Get detailed information for a matter."""
    return json.dumps(_c().get_matter_details(matter_id), indent=2)


@mcp.tool()
def get_matter_by_client_matter(client_matter: str) -> str:
    """Get a matter by its client/matter number string."""
    return json.dumps(_c().get_matter_by_client_matter(client_matter), indent=2)


@mcp.tool()
def does_client_matter_exist(client_matter: str) -> str:
    """Check if a client/matter number already exists."""
    return json.dumps(_c().does_client_matter_exist(client_matter), indent=2)


@mcp.tool()
def get_matter_custom_fields(matter_id: int) -> str:
    """Get custom fields for a matter."""
    return json.dumps(_c().get_matter_custom_fields(matter_id), indent=2)


@mcp.tool()
def delete_matter_custom_field(field_id: int) -> str:
    """Delete a custom field from a matter."""
    return json.dumps(_c().delete_matter_custom_field(field_id), indent=2)


@mcp.tool()
def get_matter_email_folders(matter_id: int) -> str:
    """Get the email folders associated with a matter."""
    return json.dumps(_c().get_matter_email_folders(matter_id), indent=2)


@mcp.tool()
def get_effective_rates_for_matter(matter_id: int, date: str) -> str:
    """Get effective billing rates for a matter from a specific date (ISO 8601)."""
    return json.dumps(_c().get_effective_rates_for_matter(matter_id, date), indent=2)


@mcp.tool()
def search_matter_custom_fields(search_term: str) -> str:
    """Search matters by custom field values."""
    return json.dumps(_c().search_matter_custom_fields(search_term), indent=2)


@mcp.tool()
def get_matter_shared_invoice_settings(matter_id: int) -> str:
    """Get shared invoice settings for a matter."""
    return json.dumps(_c().get_matter_shared_invoice_settings(matter_id), indent=2)


@mcp.tool()
def get_matter_types() -> str:
    """Get all available matter types."""
    return json.dumps(_c().get_matter_types(), indent=2)


# ── Clients ────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_all_clients() -> str:
    """Get all clients in the firm."""
    return json.dumps(_c().get_all_clients(), indent=2)


@mcp.tool()
def save_client(
    name: str = "",
    last_name: str = "",
    first_name: str = "",
    work_email: str = "",
    mobile_phone: str = "",
    is_company: bool = False,
    fields_json: str = "",
) -> str:
    """Create or update a client. Omit ContactID to create; include to update."""
    data = _fields(fields_json)
    if name:
        data["Name"] = name
    if last_name:
        data["LastName"] = last_name
    if first_name:
        data["FirstName"] = first_name
    if work_email:
        data["WorkEmail"] = work_email
    if mobile_phone:
        data["MobilePhone"] = mobile_phone
    if is_company:
        data["IsCompany"] = True
    return json.dumps(_c().save_client(**data), indent=2)


@mcp.tool()
def search_clients(search_term: str) -> str:
    """Search clients by name or email."""
    return json.dumps(_c().search_clients(search_term), indent=2)


@mcp.tool()
def get_client_by_code(code: str) -> str:
    """Get a client by their client code."""
    return json.dumps(_c().get_client_by_code(code), indent=2)


@mcp.tool()
def get_countries() -> str:
    """Get the list of available countries."""
    return json.dumps(_c().get_countries(), indent=2)


@mcp.tool()
def create_client_from_string(client_string: str) -> str:
    """Create a client from a formatted name string."""
    return json.dumps(_c().create_client_from_string(client_string), indent=2)


# ── Contacts ───────────────────────────────────────────────────────────────────

@mcp.tool()
def get_contact_by_id(contact_id: int) -> str:
    """Get a contact by their ID."""
    return json.dumps(_c().get_contact_by_id(contact_id), indent=2)


@mcp.tool()
def save_contact(
    first_name: str = "",
    last_name: str = "",
    work_email: str = "",
    mobile_phone: str = "",
    is_company: bool = False,
    company_name: str = "",
    fields_json: str = "",
) -> str:
    """Create or update a contact."""
    data = _fields(fields_json)
    if first_name:
        data["FirstName"] = first_name
    if last_name:
        data["LastName"] = last_name
    if work_email:
        data["WorkEmail"] = work_email
    if mobile_phone:
        data["MobilePhone"] = mobile_phone
    if is_company:
        data["IsCompany"] = True
    if company_name:
        data["CompanyName"] = company_name
    return json.dumps(_c().save_contact(**data), indent=2)


@mcp.tool()
def delete_contact(contact_id: int) -> str:
    """Delete a contact by ID."""
    return json.dumps(_c().delete_contact(contact_id), indent=2)


@mcp.tool()
def search_contacts(search_term: str) -> str:
    """Search all contacts by name or email."""
    return json.dumps(_c().search_contacts(search_term), indent=2)


@mcp.tool()
def search_person_contacts(search_term: str) -> str:
    """Search only person (non-company) contacts."""
    return json.dumps(_c().search_person_contacts(search_term), indent=2)


@mcp.tool()
def get_person_contacts() -> str:
    """Get all person (non-company) contacts."""
    return json.dumps(_c().get_person_contacts(), indent=2)


@mcp.tool()
def get_contact_data(contact_id: int) -> str:
    """Get extended data for a contact."""
    return json.dumps(_c().get_contact_data(contact_id), indent=2)


@mcp.tool()
def get_contact_custom_fields(contact_id: int) -> str:
    """Get custom fields for a contact."""
    return json.dumps(_c().get_contact_custom_fields(contact_id), indent=2)


@mcp.tool()
def delete_contact_custom_field(field_id: int) -> str:
    """Delete a custom field from a contact."""
    return json.dumps(_c().delete_contact_custom_field(field_id), indent=2)


@mcp.tool()
def get_contacts(page: int = 1, page_size: int = 50) -> str:
    """Get a paginated list of all contacts."""
    return json.dumps(_c().get_contacts(page, page_size), indent=2)


# ── Tasks ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_tasks_for_matter(matter_id: int) -> str:
    """Get all tasks for a specific matter."""
    return json.dumps(_c().get_tasks_for_matter(matter_id), indent=2)


@mcp.tool()
def get_tasks_by_filter(
    user_id: int = 0,
    is_completed: bool = False,
    fields_json: str = "",
) -> str:
    """Get tasks by filter. Use fields_json for additional filter criteria."""
    filters = _fields(fields_json)
    if user_id:
        filters["UserId"] = user_id
    if is_completed:
        filters["IsCompleted"] = True
    return json.dumps(_c().get_tasks_by_filter(**filters), indent=2)


@mcp.tool()
def get_task_by_activity_id(activity_id: int) -> str:
    """Get a task by its activity ID."""
    return json.dumps(_c().get_task_by_activity_id(activity_id), indent=2)


@mcp.tool()
def save_task(
    matter_id: int = 0,
    subject: str = "",
    due_date: str = "",
    assigned_to_id: int = 0,
    is_completed: bool = False,
    fields_json: str = "",
) -> str:
    """Create or update a task. Omit ID to create; include to update."""
    data = _fields(fields_json)
    if matter_id:
        data["MatterId"] = matter_id
    if subject:
        data["Subject"] = subject
    if due_date:
        data["DueDate"] = due_date
    if assigned_to_id:
        data["AssignedToId"] = assigned_to_id
    if is_completed:
        data["IsCompleted"] = True
    return json.dumps(_c().save_task(**data), indent=2)


@mcp.tool()
def delete_task(task_id: int) -> str:
    """Delete a task by ID."""
    return json.dumps(_c().delete_task(task_id), indent=2)


@mcp.tool()
def get_common_tags() -> str:
    """Get commonly used tags for tasks."""
    return json.dumps(_c().get_common_tags(), indent=2)


# ── Billable Activity (Time & Expenses) ────────────────────────────────────────

@mcp.tool()
def get_billable_activities(matter_id: int) -> str:
    """Get all billable activities (time entries and expenses) for a matter."""
    return json.dumps(_c().get_billable_activities(matter_id), indent=2)


@mcp.tool()
def save_billable_time(
    matter_id: int,
    user_id: int,
    total_seconds: int,
    notes: str = "",
    activity_type_id: int = 0,
    date_and_time: str = "",
) -> str:
    """Log billable time on a matter. total_seconds is the duration billed."""
    return json.dumps(_c().save_billable_time(
        matter_id, user_id, total_seconds, notes, activity_type_id, date_and_time
    ), indent=2)


@mcp.tool()
def save_expense(
    matter_id: int,
    user_id: int,
    amount: float,
    notes: str = "",
    activity_type_id: int = 0,
    date_and_time: str = "",
) -> str:
    """Log an expense on a matter."""
    return json.dumps(_c().save_expense(
        matter_id, user_id, amount, notes, activity_type_id, date_and_time
    ), indent=2)


@mcp.tool()
def get_time_expense(activity_id: int) -> str:
    """Get a specific time entry or expense by activity ID."""
    return json.dumps(_c().get_time_expense(activity_id), indent=2)


@mcp.tool()
def delete_activity(activity_id: int) -> str:
    """Delete a billable activity (time entry or expense)."""
    return json.dumps(_c().delete_activity(activity_id), indent=2)


@mcp.tool()
def get_activities_for_matter(matter_id: int) -> str:
    """Get all time and expense activities for a matter."""
    return json.dumps(_c().get_activities_for_matter(matter_id), indent=2)


@mcp.tool()
def get_firm_balances() -> str:
    """Get overall firm billing balances."""
    return json.dumps(_c().get_firm_balances(), indent=2)


@mcp.tool()
def get_activity_type_id(name: str) -> str:
    """Look up an activity type ID by name."""
    return json.dumps(_c().get_activity_type_id(name), indent=2)


@mcp.tool()
def get_all_ledes() -> str:
    """Get all LEDES billing codes."""
    return json.dumps(_c().get_all_ledes(), indent=2)


# ── Timer ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def start_timer(matter_id: int, user_id: int) -> str:
    """Start a new timer for a matter and user."""
    return json.dumps(_c().start_timer(matter_id, user_id), indent=2)


@mcp.tool()
def pause_timer(timer_id: int) -> str:
    """Pause a running timer."""
    return json.dumps(_c().pause_timer(timer_id), indent=2)


@mcp.tool()
def bill_timer(timer_id: int) -> str:
    """Convert a timer into a billable time entry."""
    return json.dumps(_c().bill_timer(timer_id), indent=2)


@mcp.tool()
def get_timer(timer_id: int) -> str:
    """Get a timer by ID."""
    return json.dumps(_c().get_timer(timer_id), indent=2)


@mcp.tool()
def get_all_non_billed_timers(user_id: int) -> str:
    """Get all unbilled timers for a user."""
    return json.dumps(_c().get_all_non_billed_timers(user_id), indent=2)


@mcp.tool()
def save_timer(matter_id: int = 0, user_id: int = 0, fields_json: str = "") -> str:
    """Create or update a timer entry."""
    data = _fields(fields_json)
    if matter_id:
        data["MatterId"] = matter_id
    if user_id:
        data["UserId"] = user_id
    return json.dumps(_c().save_timer(**data), indent=2)


@mcp.tool()
def delete_timer(timer_id: int) -> str:
    """Delete a timer by ID."""
    return json.dumps(_c().delete_timer(timer_id), indent=2)


# ── Invoices ───────────────────────────────────────────────────────────────────

@mcp.tool()
def run_invoice(matter_id: int, fields_json: str = "") -> str:
    """Generate an invoice for a matter."""
    data = _fields(fields_json)
    return json.dumps(_c().run_invoice(matter_id, **data), indent=2)


@mcp.tool()
def get_invoice_payments_for_matter(matter_id: int) -> str:
    """Get all invoice payments for a matter."""
    return json.dumps(_c().get_invoice_payments_for_matter(matter_id), indent=2)


@mcp.tool()
def record_payments_to_invoices(fields_json: str) -> str:
    """Record payments against invoices. fields_json is a JSON object."""
    data = _fields(fields_json)
    return json.dumps(_c().record_payments_to_invoices(**data), indent=2)


@mcp.tool()
def delete_payment(payment_id: int) -> str:
    """Delete a payment record."""
    return json.dumps(_c().delete_payment(payment_id), indent=2)


@mcp.tool()
def get_payments_for_matter(matter_id: int) -> str:
    """Get all payments received for a matter."""
    return json.dumps(_c().get_payments_for_matter(matter_id), indent=2)


@mcp.tool()
def process_refund(fields_json: str) -> str:
    """Process a refund. fields_json is a JSON object with refund details."""
    data = _fields(fields_json)
    return json.dumps(_c().process_refund(**data), indent=2)


@mcp.tool()
def get_most_recent_invoice_by_client(client_id: int) -> str:
    """Get the most recent invoice information for a client."""
    return json.dumps(_c().get_most_recent_invoice_by_client(client_id), indent=2)


@mcp.tool()
def get_available_invoice_templates() -> str:
    """Get all available invoice templates."""
    return json.dumps(_c().get_available_invoice_templates(), indent=2)


@mcp.tool()
def save_invoice_template(fields_json: str) -> str:
    """Create or update an invoice template. fields_json is a JSON object."""
    data = _fields(fields_json)
    return json.dumps(_c().save_invoice_template(**data), indent=2)


@mcp.tool()
def delete_invoice_template(template_id: int) -> str:
    """Delete an invoice template."""
    return json.dumps(_c().delete_invoice_template(template_id), indent=2)


@mcp.tool()
def save_retainer_request(fields_json: str) -> str:
    """Save a retainer request. fields_json is a JSON object."""
    data = _fields(fields_json)
    return json.dumps(_c().save_retainer_request(**data), indent=2)


@mcp.tool()
def get_transaction_info(transaction_id: int) -> str:
    """Get details of a specific transaction."""
    return json.dumps(_c().get_transaction_info(transaction_id), indent=2)


# ── Calendar ───────────────────────────────────────────────────────────────────

@mcp.tool()
def get_upcoming_events_for_matter(matter_id: int) -> str:
    """Get upcoming calendar events for a matter."""
    return json.dumps(_c().get_upcoming_events_for_matter(matter_id), indent=2)


@mcp.tool()
def get_upcoming_events_for_user(user_id: int) -> str:
    """Get upcoming calendar events for a user."""
    return json.dumps(_c().get_upcoming_events_for_user(user_id), indent=2)


@mcp.tool()
def save_calendar_entry(
    matter_id: int = 0,
    subject: str = "",
    start_date: str = "",
    end_date: str = "",
    fields_json: str = "",
) -> str:
    """Create or update a calendar entry."""
    data = _fields(fields_json)
    if matter_id:
        data["MatterId"] = matter_id
    if subject:
        data["Subject"] = subject
    if start_date:
        data["StartDate"] = start_date
    if end_date:
        data["EndDate"] = end_date
    return json.dumps(_c().save_calendar_entry(**data), indent=2)


@mcp.tool()
def get_calendar_entry(entry_id: int) -> str:
    """Get a calendar entry by ID."""
    return json.dumps(_c().get_calendar_entry(entry_id), indent=2)


@mcp.tool()
def delete_calendar_entry(entry_id: int) -> str:
    """Delete a calendar entry."""
    return json.dumps(_c().delete_calendar_entry(entry_id), indent=2)


@mcp.tool()
def get_calendar_entries_for_date_range(
    start_date: str,
    end_date: str,
    user_id: int = 0,
) -> str:
    """Get calendar entries within a date range (ISO 8601 format)."""
    return json.dumps(_c().get_calendar_entries_for_date_range(start_date, end_date, user_id), indent=2)


@mcp.tool()
def check_contact_availability(contact_id: int, start_date: str, end_date: str) -> str:
    """Check if a contact is available during a date range."""
    return json.dumps(_c().check_contact_availability(contact_id, start_date, end_date), indent=2)


# ── Documents ──────────────────────────────────────────────────────────────────

@mcp.tool()
def get_documents_in_path(matter_id: int, path: str = "") -> str:
    """Get documents in a folder path for a matter."""
    return json.dumps(_c().get_documents_in_path(matter_id, path), indent=2)


@mcp.tool()
def get_document(document_id: int) -> str:
    """Get a document by ID."""
    return json.dumps(_c().get_document(document_id), indent=2)


@mcp.tool()
def get_directories(matter_id: int) -> str:
    """Get the folder directory structure for a matter."""
    return json.dumps(_c().get_directories(matter_id), indent=2)


@mcp.tool()
def save_document(
    matter_id: int = 0,
    name: str = "",
    path: str = "",
    fields_json: str = "",
) -> str:
    """Create or update a document record."""
    data = _fields(fields_json)
    if matter_id:
        data["MatterId"] = matter_id
    if name:
        data["Name"] = name
    if path:
        data["Path"] = path
    return json.dumps(_c().save_document(**data), indent=2)


@mcp.tool()
def delete_document(document_id: int) -> str:
    """Delete a document."""
    return json.dumps(_c().delete_document(document_id), indent=2)


@mcp.tool()
def move_documents_to_folder(
    document_ids_csv: str,
    folder_path: str,
    matter_id: int,
) -> str:
    """Move documents to a folder. document_ids_csv is a comma-separated list of IDs."""
    doc_ids = [int(d.strip()) for d in document_ids_csv.split(",") if d.strip()]
    return json.dumps(_c().move_documents_to_folder(doc_ids, folder_path, matter_id), indent=2)


@mcp.tool()
def rename_folder(matter_id: int, old_path: str, new_name: str) -> str:
    """Rename a document folder."""
    return json.dumps(_c().rename_folder(matter_id, old_path, new_name), indent=2)


@mcp.tool()
def get_document_download_key(document_id: int) -> str:
    """Get a download key/URL for a document."""
    return json.dumps(_c().get_document_download_key(document_id), indent=2)


@mcp.tool()
def get_document_versions(document_id: int) -> str:
    """Get version history for a document."""
    return json.dumps(_c().get_document_versions(document_id), indent=2)


@mcp.tool()
def get_document_file_info(document_id: int) -> str:
    """Get file metadata for a document."""
    return json.dumps(_c().get_document_file_info(document_id), indent=2)


@mcp.tool()
def get_document_upload_url(fields_json: str = "") -> str:
    """Get a pre-signed URL for document upload."""
    data = _fields(fields_json)
    return json.dumps(_c().get_document_upload_url(**data), indent=2)


@mcp.tool()
def delete_note(note_id: int) -> str:
    """Delete a document note."""
    return json.dumps(_c().delete_note(note_id), indent=2)


@mcp.tool()
def get_invoiced_documents(matter_id: int) -> str:
    """Get all invoiced documents for a matter."""
    return json.dumps(_c().get_invoiced_documents(matter_id), indent=2)


@mcp.tool()
def get_document_templates() -> str:
    """Get all document templates."""
    return json.dumps(_c().get_document_templates(), indent=2)


@mcp.tool()
def delete_document_template(template_id: int) -> str:
    """Delete a document template."""
    return json.dumps(_c().delete_document_template(template_id), indent=2)


# ── Users ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_current_user() -> str:
    """Get the currently authenticated user."""
    return json.dumps(_c().get_current_user(), indent=2)


@mcp.tool()
def get_user(user_id: int) -> str:
    """Get a user by ID."""
    return json.dumps(_c().get_user(user_id), indent=2)


@mcp.tool()
def search_users(search_term: str) -> str:
    """Search users by name."""
    return json.dumps(_c().search_users(search_term), indent=2)


@mcp.tool()
def get_active_users() -> str:
    """Get all active users in the firm."""
    return json.dumps(_c().get_active_users(), indent=2)


@mcp.tool()
def get_user_by_initials(initials: str) -> str:
    """Get a user by their initials."""
    return json.dumps(_c().get_user_by_initials(initials), indent=2)


@mcp.tool()
def get_user_by_full_name(full_name: str) -> str:
    """Get a user by their full name."""
    return json.dumps(_c().get_user_by_full_name(full_name), indent=2)


@mcp.tool()
def set_user_preference(key: str, value: str) -> str:
    """Set a user preference key-value pair."""
    return json.dumps(_c().set_user_preference(key, value), indent=2)


@mcp.tool()
def get_user_preference(key: str) -> str:
    """Get a user preference by key."""
    return json.dumps(_c().get_user_preference(key), indent=2)


@mcp.tool()
def get_effective_user_rates(user_id: int) -> str:
    """Get the effective billing rates for a user."""
    return json.dumps(_c().get_effective_user_rates(user_id), indent=2)


# ── Tags ───────────────────────────────────────────────────────────────────────

@mcp.tool()
def search_tags(search_term: str) -> str:
    """Search tags by name."""
    return json.dumps(_c().search_tags(search_term), indent=2)


@mcp.tool()
def add_tag(entity_id: int, entity_type: str, tag: str) -> str:
    """Add a tag to an entity (matter, contact, etc.)."""
    return json.dumps(_c().add_tag(entity_id, entity_type, tag), indent=2)


@mcp.tool()
def remove_tag(entity_id: int, entity_type: str, tag: str) -> str:
    """Remove a tag from an entity."""
    return json.dumps(_c().remove_tag(entity_id, entity_type, tag), indent=2)


# ── Trust ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_trust_details_for_matter(matter_id: int) -> str:
    """Get trust account details for a matter."""
    return json.dumps(_c().get_trust_details_for_matter(matter_id), indent=2)


# ── Rates ──────────────────────────────────────────────────────────────────────

@mcp.tool()
def get_matter_custom_rates(matter_id: int) -> str:
    """Get custom billing rates for a matter."""
    return json.dumps(_c().get_matter_custom_rates(matter_id), indent=2)


@mcp.tool()
def save_custom_rate_config(fields_json: str) -> str:
    """Save a custom rate configuration. fields_json is a JSON object."""
    data = _fields(fields_json)
    return json.dumps(_c().save_custom_rate_config(**data), indent=2)


@mcp.tool()
def delete_matter_rates(matter_id: int) -> str:
    """Delete all custom rates for a matter."""
    return json.dumps(_c().delete_matter_rates(matter_id), indent=2)


# ── Firm Roles ─────────────────────────────────────────────────────────────────

@mcp.tool()
def get_firm_roles() -> str:
    """Get all firm roles."""
    return json.dumps(_c().get_firm_roles(), indent=2)


@mcp.tool()
def save_firm_role(name: str = "", fields_json: str = "") -> str:
    """Create or update a firm role."""
    data = _fields(fields_json)
    if name:
        data["Name"] = name
    return json.dumps(_c().save_firm_role(**data), indent=2)


@mcp.tool()
def delete_firm_role(role_id: int) -> str:
    """Delete a firm role."""
    return json.dumps(_c().delete_firm_role(role_id), indent=2)


# ── Tax / Discount / Surcharge / Interest Rates ────────────────────────────────

@mcp.tool()
def get_all_tax_rates() -> str:
    """Get all tax rates configured in the firm."""
    return json.dumps(_c().get_all_tax_rates(), indent=2)


@mcp.tool()
def save_tax_rate(name: str = "", rate: float = 0.0, fields_json: str = "") -> str:
    """Create or update a tax rate."""
    data = _fields(fields_json)
    if name:
        data["Name"] = name
    if rate:
        data["Rate"] = rate
    return json.dumps(_c().save_tax_rate(**data), indent=2)


@mcp.tool()
def delete_tax_rate(rate_id: int) -> str:
    """Delete a tax rate."""
    return json.dumps(_c().delete_tax_rate(rate_id), indent=2)


@mcp.tool()
def get_all_discounts() -> str:
    """Get all discount rates."""
    return json.dumps(_c().get_all_discounts(), indent=2)


@mcp.tool()
def save_discount(name: str = "", rate: float = 0.0, fields_json: str = "") -> str:
    """Create or update a discount rate."""
    data = _fields(fields_json)
    if name:
        data["Name"] = name
    if rate:
        data["Rate"] = rate
    return json.dumps(_c().save_discount(**data), indent=2)


@mcp.tool()
def get_all_interests() -> str:
    """Get all interest rates."""
    return json.dumps(_c().get_all_interests(), indent=2)


@mcp.tool()
def save_interest(name: str = "", rate: float = 0.0, fields_json: str = "") -> str:
    """Create or update an interest rate."""
    data = _fields(fields_json)
    if name:
        data["Name"] = name
    if rate:
        data["Rate"] = rate
    return json.dumps(_c().save_interest(**data), indent=2)


@mcp.tool()
def charge_interest_fees(matter_id: int) -> str:
    """Apply interest fees to a matter."""
    return json.dumps(_c().charge_interest_fees(matter_id), indent=2)


@mcp.tool()
def get_all_surcharge_rates() -> str:
    """Get all surcharge rates."""
    return json.dumps(_c().get_all_surcharge_rates(), indent=2)


@mcp.tool()
def save_surcharge_rate(name: str = "", rate: float = 0.0, fields_json: str = "") -> str:
    """Create or update a surcharge rate."""
    data = _fields(fields_json)
    if name:
        data["Name"] = name
    if rate:
        data["Rate"] = rate
    return json.dumps(_c().save_surcharge_rate(**data), indent=2)


@mcp.tool()
def delete_surcharge_rate(rate_id: int) -> str:
    """Delete a surcharge rate."""
    return json.dumps(_c().delete_surcharge_rate(rate_id), indent=2)


# ── Messages ───────────────────────────────────────────────────────────────────

@mcp.tool()
def save_phone_message(
    matter_id: int,
    contact_id: int,
    message: str,
    fields_json: str = "",
) -> str:
    """Save a phone message record on a matter."""
    data = _fields(fields_json)
    return json.dumps(_c().save_phone_message(matter_id, contact_id, message, **data), indent=2)


@mcp.tool()
def get_phone_message(message_id: int) -> str:
    """Get a phone message by ID."""
    return json.dumps(_c().get_phone_message(message_id), indent=2)


# ── Communicator (Internal Chat) ───────────────────────────────────────────────

@mcp.tool()
def get_channels_i_belong_to() -> str:
    """Get all chat channels the current user belongs to."""
    return json.dumps(_c().get_channels_i_belong_to(), indent=2)


@mcp.tool()
def send_direct_message(to_user_id: int, message: str) -> str:
    """Send a direct message to a user."""
    return json.dumps(_c().send_direct_message(to_user_id, message), indent=2)


@mcp.tool()
def send_channel_message(channel_id: int, message: str) -> str:
    """Send a message to a channel."""
    return json.dumps(_c().send_channel_message(channel_id, message), indent=2)


@mcp.tool()
def get_direct_chat(user_id: int) -> str:
    """Get the direct message chat history with a user."""
    return json.dumps(_c().get_direct_chat(user_id), indent=2)


@mcp.tool()
def get_channel_chat(channel_id: int) -> str:
    """Get the chat history for a channel."""
    return json.dumps(_c().get_channel_chat(channel_id), indent=2)


@mcp.tool()
def get_unread_direct_messages() -> str:
    """Get all unread direct messages."""
    return json.dumps(_c().get_unread_direct_messages(), indent=2)


@mcp.tool()
def get_unread_channel_messages() -> str:
    """Get all unread channel messages."""
    return json.dumps(_c().get_unread_channel_messages(), indent=2)


@mcp.tool()
def save_channel(name: str = "", fields_json: str = "") -> str:
    """Create or update a chat channel."""
    data = _fields(fields_json)
    if name:
        data["Name"] = name
    return json.dumps(_c().save_channel(**data), indent=2)


@mcp.tool()
def delete_channel(channel_id: int) -> str:
    """Delete a chat channel."""
    return json.dumps(_c().delete_channel(channel_id), indent=2)


# ── Workflow ───────────────────────────────────────────────────────────────────

@mcp.tool()
def get_matter_current_workflow_status(matter_id: int) -> str:
    """Get the current workflow status for a matter."""
    return json.dumps(_c().get_matter_current_workflow_status(matter_id), indent=2)


@mcp.tool()
def get_matter_workflow_statuses(matter_id: int) -> str:
    """Get all workflow statuses available for a matter."""
    return json.dumps(_c().get_matter_workflow_statuses(matter_id), indent=2)


@mcp.tool()
def apply_new_matter_workflow_status(matter_id: int, status_id: int) -> str:
    """Apply a new workflow status to a matter."""
    return json.dumps(_c().apply_new_matter_workflow_status(matter_id, status_id), indent=2)


@mcp.tool()
def add_edit_workflow_status(name: str = "", fields_json: str = "") -> str:
    """Add or edit a workflow status definition."""
    data = _fields(fields_json)
    if name:
        data["Name"] = name
    return json.dumps(_c().add_edit_workflow_status(**data), indent=2)


# ── Reports ────────────────────────────────────────────────────────────────────

@mcp.tool()
def run_report(report_id: int, fields_json: str = "") -> str:
    """Run a report by ID with optional parameters."""
    data = _fields(fields_json)
    return json.dumps(_c().run_report(report_id, **data), indent=2)


@mcp.tool()
def get_report_summary() -> str:
    """Get a summary of all available reports."""
    return json.dumps(_c().get_report_summary(), indent=2)


@mcp.tool()
def get_report_metadata(report_id: int) -> str:
    """Get metadata and parameters for a specific report."""
    return json.dumps(_c().get_report_metadata(report_id), indent=2)


# ── Search ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def global_search(search_term: str) -> str:
    """Search across all entities — matters, clients, contacts, documents."""
    return json.dumps(_c().global_search(search_term), indent=2)


@mcp.tool()
def search_occurrence_for_type(search_term: str, entity_type: str) -> str:
    """Search for a term within a specific entity type."""
    return json.dumps(_c().search_occurrence_for_type(search_term, entity_type), indent=2)


# ── Recurring Billing ──────────────────────────────────────────────────────────

@mcp.tool()
def get_matter_payment_plan(matter_id: int) -> str:
    """Get the recurring payment plan for a matter."""
    return json.dumps(_c().get_matter_payment_plan(matter_id), indent=2)


@mcp.tool()
def generate_payment_plan(fields_json: str) -> str:
    """Generate a payment plan. fields_json is a JSON object with plan details."""
    data = _fields(fields_json)
    return json.dumps(_c().generate_payment_plan(**data), indent=2)


@mcp.tool()
def commit_payment_plan(fields_json: str) -> str:
    """Commit and activate a payment plan."""
    data = _fields(fields_json)
    return json.dumps(_c().commit_payment_plan(**data), indent=2)


@mcp.tool()
def cancel_payment_plan(plan_id: int) -> str:
    """Cancel a recurring payment plan."""
    return json.dumps(_c().cancel_payment_plan(plan_id), indent=2)


# ── Matter Templates ───────────────────────────────────────────────────────────

@mcp.tool()
def get_all_matter_templates() -> str:
    """Get all matter templates."""
    return json.dumps(_c().get_all_matter_templates(), indent=2)


@mcp.tool()
def get_matter_template(template_id: int) -> str:
    """Get a matter template by ID."""
    return json.dumps(_c().get_matter_template(template_id), indent=2)


@mcp.tool()
def save_matter_template(name: str = "", fields_json: str = "") -> str:
    """Create or update a matter template."""
    data = _fields(fields_json)
    if name:
        data["Name"] = name
    return json.dumps(_c().save_matter_template(**data), indent=2)


@mcp.tool()
def delete_matter_template(template_id: int) -> str:
    """Delete a matter template."""
    return json.dumps(_c().delete_matter_template(template_id), indent=2)


@mcp.tool()
def get_new_matter_from_template(template_id: int) -> str:
    """Create a new matter pre-populated from a template."""
    return json.dumps(_c().get_new_matter_from_template(template_id), indent=2)


# ── Court Rules ────────────────────────────────────────────────────────────────

@mcp.tool()
def get_matter_court_rules(matter_id: int) -> str:
    """Get court rules applied to a matter."""
    return json.dumps(_c().get_matter_court_rules(matter_id), indent=2)


@mcp.tool()
def add_matter_court_rule(matter_id: int, court_rule_id: int) -> str:
    """Apply a court rule to a matter."""
    return json.dumps(_c().add_matter_court_rule(matter_id, court_rule_id), indent=2)


@mcp.tool()
def delete_matter_court_rule(matter_court_rule_id: int) -> str:
    """Remove a court rule from a matter."""
    return json.dumps(_c().delete_matter_court_rule(matter_court_rule_id), indent=2)


@mcp.tool()
def get_available_court_rules() -> str:
    """Get all available court rules in the system."""
    return json.dumps(_c().get_available_court_rules(), indent=2)


@mcp.tool()
def calculate_deadlines(court_rule_id: int, trigger_date: str) -> str:
    """Calculate court deadlines for a rule from a trigger date (ISO 8601)."""
    return json.dumps(_c().calculate_deadlines(court_rule_id, trigger_date), indent=2)


# ── Reference Data ─────────────────────────────────────────────────────────────

@mcp.tool()
def get_firm_features() -> str:
    """Get the features enabled for this firm."""
    return json.dumps(_c().get_firm_features(), indent=2)


@mcp.tool()
def get_time_options() -> str:
    """Get time rounding and billing increment options."""
    return json.dumps(_c().get_time_options(), indent=2)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
