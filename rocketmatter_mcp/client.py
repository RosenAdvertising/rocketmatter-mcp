#!/usr/bin/env python3
"""Rocketmatter API client. Token auth via GrantToken, all calls are POST with JSON body."""

import json
import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime, timezone

CONFIG_DIR = Path.home() / ".rocketmatter-mcp"


def _load_env():
    env_file = CONFIG_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())


_load_env()

DOMAIN = os.environ.get("ROCKETMATTER_DOMAIN", "")
INSTALL = os.environ.get("ROCKETMATTER_INSTALL", "")
USERNAME = os.environ.get("ROCKETMATTER_USERNAME", "")
PASSWORD = os.environ.get("ROCKETMATTER_PASSWORD", "")

BASE_URL = f"{DOMAIN.rstrip('/')}/{INSTALL}/API_V2" if DOMAIN and INSTALL else ""
AUTH_URL = f"{DOMAIN.rstrip('/')}/{INSTALL}/API_V2/Authentication.svc/json" if DOMAIN and INSTALL else ""


class TokenManager:
    def __init__(self):
        self.token_file = CONFIG_DIR / "tokens.json"
        self.tokens = self._load()

    def _load(self):
        if self.token_file.exists():
            with open(self.token_file) as f:
                return json.load(f)
        return {}

    def save(self, tokens):
        self.tokens = tokens
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_file, "w") as f:
            json.dump(tokens, f, indent=2)
        os.chmod(self.token_file, 0o600)

    @property
    def access_token(self):
        return self.tokens.get("AccessToken", "")

    @property
    def refresh_token(self):
        return self.tokens.get("RefreshToken", "")

    def is_expired(self):
        expires_at = self.tokens.get("expires_at", 0)
        return time.time() >= expires_at - 60

    def grant(self):
        resp = requests.post(f"{AUTH_URL}/GrantToken", json={
            "username": USERNAME,
            "password": PASSWORD,
        })
        if resp.status_code == 200:
            tokens = resp.json()
            # Rocketmatter tokens typically last 24h; store expires_at
            tokens["expires_at"] = time.time() + 86400
            tokens["fetched_at"] = datetime.now(timezone.utc).isoformat()
            self.save(tokens)
            return tokens
        raise RuntimeError(f"GrantToken failed ({resp.status_code}): {resp.text}")

    def refresh(self):
        if not self.refresh_token:
            return self.grant()
        resp = requests.post(f"{AUTH_URL}/RefreshToken", json={
            "RefreshToken": self.refresh_token,
        })
        if resp.status_code == 200:
            tokens = resp.json()
            tokens["expires_at"] = time.time() + 86400
            tokens["fetched_at"] = datetime.now(timezone.utc).isoformat()
            self.save(tokens)
            return tokens
        return self.grant()

    def get_valid_token(self):
        if not self.access_token or self.is_expired():
            self.refresh()
        return self.access_token


class RocketMatterClient:
    def __init__(self):
        self.tm = TokenManager()
        self.session = requests.Session()
        self._refresh_headers()

    def _refresh_headers(self):
        token = self.tm.get_valid_token()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _request(self, path, body=None):
        if self.tm.is_expired():
            self._refresh_headers()

        url = f"{BASE_URL}/{path.lstrip('/')}"
        resp = self.session.post(url, json=body or {})

        if resp.status_code == 401:
            self.tm.grant()
            self._refresh_headers()
            resp = self.session.post(url, json=body or {})

        if resp.status_code == 429:
            retry_after = int(resp.headers.get("Retry-After", 10))
            print(f"Rate limited. Waiting {retry_after}s...", file=sys.stderr)
            time.sleep(retry_after)
            resp = self.session.post(url, json=body or {})

        if not resp.ok:
            raise RuntimeError(f"Rocketmatter API error {resp.status_code}: {resp.text[:400]}")

        if not resp.content:
            return {"success": True}

        return resp.json()

    # ── Authentication ─────────────────────────────────────────────────────────

    def get_new_refresh_token(self):
        return self._request("Authentication.svc/json/GetNewRefreshToken")

    def logout(self):
        return self._request("Authentication.svc/json/LogOut")

    # ── Matters ────────────────────────────────────────────────────────────────

    def get_matter(self, matter_id: int):
        return self._request("Matters.svc/json/Get", {"ID": matter_id})

    def save_matter(self, **fields):
        return self._request("Matters.svc/json/Save", fields)

    def search_matters(self, search_term: str, page: int = 1, page_size: int = 50):
        return self._request("Matters.svc/json/GetMattersBySearch", {
            "SearchTerm": search_term,
            "Page": page,
            "PageSize": page_size,
        })

    def get_matter_billing_info(self, matter_id: int):
        return self._request("Matters.svc/json/GetMatterBillingInfo", {"ID": matter_id})

    def get_matter_budget_info(self, matter_id: int):
        return self._request("Matters.svc/json/GetMatterBudgetInfo", {"ID": matter_id})

    def get_matter_budget(self, matter_id: int):
        return self._request("Matters.svc/json/GetMatterBudget", {"MatterId": matter_id})

    def update_matter_budget(self, matter_id: int, **fields):
        body = {"MatterId": matter_id, **fields}
        return self._request("Matters.svc/json/UpdateMatterBudget", body)

    def update_matter_status(self, matter_id: int, status_id: int):
        return self._request("Matters.svc/json/UpdateMatterStatus", {
            "MatterId": matter_id,
            "StatusId": status_id,
        })

    def delete_matter(self, matter_id: int):
        return self._request("Matters.svc/json/DeleteMatter", {"ID": matter_id})

    def get_matter_details(self, matter_id: int):
        return self._request("Matters.svc/json/GetDetailsForMatter", {"ID": matter_id})

    def get_matter_by_client_matter(self, client_matter: str):
        return self._request("Matters.svc/json/GetMatterByClientMatter", {"ClientMatter": client_matter})

    def does_client_matter_exist(self, client_matter: str):
        return self._request("Matters.svc/json/DoesClientMatterExists", {"ClientMatter": client_matter})

    def get_matter_custom_fields(self, matter_id: int):
        return self._request("Matters.svc/json/GetMatterCustomFields", {"MatterId": matter_id})

    def save_matter_custom_fields(self, matter_id: int, custom_fields: list):
        return self._request("Matters.svc/json/SaveMatterCustomFields", {
            "MatterId": matter_id,
            "CustomFields": custom_fields,
        })

    def delete_matter_custom_field(self, field_id: int):
        return self._request("Matters.svc/json/DeleteMatterCustomField", {"ID": field_id})

    def get_matter_email_folders(self, matter_id: int):
        return self._request("Matters.svc/json/GetMatterEmailFolders", {"MatterId": matter_id})

    def get_effective_rates_for_matter(self, matter_id: int, date: str):
        return self._request("Matters.svc/json/GetEffectiveRatesForMatterFromDate", {
            "MatterId": matter_id,
            "Date": date,
        })

    def search_matter_custom_fields(self, search_term: str):
        return self._request("Matters.svc/json/SearchCustomFields", {"SearchTerm": search_term})

    def get_matter_shared_invoice_settings(self, matter_id: int):
        return self._request("Matters.svc/json/GetMatterSharedInvoiceSettings", {"MatterId": matter_id})

    # ── Matter Types ───────────────────────────────────────────────────────────

    def get_matter_types(self):
        return self._request("MatterTypes.svc/json/Get")

    # ── Clients (Contacts) ─────────────────────────────────────────────────────

    def get_all_clients(self):
        return self._request("Clients.svc/json/GetAllClients")

    def save_client(self, **fields):
        return self._request("Clients.svc/json/Save", fields)

    def search_clients(self, search_term: str):
        return self._request("Clients.svc/json/Search", {"SearchTerm": search_term})

    def get_client_by_code(self, code: str):
        return self._request("Clients.svc/json/GetClientByCode", {"Code": code})

    def get_clients_by_ids(self, ids: list):
        return self._request("Clients.svc/json/GetClientsByIds", {"Ids": ids})

    def get_matter_relationships_for_client(self, client_id: int):
        return self._request("Clients.svc/json/GetMatterReadOnlyRelationshipsForClient", {"ClientId": client_id})

    def get_countries(self):
        return self._request("Clients.svc/json/GetCountries")

    def create_client_from_string(self, client_string: str):
        return self._request("Clients.svc/json/CreateClientFromString", {"ClientString": client_string})

    # ── Contacts ───────────────────────────────────────────────────────────────

    def get_contact_by_id(self, contact_id: int):
        return self._request("Contacts.svc/json/GetContactByID", {"ContactId": contact_id})

    def save_contact(self, **fields):
        return self._request("Contacts.svc/json/Save", fields)

    def delete_contact(self, contact_id: int):
        return self._request("Contacts.svc/json/DeleteContact", {"ContactId": contact_id})

    def search_contacts(self, search_term: str):
        return self._request("Contacts.svc/json/SearchContacts", {"SearchTerm": search_term})

    def search_person_contacts(self, search_term: str):
        return self._request("Contacts.svc/json/SearchPersonContacts", {"SearchTerm": search_term})

    def get_person_contacts(self):
        return self._request("Contacts.svc/json/GetPersonContacts")

    def get_contact_data(self, contact_id: int):
        return self._request("Contacts.svc/json/GetContactData", {"ContactId": contact_id})

    def get_contact_custom_fields(self, contact_id: int):
        return self._request("Contacts.svc/json/GetContactCustomFields", {"ContactId": contact_id})

    def save_contact_custom_fields(self, contact_id: int, custom_fields: list):
        return self._request("Contacts.svc/json/SaveContactCustomFields", {
            "ContactId": contact_id,
            "CustomFields": custom_fields,
        })

    def delete_contact_custom_field(self, field_id: int):
        return self._request("Contacts.svc/json/DeleteContactCustomField", {"ID": field_id})

    def get_contacts(self, page: int = 1, page_size: int = 50):
        return self._request("Contacts.svc/json/GetContacts", {"Page": page, "PageSize": page_size})

    # ── Tasks ──────────────────────────────────────────────────────────────────

    def get_tasks_for_matter(self, matter_id: int):
        return self._request("Tasks.svc/json/GetTasksForMatter", {"MatterId": matter_id})

    def get_tasks_by_filter(self, **filters):
        return self._request("Tasks.svc/json/GetTasksByFilter", filters)

    def get_task_by_activity_id(self, activity_id: int):
        return self._request("Tasks.svc/json/GetTaskByActivityId", {"ActivityId": activity_id})

    def save_task(self, **fields):
        return self._request("Tasks.svc/json/Save", fields)

    def delete_task(self, task_id: int):
        return self._request("Tasks.svc/json/Delete", {"ID": task_id})

    def get_common_tags(self):
        return self._request("Tasks.svc/json/GetCommonTags")

    # ── Billable Activity ──────────────────────────────────────────────────────

    def get_billable_activities(self, matter_id: int):
        return self._request("BillableActivity.svc/json/GetBillableActivities", {"MatterId": matter_id})

    def save_billable_time(self, matter_id: int, user_id: int, total_seconds: int,
                           notes: str = "", activity_type_id: int = 0, date_and_time: str = ""):
        body = {
            "MatterId": matter_id,
            "UserId": user_id,
            "TotalSeconds": total_seconds,
        }
        if notes:
            body["Notes"] = notes
        if activity_type_id:
            body["ActivityTypeId"] = activity_type_id
        if date_and_time:
            body["DateAndTime"] = date_and_time
        return self._request("BillableActivity.svc/json/SaveBillableTime", body)

    def save_expense(self, matter_id: int, user_id: int, amount: float,
                     notes: str = "", activity_type_id: int = 0, date_and_time: str = ""):
        body = {
            "MatterId": matter_id,
            "UserId": user_id,
            "Amount": amount,
        }
        if notes:
            body["Notes"] = notes
        if activity_type_id:
            body["ActivityTypeId"] = activity_type_id
        if date_and_time:
            body["DateAndTime"] = date_and_time
        return self._request("BillableActivity.svc/json/SaveExpense", body)

    def get_time_expense(self, activity_id: int):
        return self._request("BillableActivity.svc/json/GetTimeExpense", {"ID": activity_id})

    def delete_activity(self, activity_id: int):
        return self._request("BillableActivity.svc/json/DeleteActivity", {"ID": activity_id})

    def get_activities_for_matter(self, matter_id: int):
        return self._request("BillableActivity.svc/json/GetActivitiesForMatter", {"MatterId": matter_id})

    def get_firm_balances(self):
        return self._request("BillableActivity.svc/json/GetFirmBalances")

    def get_activity_type_id(self, name: str):
        return self._request("BillableActivity.svc/json/GetActivityTypeId", {"Name": name})

    def get_all_ledes(self):
        return self._request("BillableActivity.svc/json/GetAllLedes")

    # ── Timer ──────────────────────────────────────────────────────────────────

    def start_timer(self, matter_id: int, user_id: int):
        return self._request("Timer.svc/json/Start", {"MatterId": matter_id, "UserId": user_id})

    def pause_timer(self, timer_id: int):
        return self._request("Timer.svc/json/Pause", {"ID": timer_id})

    def bill_timer(self, timer_id: int):
        return self._request("Timer.svc/json/Bill", {"ID": timer_id})

    def get_timer(self, timer_id: int):
        return self._request("Timer.svc/json/Get", {"ID": timer_id})

    def get_all_non_billed_timers(self, user_id: int):
        return self._request("Timer.svc/json/GetAllNonBilledForUser", {"UserId": user_id})

    def save_timer(self, **fields):
        return self._request("Timer.svc/json/Save", fields)

    def delete_timer(self, timer_id: int):
        return self._request("Timer.svc/json/Delete", {"ID": timer_id})

    # ── Invoices ───────────────────────────────────────────────────────────────

    def run_invoice(self, matter_id: int, **fields):
        body = {"MatterId": matter_id, **fields}
        return self._request("Invoices.svc/json/RunInvoice", body)

    def get_invoice_payments_for_matter(self, matter_id: int):
        return self._request("Invoices.svc/json/GetInvoicePaymentsForMatter", {"MatterId": matter_id})

    def record_payments_to_invoices(self, **fields):
        return self._request("Invoices.svc/json/RecordPaymentsToInvoices", fields)

    def delete_payment(self, payment_id: int):
        return self._request("Invoices.svc/json/DeletePayment", {"ID": payment_id})

    def get_payments_for_matter(self, matter_id: int):
        return self._request("Invoices.svc/json/GetPaymentsForMatter", {"MatterId": matter_id})

    def process_refund(self, **fields):
        return self._request("Invoices.svc/json/ProcessRefund", fields)

    def get_most_recent_invoice_by_client(self, client_id: int):
        return self._request("Invoices.svc/json/GetMostRecentInvoiceInfoByClient", {"ClientId": client_id})

    def save_invoice_template(self, **fields):
        return self._request("Invoices.svc/json/SaveInvoiceTemplate", fields)

    def get_available_invoice_templates(self):
        return self._request("Invoices.svc/json/getAvailableInvoiceTemplates")

    def delete_invoice_template(self, template_id: int):
        return self._request("Invoices.svc/json/deleteInvoiceTemplate", {"ID": template_id})

    def save_retainer_request(self, **fields):
        return self._request("Invoices.svc/json/SaveRetainerRequest", fields)

    def get_transaction_info(self, transaction_id: int):
        return self._request("Invoices.svc/json/GetTransactionInfo", {"ID": transaction_id})

    # ── Calendar ───────────────────────────────────────────────────────────────

    def get_upcoming_events_for_matter(self, matter_id: int):
        return self._request("CalendarEntries.svc/json/GetUpcomingEventsForMatter", {"MatterId": matter_id})

    def get_upcoming_events_for_user(self, user_id: int):
        return self._request("CalendarEntries.svc/json/GetUpcomingEventsForUser", {"UserId": user_id})

    def save_calendar_entry(self, **fields):
        return self._request("CalendarEntries.svc/json/SaveCalendarEntry", fields)

    def get_calendar_entry(self, entry_id: int):
        return self._request("CalendarEntries.svc/json/GetCalendarEntry", {"ID": entry_id})

    def delete_calendar_entry(self, entry_id: int):
        return self._request("CalendarEntries.svc/json/DeleteCalendarEntry", {"ID": entry_id})

    def get_calendar_entries_for_date_range(self, start_date: str, end_date: str, user_id: int = 0):
        body = {"StartDate": start_date, "EndDate": end_date}
        if user_id:
            body["UserId"] = user_id
        return self._request("CalendarEntries.svc/json/GetCalendarEntriesForDateRange", body)

    def check_contact_availability(self, contact_id: int, start_date: str, end_date: str):
        return self._request("CalendarEntries.svc/json/CheckContactAvailability", {
            "ContactId": contact_id,
            "StartDate": start_date,
            "EndDate": end_date,
        })

    # ── Documents ──────────────────────────────────────────────────────────────

    def get_documents_in_path(self, matter_id: int, path: str = ""):
        return self._request("Documents.svc/json/GetDocumentsInPath", {"MatterId": matter_id, "Path": path})

    def get_document(self, document_id: int):
        return self._request("Documents.svc/json/GetDocument", {"ID": document_id})

    def get_directories(self, matter_id: int):
        return self._request("Documents.svc/json/GetDirectories", {"MatterId": matter_id})

    def save_document(self, **fields):
        return self._request("Documents.svc/json/Save", fields)

    def delete_document(self, document_id: int):
        return self._request("Documents.svc/json/DeleteDocument", {"ID": document_id})

    def move_documents_to_folder(self, document_ids: list, folder_path: str, matter_id: int):
        return self._request("Documents.svc/json/MoveDocumentsToFolder", {
            "DocumentIds": document_ids,
            "FolderPath": folder_path,
            "MatterId": matter_id,
        })

    def rename_folder(self, matter_id: int, old_path: str, new_name: str):
        return self._request("Documents.svc/json/RenameFolder", {
            "MatterId": matter_id,
            "OldPath": old_path,
            "NewName": new_name,
        })

    def get_document_download_key(self, document_id: int):
        return self._request("Documents.svc/json/GetDownloadKey", {"DocumentId": document_id})

    def get_document_versions(self, document_id: int):
        return self._request("Documents.svc/json/GetDocumentVersions", {"DocumentId": document_id})

    def get_document_file_info(self, document_id: int):
        return self._request("Documents.svc/json/GetDocumentFileInfo", {"DocumentId": document_id})

    def get_document_upload_url(self, **fields):
        return self._request("Documents.svc/json/GetDocumentUploadUrl", fields)

    def delete_note(self, note_id: int):
        return self._request("Documents.svc/json/DeleteNote", {"ID": note_id})

    def get_invoiced_documents(self, matter_id: int):
        return self._request("Documents.svc/json/GetInvoicedDocuments", {"MatterId": matter_id})

    # ── Document Templates ─────────────────────────────────────────────────────

    def get_document_templates(self):
        return self._request("DocumentTemplates.svc/json/GetDocumentTemplates")

    def delete_document_template(self, template_id: int):
        return self._request("DocumentTemplates.svc/json/DeleteDocumentTemplate", {"ID": template_id})

    # ── Users ──────────────────────────────────────────────────────────────────

    def get_current_user(self):
        return self._request("Users.svc/json/GetCurrentUser")

    def get_user(self, user_id: int):
        return self._request("Users.svc/json/Get", {"ID": user_id})

    def search_users(self, search_term: str):
        return self._request("Users.svc/json/Search", {"SearchTerm": search_term})

    def get_active_users(self):
        return self._request("Users.svc/json/GetActiveUsers")

    def get_user_by_initials(self, initials: str):
        return self._request("Users.svc/json/GetByInitials", {"Initials": initials})

    def get_user_by_full_name(self, full_name: str):
        return self._request("Users.svc/json/GetByFullName", {"FullName": full_name})

    def set_user_preference(self, key: str, value: str):
        return self._request("Users.svc/json/SetUserPreference", {"Key": key, "Value": value})

    def get_user_preference(self, key: str):
        return self._request("Users.svc/json/GetUserPreference", {"Key": key})

    def get_effective_user_rates(self, user_id: int):
        return self._request("Users.svc/json/GetEffectiveUserRates", {"UserId": user_id})

    # ── Tags ───────────────────────────────────────────────────────────────────

    def search_tags(self, search_term: str):
        return self._request("Tags.svc/json/Search", {"SearchTerm": search_term})

    def add_tag(self, entity_id: int, entity_type: str, tag: str):
        return self._request("Tags.svc/json/AddTag", {
            "EntityId": entity_id,
            "EntityType": entity_type,
            "Tag": tag,
        })

    def remove_tag(self, entity_id: int, entity_type: str, tag: str):
        return self._request("Tags.svc/json/RemoveTag", {
            "EntityId": entity_id,
            "EntityType": entity_type,
            "Tag": tag,
        })

    # ── Trust ──────────────────────────────────────────────────────────────────

    def get_trust_details_for_matter(self, matter_id: int):
        return self._request("Trust.svc/json/TrustDetailsForMatter", {"MatterId": matter_id})

    # ── Rates ──────────────────────────────────────────────────────────────────

    def get_matter_custom_rates(self, matter_id: int):
        return self._request("Rates.svc/json/GetMatterCustomRates", {"MatterId": matter_id})

    def save_custom_rate_config(self, **fields):
        return self._request("Rates.svc/json/SaveCustomRateConfig", fields)

    def delete_matter_rates(self, matter_id: int):
        return self._request("Rates.svc/json/DeleteMatterRates", {"MatterId": matter_id})

    # ── Firm Roles ─────────────────────────────────────────────────────────────

    def get_firm_roles(self):
        return self._request("FirmRoles.svc/json/GetFirmRoles")

    def save_firm_role(self, **fields):
        return self._request("FirmRoles.svc/json/SaveFirmRole", fields)

    def delete_firm_role(self, role_id: int):
        return self._request("FirmRoles.svc/json/DeleteFirmRole", {"ID": role_id})

    # ── Tax / Discount / Surcharge / Interest Rates ────────────────────────────

    def get_all_tax_rates(self):
        return self._request("TaxRates.svc/json/GetAll")

    def save_tax_rate(self, **fields):
        return self._request("TaxRates.svc/json/Save", fields)

    def delete_tax_rate(self, rate_id: int):
        return self._request("TaxRates.svc/json/Delete", {"ID": rate_id})

    def get_all_discounts(self):
        return self._request("Discounts.svc/json/GetAll")

    def save_discount(self, **fields):
        return self._request("Discounts.svc/json/Save", fields)

    def get_all_interests(self):
        return self._request("Interests.svc/json/GetAll")

    def save_interest(self, **fields):
        return self._request("Interests.svc/json/Save", fields)

    def charge_interest_fees(self, matter_id: int):
        return self._request("Interests.svc/json/ChargeInterestFees", {"MatterId": matter_id})

    def get_all_surcharge_rates(self):
        return self._request("SurchargeRates.svc/json/GetAll")

    def save_surcharge_rate(self, **fields):
        return self._request("SurchargeRates.svc/json/Save", fields)

    def delete_surcharge_rate(self, rate_id: int):
        return self._request("SurchargeRates.svc/json/Delete", {"ID": rate_id})

    # ── Messages (Phone) ───────────────────────────────────────────────────────

    def save_phone_message(self, matter_id: int, contact_id: int, message: str, **fields):
        body = {"MatterId": matter_id, "ContactId": contact_id, "Message": message, **fields}
        return self._request("Messages.svc/json/SavePhoneMessage", body)

    def get_phone_message(self, message_id: int):
        return self._request("Messages.svc/json/GetPhoneMessage", {"ID": message_id})

    # ── Communicator (Internal Messaging) ──────────────────────────────────────

    def get_channels_i_belong_to(self):
        return self._request("Communicator.svc/json/GetChannelsIBelongTo")

    def send_direct_message(self, to_user_id: int, message: str):
        return self._request("Communicator.svc/json/SendDirectMessage", {
            "ToUserId": to_user_id,
            "Message": message,
        })

    def send_channel_message(self, channel_id: int, message: str):
        return self._request("Communicator.svc/json/SendChannelMessage", {
            "ChannelId": channel_id,
            "Message": message,
        })

    def get_direct_chat(self, user_id: int):
        return self._request("Communicator.svc/json/GetDirectChat", {"UserId": user_id})

    def get_channel_chat(self, channel_id: int):
        return self._request("Communicator.svc/json/GetChannelChat", {"ChannelId": channel_id})

    def get_unread_direct_messages(self):
        return self._request("Communicator.svc/json/GetUnreadDirectMessages")

    def get_unread_channel_messages(self):
        return self._request("Communicator.svc/json/GetUnreadChannelMessages")

    def save_channel(self, **fields):
        return self._request("Communicator.svc/json/SaveChannel", fields)

    def delete_channel(self, channel_id: int):
        return self._request("Communicator.svc/json/DeleteChannel", {"ChannelId": channel_id})

    # ── Workflow ───────────────────────────────────────────────────────────────

    def get_matter_current_workflow_status(self, matter_id: int):
        return self._request("WorkFlow.svc/json/GetMatterCurrentWorkFlowStatus", {"MatterId": matter_id})

    def get_matter_workflow_statuses(self, matter_id: int):
        return self._request("WorkFlow.svc/json/GetMatterWorkFLowStatuses", {"MatterId": matter_id})

    def apply_new_matter_workflow_status(self, matter_id: int, status_id: int):
        return self._request("WorkFlow.svc/json/ApplyNewMatterWorkFlowStatus", {
            "MatterId": matter_id,
            "StatusId": status_id,
        })

    def add_edit_workflow_status(self, **fields):
        return self._request("WorkFlow.svc/json/AddEditWorkflowStatus", fields)

    # ── Reports ────────────────────────────────────────────────────────────────

    def run_report(self, report_id: int, **fields):
        body = {"ReportId": report_id, **fields}
        return self._request("Reports.svc/json/RunReport", body)

    def get_report_summary(self):
        return self._request("Reports.svc/json/GetReportSummary")

    def get_report_metadata(self, report_id: int):
        return self._request("Reports.svc/json/GetReportMetaData", {"ReportId": report_id})

    # ── Search ─────────────────────────────────────────────────────────────────

    def global_search(self, search_term: str):
        return self._request("Search.svc/json/GlobalSearch", {"SearchTerm": search_term})

    def search_occurrence_for_type(self, search_term: str, entity_type: str):
        return self._request("Search.svc/json/SearchOccurenceForType", {
            "SearchTerm": search_term,
            "EntityType": entity_type,
        })

    # ── Recurring Billing ──────────────────────────────────────────────────────

    def get_matter_payment_plan(self, matter_id: int):
        return self._request("RecurringBilling.svc/json/getMatterPaymentPlan", {"MatterId": matter_id})

    def generate_payment_plan(self, **fields):
        return self._request("RecurringBilling.svc/json/GeneratePaymentPlan", fields)

    def commit_payment_plan(self, **fields):
        return self._request("RecurringBilling.svc/json/CommitPlan", fields)

    def cancel_payment_plan(self, plan_id: int):
        return self._request("RecurringBilling.svc/json/cancelPaymentPlan", {"PlanId": plan_id})

    # ── Matter Templates ───────────────────────────────────────────────────────

    def get_all_matter_templates(self):
        return self._request("MatterTemplates.svc/json/GetAll")

    def get_matter_template(self, template_id: int):
        return self._request("MatterTemplates.svc/json/Get", {"ID": template_id})

    def save_matter_template(self, **fields):
        return self._request("MatterTemplates.svc/json/Save", fields)

    def delete_matter_template(self, template_id: int):
        return self._request("MatterTemplates.svc/json/Delete", {"ID": template_id})

    def get_new_matter_from_template(self, template_id: int):
        return self._request("MatterTemplates.svc/json/GetNewMatterFromTemplate", {"ID": template_id})

    # ── Court Rules ────────────────────────────────────────────────────────────

    def get_matter_court_rules(self, matter_id: int):
        return self._request("CourtRules.svc/json/GetMatterCourtRules", {"MatterId": matter_id})

    def add_matter_court_rule(self, matter_id: int, court_rule_id: int):
        return self._request("CourtRules.svc/json/AddMatterCourtRule", {
            "MatterId": matter_id,
            "CourtRuleId": court_rule_id,
        })

    def delete_matter_court_rule(self, matter_court_rule_id: int):
        return self._request("CourtRules.svc/json/DeleteMatterCourtRule", {"ID": matter_court_rule_id})

    def get_available_court_rules(self):
        return self._request("CourtRules.svc/json/GetAvailableCourtRules")

    def calculate_deadlines(self, court_rule_id: int, trigger_date: str):
        return self._request("CourtRules.svc/json/CalculateDeadlines", {
            "CourtRuleId": court_rule_id,
            "TriggerDate": trigger_date,
        })

    # ── Features ───────────────────────────────────────────────────────────────

    def get_firm_features(self):
        return self._request("Features.svc/json/GetFirmFeatures")

    # ── Time Options ───────────────────────────────────────────────────────────

    def get_time_options(self):
        return self._request("TimeOptions.svc/json/GetAll")
