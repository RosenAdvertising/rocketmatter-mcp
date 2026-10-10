"""Offline checks of the CLI's stateless Streamable HTTP application."""

from __future__ import annotations

import asyncio
import json
import time
from contextlib import asynccontextmanager
from importlib.metadata import version
from unittest.mock import Mock

import httpx
import pytest
import requests
from mcp import ClientSession
from mcp.client._memory import InMemoryTransport

from rocketmatter_mcp import client as client_module
from rocketmatter_mcp import server

PROTOCOL_VERSION = "2026-07-28"
SERVER_INFO_KEY = "io.modelcontextprotocol/serverInfo"


@pytest.fixture(autouse=True)
def isolated_configuration(monkeypatch):
    for name in (
        "ROCKETMATTER_MCP_TRANSPORT",
        "ROCKETMATTER_MCP_HOST",
        "ROCKETMATTER_MCP_ALLOWED_HOSTS",
        "ROCKETMATTER_MCP_ALLOWED_ORIGINS",
        "PORT",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("ROCKETMATTER_MCP_USE_KEYRING", "0")
    for name in (
        "ROCKETMATTER_API_KEY",
        "ROCKETMATTER_CLIENT_ID",
        "ROCKETMATTER_CLIENT_SECRET",
    ):
        monkeypatch.setenv(name, "from-process-environment")


def _request(method, params=None, *, request_id=1):
    body = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": method,
        "params": {
            **(params or {}),
            "_meta": {
                "io.modelcontextprotocol/protocolVersion": PROTOCOL_VERSION,
                "io.modelcontextprotocol/clientCapabilities": {},
                "io.modelcontextprotocol/clientInfo": {
                    "name": "rocketmatter-http-test",
                    "version": "0",
                },
            },
        },
    }
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
        "mcp-protocol-version": PROTOCOL_VERSION,
        "mcp-method": method,
    }
    if method == "tools/call":
        headers["mcp-name"] = params["name"]
    return headers, body


async def _post(client, method, params=None, *, request_id=1, **extra_headers):
    headers, body = _request(method, params, request_id=request_id)
    return await client.post("/mcp", headers={**headers, **extra_headers}, json=body)


def _result(response):
    assert response.status_code == 200, response.text
    assert "mcp-session-id" not in response.headers
    if response.headers["content-type"].startswith("text/event-stream"):
        messages = [
            json.loads(line[5:].strip())
            for line in response.text.splitlines()
            if line.startswith("data:")
        ]
        payload = next(message for message in messages if "id" in message)
    else:
        payload = response.json()
    return payload["result"]


@asynccontextmanager
async def _http_client():
    app = server.create_serve_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1:8080",
        ) as client:
            yield client


def test_http_catalog_matches_stdio_server():
    async def catalogs():
        async with InMemoryTransport(server.mcp) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                stdio_tools = (await session.list_tools()).tools
        async with _http_client() as client:
            http_tools = _result(await _post(client, "tools/list"))["tools"]
        return stdio_tools, http_tools

    stdio_tools, http_tools = asyncio.run(catalogs())
    assert len(http_tools) == 86
    assert [(tool["name"], tool["inputSchema"]) for tool in http_tools] == [
        (tool.name, tool.input_schema) for tool in stdio_tools
    ]


def test_http_read_uses_existing_vendor_client_and_environment(monkeypatch):
    payload = {"items": [{"id": "example-matter", "name": "Example"}], "page": 2}
    response = requests.Response()
    response.status_code = 200
    response._content = json.dumps(payload).encode()
    vendor_request = Mock(return_value=response)
    monkeypatch.setattr(client_module.requests.Session, "request", vendor_request)
    monkeypatch.setattr(
        client_module,
        "_load_tokens",
        lambda: {"access_token": "fake-cached-token", "expires_at": time.time() + 3600},
    )

    async def invoke():
        async with _http_client() as client:
            return _result(
                await _post(
                    client,
                    "tools/call",
                    {"name": "list_matters", "arguments": {"page": 2, "page_size": 1}},
                    **{
                        "ROCKETMATTER_API_KEY": "from-request",
                        "X-Api-Key": "from-request",
                        "X-User-Token": "from-request",
                    },
                )
            )

    result = asyncio.run(invoke())
    assert result["isError"] is False
    assert result["content"][0]["text"] == server.list_matters(page=2, page_size=1)
    assert json.loads(result["content"][0]["text"]) == payload
    assert vendor_request.call_count == 2
    for call in vendor_request.call_args_list:
        assert call.args == ("GET", f"{client_module.API_BASE}/v1/matters")
        assert call.kwargs["params"] == {"page": 2, "pageSize": 1}
        assert call.kwargs["headers"] == {
            "X-Api-Key": "from-process-environment",
            "X-User-Token": "fake-cached-token",
        }


def test_concurrent_requests_have_fresh_connection_state_and_one_lifespan(monkeypatch):
    events = []
    connections = []
    original_call = server.mcp.call_tool

    @asynccontextmanager
    async def lifespan(_server):
        events.append("start")
        yield {"shared": "app-lifespan"}
        events.append("stop")

    async def observe(name, arguments, context=None):
        connection = context.request_context.session._connection
        assert connection.state == {}
        connection.state["private"] = arguments["page"]
        connections.append(connection)
        assert context.request_context.lifespan_context == {"shared": "app-lifespan"}
        return await original_call(name, arguments, context)

    class VendorMock:
        def list_matters(self, **kwargs):
            return {"page": kwargs["page"]}

    monkeypatch.setattr(server.mcp._lowlevel_server, "lifespan", lifespan)
    monkeypatch.setattr(server.mcp, "call_tool", observe)
    monkeypatch.setattr(server, "_c", VendorMock)

    async def invoke():
        async with _http_client() as client:
            assert events == ["start"]
            results = await asyncio.gather(
                *(
                    _post(
                        client,
                        "tools/call",
                        {"name": "list_matters", "arguments": {"page": page}},
                        **{"mcp-session-id": "same-client-supplied-id"},
                    )
                    for page in (1, 2)
                )
            )
            assert events == ["start"]
            return results

    results = asyncio.run(invoke())
    assert [
        json.loads(_result(result)["content"][0]["text"]) for result in results
    ] == [
        {"page": 1},
        {"page": 2},
    ]
    assert connections[0] is not connections[1]
    assert events == ["start", "stop"]


def test_default_transport_keeps_stdio_run(monkeypatch):
    run = Mock()
    monkeypatch.setattr(server.mcp, "run", run)
    assert server._requested_transport() == "stdio"
    server.main()
    run.assert_called_once_with()


@pytest.mark.parametrize("value", ["stdio", " STDIO ", " "])
def test_transport_normalization(value, monkeypatch):
    monkeypatch.setenv("ROCKETMATTER_MCP_TRANSPORT", value)
    assert server._requested_transport() == "stdio"


def test_unknown_transport_exits(monkeypatch):
    monkeypatch.setenv("ROCKETMATTER_MCP_TRANSPORT", "bogus")
    with pytest.raises(
        SystemExit, match="ROCKETMATTER_MCP_TRANSPORT.*stdio.*streamable-http"
    ):
        server.main()


def test_http_dispatch_runs_uvicorn_with_sse_default(monkeypatch):
    import uvicorn

    configs = []

    class UvicornMock:
        def __init__(self, config):
            configs.append(config)

        async def serve(self):
            pass

    monkeypatch.setattr(uvicorn, "Server", UvicornMock)
    monkeypatch.setenv("ROCKETMATTER_MCP_TRANSPORT", " STREAMABLE-HTTP ")
    monkeypatch.setenv("PORT", " 8123 ")
    server.main()
    config = configs[0]
    assert config.host == "127.0.0.1"
    assert config.port == 8123
    assert config.access_log is False
    manager = server.mcp._lowlevel_server._session_manager
    assert manager.stateless is True
    assert manager.json_response is False


def test_port_default_and_invalid_value(monkeypatch):
    assert server._port() == 8080
    monkeypatch.setenv("PORT", "not-a-number")
    with pytest.raises(SystemExit, match="PORT must be an integer"):
        server._port()


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_loopback_keeps_sdk_protection(host, monkeypatch):
    monkeypatch.setenv("ROCKETMATTER_MCP_HOST", host)
    assert server._transport_security() is None
    server.create_serve_app()
    settings = server.mcp._lowlevel_server._session_manager.security_settings
    assert settings.enable_dns_rebinding_protection is True
    assert settings.allowed_origins


@pytest.mark.parametrize("allowed_hosts", [None, "", " , "])
def test_non_loopback_requires_allowed_hosts(allowed_hosts, monkeypatch):
    monkeypatch.setenv("ROCKETMATTER_MCP_HOST", "0.0.0.0")
    if allowed_hosts is not None:
        monkeypatch.setenv("ROCKETMATTER_MCP_ALLOWED_HOSTS", allowed_hosts)
    with pytest.raises(SystemExit, match="ROCKETMATTER_MCP_ALLOWED_HOSTS"):
        server.create_serve_app()


def test_http_rejects_disallowed_host_and_origin(monkeypatch):
    monkeypatch.setenv("ROCKETMATTER_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv(
        "ROCKETMATTER_MCP_ALLOWED_HOSTS", " 127.0.0.1:8080 , mcp.example:*"
    )
    monkeypatch.setenv("ROCKETMATTER_MCP_ALLOWED_ORIGINS", " https://client.example , ")

    async def invoke():
        async with _http_client() as client:
            bad_host = await _post(client, "tools/list", host="evil.example")
            bad_origin = await _post(
                client, "tools/list", origin="https://evil.example"
            )
            good = await _post(client, "tools/list", origin="https://client.example")
            return bad_host, bad_origin, good

    bad_host, bad_origin, good = asyncio.run(invoke())
    assert bad_host.status_code == 421
    assert bad_origin.status_code == 403
    assert len(_result(good)["tools"]) == 86


def test_non_loopback_without_origin_allowlist_rejects_any_origin(monkeypatch):
    monkeypatch.setenv("ROCKETMATTER_MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("ROCKETMATTER_MCP_ALLOWED_HOSTS", "127.0.0.1:8080")

    async def invoke():
        async with _http_client() as client:
            return await _post(client, "tools/list", origin="https://client.example")

    assert asyncio.run(invoke()).status_code == 403


def test_loopback_rejects_bad_host_and_origin():
    async def invoke():
        async with _http_client() as client:
            return (
                await _post(client, "tools/list", host="evil.example"),
                await _post(client, "tools/list", origin="https://evil.example"),
            )

    bad_host, bad_origin = asyncio.run(invoke())
    assert bad_host.status_code == 421
    assert bad_origin.status_code == 403


def test_get_delete_are_405_and_discovery_has_identity():
    async def invoke():
        async with _http_client() as client:
            headers, _ = _request("server/discover")
            for method in ("GET", "DELETE"):
                response = await client.request(method, "/mcp", headers=headers)
                assert response.status_code == 405
                assert "mcp-session-id" not in response.headers
            return _result(await _post(client, "server/discover"))

    discovery = asyncio.run(invoke())
    assert PROTOCOL_VERSION in discovery["supportedVersions"]
    identity = discovery["_meta"][SERVER_INFO_KEY]
    assert identity["name"] == "rocketmatter"
    assert identity["title"]
    assert identity["version"] == version("rocketmatter-mcp")


def test_tool_boundary_propagates_cancellation(monkeypatch):
    tool = server.mcp._tool_manager.get_tool("list_matters")

    async def cancelled(*args, **kwargs):
        raise asyncio.CancelledError

    monkeypatch.setattr(type(tool), "run", cancelled)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(server.mcp.call_tool("list_matters", {}))
