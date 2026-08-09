"""Offline protocol and fleet-canary regressions for MCP 2026-07-28."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import httpx
import pytest
import requests
from mcp import Client
from mcp.types import LATEST_PROTOCOL_VERSION
from mcp_types.version import MODERN_PROTOCOL_VERSIONS


# Keep the offline suite away from OS keyrings and any local credential fallback.
os.environ["ROCKETMATTER_MCP_USE_KEYRING"] = "0"
for credential_name in (
    "ROCKETMATTER_API_KEY",
    "ROCKETMATTER_CLIENT_ID",
    "ROCKETMATTER_CLIENT_SECRET",
):
    os.environ.setdefault(credential_name, "unused")

from rocketmatter_mcp import client as client_module  # noqa: E402
from rocketmatter_mcp import server  # noqa: E402
from rocketmatter_mcp.client import LCSClient  # noqa: E402
from rocketmatter_mcp.setup import oauth_flow, verify  # noqa: E402


PROTOCOL_VERSION = "2026-07-28"
LEGACY_PROTOCOL_VERSION = "2025-11-25"
PROTOCOL_VERSION_META_KEY = "io.modelcontextprotocol/protocolVersion"
CLIENT_CAPABILITIES_META_KEY = "io.modelcontextprotocol/clientCapabilities"
CLIENT_INFO_META_KEY = "io.modelcontextprotocol/clientInfo"
SERVER_INFO_META_KEY = "io.modelcontextprotocol/serverInfo"
REPO_ROOT = Path(__file__).resolve().parents[1]


def _modern_request(
    method: str,
    params: dict[str, Any] | None = None,
    *,
    protocol_version: str = PROTOCOL_VERSION,
    request_id: int = 1,
) -> tuple[dict[str, str], dict[str, Any]]:
    request_params = dict(params or {})
    request_params["_meta"] = {
        PROTOCOL_VERSION_META_KEY: protocol_version,
        CLIENT_CAPABILITIES_META_KEY: {},
        CLIENT_INFO_META_KEY: {"name": "rocketmatter-spec-test", "version": "0"},
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "mcp-protocol-version": protocol_version,
        "mcp-method": method,
    }
    if method == "tools/call":
        headers["mcp-name"] = str(request_params["name"])
    elif method == "prompts/get":
        headers["mcp-name"] = str(request_params["name"])
    elif method == "resources/read":
        headers["mcp-name"] = str(request_params["uri"])
    return headers, {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": request_params,
    }


async def _post_modern(
    method: str,
    params: dict[str, Any] | None = None,
    *,
    protocol_version: str = PROTOCOL_VERSION,
    header_overrides: dict[str, str] | None = None,
) -> httpx.Response:
    app = server.mcp.streamable_http_app(
        host="0.0.0.0",
        stateless_http=True,
        json_response=True,
    )
    headers, body = _modern_request(
        method,
        params,
        protocol_version=protocol_version,
    )
    if header_overrides:
        headers.update(header_overrides)
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://spec-test",
        ) as http_client:
            return await http_client.post("/mcp", headers=headers, json=body)


def _result(response: httpx.Response) -> dict[str, Any]:
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["jsonrpc"] == "2.0"
    return payload["result"]


def _response(status: int, payload: Any) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(payload).encode()
    response.headers["Content-Type"] = "application/json"
    return response


def test_spec_check_pins_the_2026_revision() -> None:
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "tests" / "spec_check.py"), "--mcp-only"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Spec check: PASS" in result.stdout
    assert LATEST_PROTOCOL_VERSION == PROTOCOL_VERSION
    assert MODERN_PROTOCOL_VERSIONS == (PROTOCOL_VERSION,)


def test_modern_discovery_is_sessionless_and_declares_used_capabilities() -> None:
    response = asyncio.run(_post_modern("server/discover"))
    result = _result(response)

    assert "mcp-session-id" not in response.headers
    assert result["supportedVersions"] == [PROTOCOL_VERSION]
    assert result["resultType"] == "complete"
    assert result["ttlMs"] == 0
    assert result["cacheScope"] == "private"
    assert result["capabilities"] == {
        "prompts": {"listChanged": True},
        "resources": {"listChanged": True, "subscribe": True},
        "tools": {"listChanged": True},
    }
    assert "extensions" not in result["capabilities"]
    assert result["_meta"][SERVER_INFO_META_KEY]["name"] == "rocketmatter"


def test_client_negotiates_modern_and_legacy_protocols() -> None:
    async def negotiate() -> tuple[str, str]:
        async with Client(server.mcp, cache=None) as modern:
            modern_version = modern.protocol_version
        async with Client(server.mcp, mode="legacy", cache=None) as legacy:
            legacy_version = legacy.protocol_version
        return modern_version, legacy_version

    modern_version, legacy_version = asyncio.run(negotiate())
    assert modern_version == PROTOCOL_VERSION
    assert legacy_version == LEGACY_PROTOCOL_VERSION


def test_cacheable_results_are_complete_private_and_deterministic() -> None:
    async def list_results() -> list[dict[str, Any]]:
        methods = (
            "tools/list",
            "tools/list",
            "prompts/list",
            "resources/list",
            "resources/templates/list",
        )
        return [_result(await _post_modern(method)) for method in methods]

    first_tools, second_tools, prompts, resources, templates = asyncio.run(
        list_results()
    )
    for result in (first_tools, second_tools, prompts, resources, templates):
        assert result["resultType"] == "complete"
        assert result["ttlMs"] == 0
        assert result["cacheScope"] == "private"

    first_names = [tool["name"] for tool in first_tools["tools"]]
    second_names = [tool["name"] for tool in second_tools["tools"]]
    assert first_names == second_names
    assert len(first_names) == 86
    assert all(tool["inputSchema"]["type"] == "object" for tool in first_tools["tools"])
    assert len(prompts["prompts"]) == 3
    assert [item["uri"] for item in resources["resources"]] == [
        "rocketmatter://users",
        "rocketmatter://clients",
        "rocketmatter://security-notes",
    ]
    assert templates["resourceTemplates"] == []


def test_paginated_tool_schemas_have_fleet_bounds() -> None:
    tools = _result(asyncio.run(_post_modern("tools/list")))["tools"]
    paginated = [
        tool for tool in tools if "page_size" in tool["inputSchema"]["properties"]
    ]

    assert len(paginated) == 15
    for tool in paginated:
        properties = tool["inputSchema"]["properties"]
        assert properties["page"] == {
            "default": 1,
            "description": "One-based vendor API page number.",
            "minimum": 1,
            "title": "Page",
            "type": "integer",
        }
        assert properties["page_size"] == {
            "default": 25,
            "description": (
                "Maximum number of records returned from the requested page."
            ),
            "maximum": 200,
            "minimum": 1,
            "title": "Page Size",
            "type": "integer",
        }


def test_invalid_page_size_is_rejected_before_client_construction(monkeypatch) -> None:
    monkeypatch.setattr(
        server,
        "_c",
        lambda: pytest.fail("validated tool input must not construct the API client"),
    )
    response = asyncio.run(
        _post_modern(
            "tools/call",
            {"name": "list_matters", "arguments": {"page_size": 201}},
        )
    )
    result = _result(response)
    assert result["isError"] is True
    assert result["resultType"] == "complete"
    assert "less than or equal to 200" in result["content"][0]["text"]


def test_resource_read_cache_hints_and_not_found_error(monkeypatch) -> None:
    class StubLCSClient:
        def list_users(self, page: int, page_size: int) -> dict[str, Any]:
            return {"items": [{"id": 7}], "page": page, "pageSize": page_size}

        def list_clients(self, page: int, page_size: int) -> dict[str, Any]:
            return {"items": [], "page": page, "pageSize": page_size}

    monkeypatch.setattr(server, "_c", StubLCSClient)
    found = asyncio.run(_post_modern("resources/read", {"uri": "rocketmatter://users"}))
    result = _result(found)
    assert result["resultType"] == "complete"
    assert result["ttlMs"] == 0
    assert result["cacheScope"] == "private"
    assert '"id": 7' in result["contents"][0]["text"]

    missing = asyncio.run(
        _post_modern("resources/read", {"uri": "rocketmatter://does-not-exist"})
    )
    assert missing.status_code == 400
    assert missing.json()["error"]["code"] == -32602


def test_modern_tool_errors_are_complete_and_pii_free(monkeypatch, caplog) -> None:
    pii_sentinel = "person-name-and-email@example.invalid"

    class StubLCSClient:
        def create_matter(self, **fields: Any) -> dict[str, Any]:
            raise AssertionError(f"malformed input reached client: {fields}")

    monkeypatch.setattr(server, "_c", StubLCSClient)
    caplog.set_level(logging.WARNING)
    response = asyncio.run(
        _post_modern(
            "tools/call",
            {
                "name": "create_matter",
                "arguments": {"fields_json": f"[{pii_sentinel}"},
            },
        )
    )
    result = _result(response)

    assert result["isError"] is True
    assert result["resultType"] == "complete"
    assert "Invalid fields_json: malformed JSON" in result["content"][0]["text"]
    assert pii_sentinel not in result["content"][0]["text"]
    assert "reason=fields_json_invalid_json" in caplog.text
    assert pii_sentinel not in caplog.text


def test_modern_http_enforces_routing_headers_versions_and_method_errors() -> None:
    mismatch = asyncio.run(
        _post_modern(
            "tools/list",
            header_overrides={"mcp-method": "resources/list"},
        )
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["error"]["code"] == -32020

    name_mismatch = asyncio.run(
        _post_modern(
            "tools/call",
            {"name": "list_matters", "arguments": {}},
            header_overrides={"mcp-name": "list_clients"},
        )
    )
    assert name_mismatch.status_code == 400
    assert name_mismatch.json()["error"]["code"] == -32020

    unsupported = asyncio.run(_post_modern("tools/list", protocol_version="2099-01-01"))
    assert unsupported.status_code == 400
    assert unsupported.json()["error"] == {
        "code": -32022,
        "message": "Unsupported protocol version",
        "data": {
            "supported": [PROTOCOL_VERSION],
            "requested": "2099-01-01",
        },
    }

    unknown = asyncio.run(_post_modern("example/unknown"))
    assert unknown.status_code == 404
    assert unknown.json()["error"] == {
        "code": -32601,
        "message": "Method not found",
        "data": "example/unknown",
    }


@pytest.mark.parametrize("bare_list", [False, True])
def test_list_page_size_is_a_true_cap_and_only_one_page_is_requested(
    bare_list: bool,
) -> None:
    api_client = object.__new__(LCSClient)
    items = [{"id": index} for index in range(4)]
    payload: Any = items if bare_list else {"items": items, "totalCount": 40}
    api_client._send = Mock(return_value=_response(200, payload))

    result = api_client._list(
        "documents" if bare_list else "matters", page=2, page_size=3
    )

    if bare_list:
        assert isinstance(result, list)
        returned_items = result
    else:
        assert isinstance(result, dict)
        returned_items = result["items"]
    assert returned_items == items[:3]
    api_client._send.assert_called_once_with(
        "GET",
        "documents" if bare_list else "matters",
        params={"page": 2, "pageSize": 3},
    )


@pytest.mark.parametrize(
    ("page", "page_size", "reason"),
    [
        (0, 25, "page_below_minimum"),
        (1, 0, "page_size_out_of_range"),
        (1, 201, "page_size_out_of_range"),
    ],
)
def test_direct_client_rejects_invalid_pagination_without_network(
    page: int,
    page_size: int,
    reason: str,
    caplog,
) -> None:
    api_client = object.__new__(LCSClient)
    api_client._send = Mock()
    caplog.set_level(logging.WARNING)

    with pytest.raises(ValueError):
        api_client._list("matters", page=page, page_size=page_size)

    api_client._send.assert_not_called()
    assert f"reason={reason}" in caplog.text


def test_rejection_logs_and_errors_do_not_expose_upstream_pii(caplog) -> None:
    pii_sentinel = "sub-email-name-token-secret@example.invalid"
    caplog.set_level(logging.WARNING)

    with pytest.raises(RuntimeError) as token_error:
        client_module._token_record({"detail": pii_sentinel})
    assert pii_sentinel not in str(token_error.value)

    with pytest.raises(RuntimeError) as api_error:
        LCSClient._json_or_raise(_response(403, {"message": pii_sentinel}))
    assert pii_sentinel not in str(api_error.value)

    api_client = object.__new__(LCSClient)
    with pytest.raises(RuntimeError):
        api_client.list_transactions()

    assert "reason=missing_access_token" in caplog.text
    assert "reason=http_error status=403" in caplog.text
    assert "reason=missing_transaction_scope" in caplog.text
    assert pii_sentinel not in caplog.text


def test_cli_success_output_does_not_emit_user_records(monkeypatch, capsys) -> None:
    pii_sentinel = "private-person@example.invalid"

    class StubVerifyClient:
        def list_users(self, page: int, page_size: int) -> dict[str, Any]:
            return {
                "totalCount": 1,
                "items": [{"name": pii_sentinel, "email": pii_sentinel}],
            }

    monkeypatch.setattr(verify, "LCSClient", StubVerifyClient)
    verify.main()
    assert pii_sentinel not in capsys.readouterr().out

    monkeypatch.setattr(oauth_flow, "_capture", lambda *args, **kwargs: "unused")
    monkeypatch.setattr(oauth_flow.credentials, "set_secret", lambda *args: "keyring")
    monkeypatch.setattr(
        oauth_flow.credentials, "storage_backend", lambda: "test-keyring"
    )
    monkeypatch.setattr(
        oauth_flow, "build_authorize_url", lambda *args: "https://example.invalid"
    )
    monkeypatch.setattr(
        oauth_flow,
        "exchange_code",
        lambda *args: {"firm_id": "42", "user_name": pii_sentinel},
    )
    monkeypatch.setenv("ROCKETMATTER_OAUTH_CODE", "unused")
    monkeypatch.setattr(sys, "argv", ["rocketmatter-mcp-setup"])
    oauth_flow.main()
    assert pii_sentinel not in capsys.readouterr().out
