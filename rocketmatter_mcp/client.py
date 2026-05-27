#!/usr/bin/env python3
"""Rocketmatter LCS Integration API client.

Auth:
  Authorization: ApiKey <ROCKETMATTER_API_KEY>     — all requests
  X-User-Token: <user access_token>                — NextGen-proxied endpoints
"""

import json
import os
import time
import requests
from pathlib import Path

BASE_URL = os.environ.get("ROCKETMATTER_BASE_URL", "https://app.rocketmatter.net")
API_KEY = os.environ.get("ROCKETMATTER_API_KEY", "")
USERNAME = os.environ.get("ROCKETMATTER_USERNAME", "")
PASSWORD = os.environ.get("ROCKETMATTER_PASSWORD", "")

CONFIG_DIR = Path.home() / ".rocketmatter-mcp"
TOKEN_FILE = CONFIG_DIR / "tokens.json"


def _load_tokens():
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return {}


def _save_tokens(tokens: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)


def _fetch_user_token(session: requests.Session) -> str:
    if not USERNAME or not PASSWORD:
        raise RuntimeError(
            "ROCKETMATTER_USERNAME and ROCKETMATTER_PASSWORD must be set. "
            "Run: rocketmatter-mcp-setup"
        )
    resp = session.post(
        f"{BASE_URL}/v1/lookups/user-token",
        json={
            "username": USERNAME,
            "password": PASSWORD,
        },
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"User token request failed ({resp.status_code}): {resp.text[:200]}"
        )
    data = resp.json()
    token = data.get("access_token", "")
    if not token:
        raise RuntimeError(f"No access_token in response: {data}")
    tokens = {
        "access_token": token,
        "expires_at": time.time() + data.get("expires_in", 17999),
    }
    _save_tokens(tokens)
    return token


class LCSClient:
    def __init__(self):
        if not API_KEY:
            raise RuntimeError(
                "ROCKETMATTER_API_KEY must be set. Run: rocketmatter-mcp-setup"
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"ApiKey {API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )
        self._user_token = self._get_user_token()

    def _get_user_token(self) -> str:
        tokens = _load_tokens()
        if (
            tokens.get("access_token")
            and time.time() < tokens.get("expires_at", 0) - 60
        ):
            return tokens["access_token"]
        return _fetch_user_token(self.session)

    def _user_headers(self) -> dict:
        return {"X-User-Token": self._user_token}

    def _handle(self, resp: requests.Response) -> dict:
        if resp.status_code == 401:
            self._user_token = _fetch_user_token(self.session)
            return None  # caller retries
        if not resp.ok:
            raise RuntimeError(f"API error {resp.status_code}: {resp.text[:400]}")
        if not resp.content:
            return {"success": True}
        return resp.json()

    def _get(self, path: str, params: dict = None, user_token: bool = True) -> dict:
        headers = self._user_headers() if user_token else {}
        resp = self.session.get(f"{BASE_URL}{path}", params=params, headers=headers)
        result = self._handle(resp)
        if result is None:
            resp = self.session.get(
                f"{BASE_URL}{path}",
                params=params,
                headers=self._user_headers() if user_token else {},
            )
            return self._handle(resp)
        return result

    def _post(self, path: str, body: dict = None, user_token: bool = True) -> dict:
        headers = self._user_headers() if user_token else {}
        resp = self.session.post(f"{BASE_URL}{path}", json=body or {}, headers=headers)
        result = self._handle(resp)
        if result is None:
            resp = self.session.post(
                f"{BASE_URL}{path}",
                json=body or {},
                headers=self._user_headers() if user_token else {},
            )
            return self._handle(resp)
        return result

    def _put(self, path: str, body: dict = None, user_token: bool = True) -> dict:
        headers = self._user_headers() if user_token else {}
        resp = self.session.put(f"{BASE_URL}{path}", json=body or {}, headers=headers)
        result = self._handle(resp)
        if result is None:
            resp = self.session.put(
                f"{BASE_URL}{path}",
                json=body or {},
                headers=self._user_headers() if user_token else {},
            )
            return self._handle(resp)
        return result

    def _patch(self, path: str, body: dict = None, user_token: bool = True) -> dict:
        headers = self._user_headers() if user_token else {}
        resp = self.session.patch(f"{BASE_URL}{path}", json=body or {}, headers=headers)
        result = self._handle(resp)
        if result is None:
            resp = self.session.patch(
                f"{BASE_URL}{path}",
                json=body or {},
                headers=self._user_headers() if user_token else {},
            )
            return self._handle(resp)
        return result

    def _delete(self, path: str, params: dict = None, user_token: bool = True) -> dict:
        headers = self._user_headers() if user_token else {}
        resp = self.session.delete(f"{BASE_URL}{path}", params=params, headers=headers)
        result = self._handle(resp)
        if result is None:
            resp = self.session.delete(
                f"{BASE_URL}{path}",
                params=params,
                headers=self._user_headers() if user_token else {},
            )
            return self._handle(resp)
        return result

    # ── Matters ────────────────────────────────────────────────────────────────

    def list_matters(
        self,
        page: int = 1,
        page_size: int = 25,
        active_only: bool = None,
        search_text: str = None,
        matter_owner_id: int = None,
    ) -> dict:
        params = {"page": page, "pageSize": page_size}
        if active_only is not None:
            params["activeOnly"] = active_only
        if search_text:
            params["SearchText"] = search_text
        if matter_owner_id:
            params["MatterOwnerId"] = matter_owner_id
        return self._get("/v1/matters", params=params)

    def get_matter(self, matter_id: int) -> dict:
        return self._get(f"/v1/matters/{matter_id}")

    def create_matter(self, **fields) -> dict:
        return self._post("/v1/matters", body=fields)

    def update_matter(self, matter_id: int, **fields) -> dict:
        return self._put(f"/v1/matters/{matter_id}", body=fields)

    def delete_matter(self, matter_id: int) -> dict:
        return self._delete(f"/v1/matters/{matter_id}")

    # ── Clients ────────────────────────────────────────────────────────────────

    def list_clients(
        self,
        page: int = 1,
        page_size: int = 25,
        active_only: bool = None,
        display_name: str = None,
        name: str = None,
    ) -> dict:
        params = {"page": page, "pageSize": page_size}
        if active_only is not None:
            params["activeOnly"] = active_only
        if display_name:
            params["DisplayName"] = display_name
        if name:
            params["Name"] = name
        return self._get("/v1/clients", params=params)

    def get_client(self, client_id: int) -> dict:
        return self._get(f"/v1/clients/{client_id}")

    def create_client(self, **fields) -> dict:
        return self._post("/v1/clients", body=fields)

    def update_client(self, client_id: int, **fields) -> dict:
        return self._put(f"/v1/clients/{client_id}", body=fields)

    def delete_client(self, client_id: int) -> dict:
        return self._delete(f"/v1/clients/{client_id}")

    # ── Contacts ───────────────────────────────────────────────────────────────

    def list_contacts(self, page: int = 1, page_size: int = 25) -> dict:
        return self._get("/v1/contacts", params={"page": page, "pageSize": page_size})

    def get_contact(self, contact_id: int) -> dict:
        return self._get(f"/v1/contacts/{contact_id}")

    def create_contact(self, **fields) -> dict:
        return self._post("/v1/contacts", body=fields)

    def update_contact(self, contact_id: int, **fields) -> dict:
        return self._put(f"/v1/contacts/{contact_id}", body=fields)

    def delete_contact(self, contact_id: int) -> dict:
        return self._delete(f"/v1/contacts/{contact_id}")

    # ── Time Entries ───────────────────────────────────────────────────────────

    def list_time_entries(
        self,
        matter_id: int = None,
        rate_type: str = None,
        billing_status: str = None,
        card_status: str = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict:
        params = {"page": page, "pageSize": page_size}
        if matter_id:
            params["MatterId"] = matter_id
        if rate_type:
            params["RateType"] = rate_type
        if billing_status:
            params["BillingStatus"] = billing_status
        if card_status:
            params["CardStatus"] = card_status
        return self._get("/v1/time-entries", params=params)

    def get_time_entry(self, time_entry_id: int) -> dict:
        return self._get(f"/v1/time-entries/{time_entry_id}")

    def create_time_entry(self, **fields) -> dict:
        return self._post("/v1/time-entries", body=fields)

    def update_time_entry(self, time_entry_id: int, **fields) -> dict:
        return self._put(f"/v1/time-entries/{time_entry_id}", body=fields)

    def delete_time_entry(self, time_entry_id: int) -> dict:
        return self._delete(f"/v1/time-entries/{time_entry_id}")

    # ── Expenses ───────────────────────────────────────────────────────────────

    def list_expenses(
        self,
        billing_type_id: int = None,
        billing_status_id: int = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict:
        params = {"page": page, "pageSize": page_size}
        if billing_type_id:
            params["BillingTypeId"] = billing_type_id
        if billing_status_id:
            params["BillingStatusId"] = billing_status_id
        return self._get("/v1/expense", params=params)

    def get_expense(self, expense_id: int) -> dict:
        return self._get(f"/v1/expense/{expense_id}")

    def create_expense(self, **fields) -> dict:
        return self._post("/v1/expense", body=fields)

    def update_expense(self, expense_id: int, **fields) -> dict:
        return self._put(f"/v1/expense/{expense_id}", body=fields)

    def delete_expense(self, expense_id: int) -> dict:
        return self._delete(f"/v1/expense/{expense_id}")

    # ── Invoices ───────────────────────────────────────────────────────────────

    def list_invoices(self, page: int = 1, page_size: int = 25) -> dict:
        return self._get("/v1/invoices", params={"page": page, "pageSize": page_size})

    def get_invoice(self, invoice_id: int) -> dict:
        return self._get(f"/v1/invoices/{invoice_id}")

    def create_invoice(self, **fields) -> dict:
        return self._post("/v1/invoices", body=fields)

    def update_invoice(self, invoice_id: int, **fields) -> dict:
        return self._patch(f"/v1/invoices/{invoice_id}", body=fields)

    def delete_invoice(self, invoice_id: int) -> dict:
        return self._delete(f"/v1/invoices/{invoice_id}")

    def approve_invoice(self, invoice_id: int, invoice_number: str) -> dict:
        return self._post(
            f"/v1/invoices/{invoice_id}/approve", body={"invoiceNumber": invoice_number}
        )

    # ── Payments ───────────────────────────────────────────────────────────────

    def list_payments(self, page: int = 1, page_size: int = 25) -> dict:
        return self._get("/v1/payments", params={"page": page, "pageSize": page_size})

    def create_payment(self, **fields) -> dict:
        return self._post("/v1/payments", body=fields)

    def get_invoice_allocations(self, **params) -> dict:
        return self._get("/v1/payments/invoice-allocations", params=params)

    # ── Transactions ───────────────────────────────────────────────────────────

    def list_transactions(self, page: int = 1, page_size: int = 25) -> dict:
        return self._get(
            "/v1/transactions", params={"page": page, "pageSize": page_size}
        )

    def get_transaction(self, transaction_id: int) -> dict:
        return self._get(f"/v1/transactions/{transaction_id}")

    def create_transaction(self, **fields) -> dict:
        return self._post("/v1/transactions", body=fields)

    def update_transaction(self, transaction_id: int, **fields) -> dict:
        return self._put(f"/v1/transactions/{transaction_id}", body=fields)

    def delete_transaction(self, transaction_id: int) -> dict:
        return self._delete(f"/v1/transactions/{transaction_id}")

    # ── Documents ──────────────────────────────────────────────────────────────

    def list_documents(
        self, matter_id: int = None, path: str = None, doc_id: str = None
    ) -> dict:
        params = {}
        if matter_id:
            params["matterId"] = matter_id
        if path:
            params["path"] = path
        if doc_id:
            params["id"] = doc_id
        return self._get("/v1/documents", params=params)

    def get_document_default_app(self) -> dict:
        return self._get("/v1/documents/defaultApplication")

    def get_document_download_url(self, **fields) -> dict:
        return self._post("/v1/documents/download-url", body=fields)

    def get_document_upload_url(self, **fields) -> dict:
        return self._post("/v1/documents/upload-url", body=fields)

    def delete_document(self, path: str, doc_id: str) -> dict:
        return self._delete("/v1/documents/delete", params={"path": path, "id": doc_id})

    # ── Users / Timekeepers ────────────────────────────────────────────────────

    def list_users(self, page: int = 1, page_size: int = 25) -> dict:
        return self._get("/v1/users", params={"page": page, "pageSize": page_size})

    def get_user(self, user_id: int) -> dict:
        return self._get(f"/v1/users/{user_id}")

    # ── Text Shortcuts ─────────────────────────────────────────────────────────

    def list_text_shortcuts(self, page: int = 1, page_size: int = 25) -> dict:
        return self._get(
            "/v1/text-shortcuts", params={"page": page, "pageSize": page_size}
        )

    def get_text_shortcut(self, shortcut_id: int) -> dict:
        return self._get(f"/v1/text-shortcuts/{shortcut_id}")

    # ── Codes ──────────────────────────────────────────────────────────────────

    def get_codes(self, matter_id: int) -> dict:
        return self._get("/v1/codes", params={"matterId": matter_id}, user_token=False)

    def get_task_codes(self, matter_id: int) -> dict:
        return self._get(
            "/v1/codes/tasks", params={"matterId": matter_id}, user_token=False
        )

    def get_activity_codes(self, matter_id: int) -> dict:
        return self._get(
            "/v1/codes/activities", params={"matterId": matter_id}, user_token=False
        )

    # ── Lookups ────────────────────────────────────────────────────────────────

    def get_new_matter_defaults(self) -> dict:
        return self._get("/v1/lookups/new-matter/definition/defaults")

    def get_new_matter_definition(self, matter_id: int = None) -> dict:
        if matter_id:
            return self._get(f"/v1/lookups/new-matter/definition/{matter_id}")
        return self._get("/v1/lookups/new-matter/definition")

    def get_ebilling_defaults(self) -> dict:
        return self._get("/v1/lookups/new-matter/ebilling-settings/defaults")

    def get_matter_type_workflow(self, matter_type_id: int) -> dict:
        return self._get(f"/v1/lookups/matter-types/{matter_type_id}/workflow")

    def get_client_labels(self) -> dict:
        return self._get("/v1/lookups/client-labels")

    def get_matter_labels(self) -> dict:
        return self._get("/v1/lookups/matter-labels")

    def get_client_suggestions(self, search: str = None) -> dict:
        params = {}
        if search:
            params["search"] = search
        return self._get("/v1/lookups/clients", params=params)

    def get_new_contact_defaults(self) -> dict:
        return self._get("/v1/lookups/api/gui/form/newContact")

    def get_expense_lookups(self) -> dict:
        return self._get("/v1/lookups/expense")

    def get_new_expense_lookups(self, matter_id: int = None) -> dict:
        if matter_id:
            return self._get(
                "/v1/lookups/expense/new-expense-info", params={"matterId": matter_id}
            )
        return self._get("/v1/lookups/expense/new-expense")

    def get_invoice_lookups(self) -> dict:
        return self._get("/v1/lookups/invoice")

    def get_new_invoice_lookups(self, matter_id: int = None) -> dict:
        if matter_id:
            return self._get(
                "/v1/lookups/invoice/new-invoice-info", params={"matterId": matter_id}
            )
        return self._get("/v1/lookups/invoice/new-invoice")

    def get_invoice_payment_lookups(self) -> dict:
        return self._get("/v1/lookups/invoice-payments")

    def get_time_entry_lookups(self, matter_id: int = None) -> dict:
        params = {}
        if matter_id:
            params["matterId"] = matter_id
        return self._get("/v1/lookups/time-entries/new-time", params=params)

    def get_time_grid_lookups(self) -> dict:
        return self._get("/v1/lookups/time-entries/new-timesheet-from-grid")

    def get_transaction_lookups(self) -> dict:
        return self._get("/v1/lookups/transactions/newTransaction")

    def get_hard_cost_expense_lookups(self, matter_id: int = None) -> dict:
        params = {}
        if matter_id:
            params["matterId"] = matter_id
        return self._get("/v1/lookups/transactions/newHardCostExpense", params=params)

    # ── Accounts Payable ───────────────────────────────────────────────────────

    def list_ap_bills(self, page: int = 1, page_size: int = 25) -> dict:
        return self._get(
            "/v1/accounts-payable/bills",
            params={"page": page, "pageSize": page_size},
            user_token=False,
        )

    def get_ap_bill(self, bill_id: int) -> dict:
        return self._get(f"/v1/accounts-payable/bills/{bill_id}", user_token=False)

    def create_ap_bill(self, **fields) -> dict:
        return self._post("/v1/accounts-payable/bills", body=fields, user_token=False)

    def update_ap_bill(self, bill_id: int, **fields) -> dict:
        return self._put(
            f"/v1/accounts-payable/bills/{bill_id}", body=fields, user_token=False
        )

    def delete_ap_bill(self, bill_id: int) -> dict:
        return self._delete(f"/v1/accounts-payable/bills/{bill_id}", user_token=False)

    def list_ap_payments(self, page: int = 1, page_size: int = 25) -> dict:
        return self._get(
            "/v1/accounts-payable/payments",
            params={"page": page, "pageSize": page_size},
            user_token=False,
        )

    def create_ap_payment(self, **fields) -> dict:
        return self._post(
            "/v1/accounts-payable/payments", body=fields, user_token=False
        )

    def get_ap_payment_status(self, **params) -> dict:
        return self._get(
            "/v1/accounts-payable/payments/status", params=params, user_token=False
        )

    def list_ap_vendors(self, page: int = 1, page_size: int = 25) -> dict:
        return self._get(
            "/v1/accounts-payable/vendors",
            params={"page": page, "pageSize": page_size},
            user_token=False,
        )

    def get_ap_vendor(self, vendor_id: int) -> dict:
        return self._get(f"/v1/accounts-payable/vendors/{vendor_id}", user_token=False)

    def create_ap_vendor(self, **fields) -> dict:
        return self._post("/v1/accounts-payable/vendors", body=fields, user_token=False)

    def update_ap_vendor(self, vendor_id: int, **fields) -> dict:
        return self._put(
            f"/v1/accounts-payable/vendors/{vendor_id}", body=fields, user_token=False
        )
