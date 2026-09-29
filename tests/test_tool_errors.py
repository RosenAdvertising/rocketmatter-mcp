"""Safe error text regressions through the official in-memory MCP client."""

from __future__ import annotations

import asyncio
import logging
import json

from mcp.client import ClientSession
from mcp.client._memory import InMemoryTransport
from mcp.types import TextContent
import requests
import pytest

from rocketmatter_mcp import server
from rocketmatter_mcp.errors import (
    ArgumentValidationError,
    AuthenticationError,
    MissingCredentialsError,
    NotFoundError,
    VendorHTTPError,
)
from rocketmatter_mcp.client import LCSClient


async def _call(monkeypatch, fake_client, tool="list_matters", arguments=None):
    monkeypatch.setattr(server, "_c", lambda: fake_client)
    async with InMemoryTransport(server.mcp) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            return await session.call_tool(tool, arguments or {})


class _FakeClient:
    def __init__(self, failure):
        self.failure = failure

    def list_matters(self, **_kwargs):
        if self.failure:
            raise self.failure
        return [{"id": "safe-result"}]


def _text(result):
    assert result.is_error is True
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    return result.content[0].text


def test_missing_credentials_is_actionable_at_sdk_boundary(monkeypatch):
    result = asyncio.run(
        _call(
            monkeypatch,
            _FakeClient(MissingCredentialsError(("ROCKETMATTER_API_KEY",))),
        )
    )
    assert _text(result) == (
        "Missing ROCKETMATTER_API_KEY. Run: rocketmatter-mcp-setup"
    )


def test_auth_rejection_requests_reauthorization(monkeypatch):
    result = asyncio.run(_call(monkeypatch, _FakeClient(AuthenticationError("secret"))))
    assert _text(result) == (
        "Rocket Matter authorization was rejected or expired. "
        "Re-authorize with rocketmatter-mcp-setup."
    )


def test_vendor_error_uses_status_and_safe_allowlisted_reason(monkeypatch):
    result = asyncio.run(
        _call(
            monkeypatch,
            _FakeClient(
                VendorHTTPError(
                    403,
                    "The vendor denied access; check the authorized account and permissions.",
                )
            ),
        )
    )
    assert _text(result) == (
        "HTTP 403: The vendor denied access; check the authorized account and permissions."
    )


def test_rate_limit_rejects_unsafe_retry_after_and_masks_vendor_payload(monkeypatch):
    result = asyncio.run(
        _call(
            monkeypatch,
            _FakeClient(
                VendorHTTPError(
                    429,
                    "Rate limited",
                    retry_after="https://client.example/token?access_token=fake",
                )
            ),
        )
    )
    assert _text(result) == "HTTP 429: Rate limit reached. Wait briefly, then retry."


def test_vendor_reason_is_not_trusted_or_echoed(monkeypatch):
    result = asyncio.run(
        _call(
            monkeypatch,
            _FakeClient(
                VendorHTTPError(
                    502,
                    "fake-token person@example.invalid https://private.example/path",
                )
            ),
        )
    )
    assert _text(result) == "HTTP 502: The vendor rejected the request."


def test_argument_error_shows_shape_without_rejected_value(monkeypatch):
    secret_value = "person@example.invalid token-fake-908"
    result = asyncio.run(
        _call(
            monkeypatch,
            _FakeClient(
                ArgumentValidationError(
                    "page_size",
                    "a whole number greater than or equal to 1 and less than or equal to 200",
                )
            ),
        )
    )
    text = _text(result)
    assert text == (
        "Invalid argument page_size: expected a whole number greater than or equal "
        "to 1 and less than or equal to 200."
    )
    assert secret_value not in text


def test_not_found_is_explicit(monkeypatch):
    result = asyncio.run(_call(monkeypatch, _FakeClient(NotFoundError("PII"))))
    assert _text(result) == "The requested Rocket Matter record was not found."


def test_vendor_404_reaches_tool_as_not_found(monkeypatch):
    response = requests.Response()
    response.status_code = 404
    response._content = json.dumps({"message": "private record"}).encode()
    monkeypatch.setattr(LCSClient, "_send", lambda *_args, **_kwargs: response)

    class MissingRecord:
        def get_matter(self, _matter_id):
            api_client = object.__new__(LCSClient)
            return api_client._detail("matters", "fake-id")

    monkeypatch.setattr(server, "_c", MissingRecord)

    async def call():
        async with InMemoryTransport(server.mcp) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                return await session.call_tool("get_matter", {"matter_id": "fake-id"})

    result = asyncio.run(call())
    assert _text(result) == "The requested Rocket Matter record was not found."


@pytest.mark.parametrize("error_type", [RuntimeError, ValueError, TypeError])
def test_unknown_failure_is_masked_and_logs_fixed_reason(
    monkeypatch, caplog, error_type
):
    unsafe = error_type(
        "fake-token-123 person@example.invalid https://private.example/path"
    )
    with caplog.at_level(logging.ERROR, logger=server.logger.name):
        result = asyncio.run(_call(monkeypatch, _FakeClient(unsafe)))
    text = _text(result)
    assert text == "Error executing tool list_matters"
    assert "fake-token-123" not in text
    assert "person@example.invalid" not in text
    assert "private.example" not in text
    assert [record.getMessage() for record in caplog.records] == [
        "tool_failed reason=unexpected"
    ]


def test_sdk_schema_validation_returns_field_shape_before_execution(monkeypatch):
    class MustNotRun:
        def list_matters(self, **_kwargs):
            raise AssertionError("tool executed despite invalid schema")

    result = asyncio.run(
        _call(monkeypatch, MustNotRun(), arguments={"page": 0, "page_size": 500})
    )
    assert result.is_error is True
    assert _text(result) == (
        "Invalid arguments: page must be a whole number of at least 1; "
        "page_size must be a whole number greater than or equal to 1 and less than "
        "or equal to 200."
    )
    assert "page=0" not in _text(result)
    assert "page_size=500" not in _text(result)


def test_fields_json_validation_stays_actionable_at_sdk_boundary(monkeypatch):
    class MustNotRun:
        def create_matter(self, **_kwargs):
            raise AssertionError("tool execution should reject malformed fields first")

    result = asyncio.run(
        _call(
            monkeypatch,
            MustNotRun(),
            tool="create_matter",
            arguments={"fields_json": "[]"},
        )
    )
    assert result.is_error is True
    assert _text(result) == "fields_json must be a JSON object"


@pytest.mark.parametrize(
    ("status", "body", "header", "expected"),
    [
        (
            400,
            {"code": "invalid_request", "message": "private@example.invalid"},
            "8",
            "HTTP 400: The request is invalid.",
        ),
        (
            503,
            {"message": "private@example.invalid token=FAKE"},
            "8",
            "HTTP 503: The vendor rejected the request.",
        ),
        (
            429,
            {"message": "private@example.invalid"},
            "8",
            "HTTP 429: Rate limit reached. Retry after 8 seconds.",
        ),
        (
            429,
            {"message": "private@example.invalid"},
            "https://example.invalid/?key=FAKE",
            "HTTP 429: Rate limit reached. Wait briefly, then retry.",
        ),
        (
            429,
            {},
            "9" * 5000,
            "HTTP 429: Rate limit reached. Wait briefly, then retry.",
        ),
    ],
)
def test_http_failures_cross_client_and_sdk(
    monkeypatch, caplog, status, body, header, expected
):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.headers["Retry-After"] = header
    instance = object.__new__(LCSClient)
    monkeypatch.setattr(instance, "_send", lambda *_args, **_kwargs: response)
    result = asyncio.run(_call(monkeypatch, instance))
    assert _text(result) == expected
    assert "private@example.invalid" not in caplog.text
    assert "token=FAKE" not in caplog.text


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (
            400,
            "Rocket Matter authorization was rejected or expired. Re-authorize with rocketmatter-mcp-setup.",
        ),
        (503, "HTTP 503: The vendor rejected the request."),
    ],
)
def test_oauth_refresh_distinguishes_rejected_grant_from_outage(
    monkeypatch, status, expected
):
    from rocketmatter_mcp import client as client_module

    response = requests.Response()
    response.status_code = status
    response._content = b'{"error":"invalid_grant","message":"private@example.invalid"}'
    instance = object.__new__(LCSClient)
    instance._tokens = {"refresh_token": "unused"}
    instance._client_id = "unused"
    instance._client_secret = "unused"
    monkeypatch.setattr(
        client_module.requests, "post", lambda *_args, **_kwargs: response
    )

    class FakeClient:
        def list_matters(self, **_kwargs):
            return instance._refresh()

    result = asyncio.run(_call(monkeypatch, FakeClient()))
    assert _text(result) == expected


def test_vendor_404_with_real_record_remains_success(monkeypatch):
    response = requests.Response()
    response.status_code = 404
    response._content = b'{"id":"example-record","name":"Example"}'
    instance = object.__new__(LCSClient)
    monkeypatch.setattr(instance, "_send", lambda *_args, **_kwargs: response)
    result = asyncio.run(
        _call(monkeypatch, instance, "get_matter", {"matter_id": "example-record"})
    )
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    assert json.loads(result.content[0].text) == {
        "id": "example-record",
        "name": "Example",
    }
