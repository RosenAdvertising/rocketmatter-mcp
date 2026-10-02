"""Safe error text regressions through the official in-memory MCP client."""

from __future__ import annotations

import asyncio
import json
import logging

import pytest
import requests
from mcp.client import ClientSession
from mcp.client._memory import InMemoryTransport
from mcp.types import TextContent

from rocketmatter_mcp import server
from rocketmatter_mcp.client import LCSClient
from rocketmatter_mcp.errors import (
    ArgumentValidationError,
    AuthenticationError,
    MissingCredentialsError,
    NotFoundError,
    TransportError,
    VendorHTTPError,
)


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


def test_public_call_tool_preserves_safe_errors_without_transport(monkeypatch):
    monkeypatch.setattr(server, "_c", lambda: _FakeClient(TransportError("POST")))
    result = asyncio.run(server.mcp.call_tool("list_matters", {}))
    assert _text(result) == (
        "The operation outcome is unknown because the connection failed. "
        "Check whether it completed before retrying."
    )


def test_missing_credentials_is_actionable_at_sdk_boundary(monkeypatch):
    result = asyncio.run(
        _call(
            monkeypatch,
            _FakeClient(MissingCredentialsError(("ROCKETMATTER_API_KEY",))),
        )
    )
    assert _text(result) == (
        "Missing ROCKETMATTER_API_KEY. Run rocketmatter-mcp-setup, then restart the MCP server."
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
                    "Rocket Matter access denied: the connected account lacks permission for this action (or the authorization expired; re-run rocketmatter-mcp-setup if so).",
                )
            ),
        )
    )
    assert _text(result) == (
        "HTTP 403: Rocket Matter access denied: the connected account lacks permission for this action (or the authorization expired; re-run rocketmatter-mcp-setup if so)."
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


@pytest.mark.parametrize(
    ("method", "expected"),
    [
        (
            "GET",
            "The Rocket Matter read could not complete because of a timeout or connection failure. You may retry.",
        ),
        (
            "POST",
            "The operation outcome is unknown because the connection failed. Check whether it completed before retrying.",
        ),
        (
            "PUT",
            "The operation outcome is unknown because the connection failed. Check whether it completed before retrying.",
        ),
        (
            "DELETE",
            "The operation outcome is unknown because the connection failed. Check whether it completed before retrying.",
        ),
    ],
)
def test_transport_failure_dispatch_is_safe_and_method_aware(
    monkeypatch, method, expected
):
    class FailingClient:
        def list_matters(self, **_kwargs):
            raise TransportError(method)

    result = asyncio.run(_call(monkeypatch, FailingClient()))
    assert _text(result) == expected


@pytest.mark.parametrize(
    "failure", [requests.Timeout("private-url"), requests.ConnectionError("secret")]
)
def test_send_maps_transport_error_without_retry(monkeypatch, failure):
    from rocketmatter_mcp.errors import TransportError

    instance = object.__new__(LCSClient)
    instance._token_valid = lambda: True
    instance._headers = lambda: {}

    class Session:
        calls = 0

        def request(self, *_args, **kwargs):
            self.calls += 1
            assert kwargs["timeout"] == 30
            raise failure

    session = Session()
    monkeypatch.setattr(instance, "session", session, raising=False)
    with pytest.raises(TransportError) as caught:
        instance._send("POST", "matters")
    assert caught.value.unsafe is True
    assert session.calls == 1


def test_id_path_segment_is_validated_before_request_preparation(monkeypatch):
    instance = object.__new__(LCSClient)
    seen = {}

    class Response:
        status_code = 200
        ok = True
        content = b'{"id":"normal-id"}'

        @staticmethod
        def json():
            return {"id": "normal-id"}

    def send(method, path, **_kwargs):
        seen["path"] = path
        return Response()

    monkeypatch.setattr(instance, "_send", send)
    instance._detail("matters", "normal-id")
    assert seen["path"] == "matters/normal-id"
    assert instance._url(seen["path"]).endswith("/v1/matters/normal-id")


def test_all_oauth_posts_have_explicit_timeout(monkeypatch):
    from rocketmatter_mcp import client as client_module

    seen = []

    class Response:
        ok = True
        status_code = 200
        headers = {}

        @staticmethod
        def json():
            return {"access_token": "fake", "refresh_token": "fake"}

    def post(*_args, **kwargs):
        seen.append(kwargs["timeout"])
        return Response()

    monkeypatch.setattr(client_module.requests, "post", post)
    client_module.exchange_code(
        "fake-code", client_id="id", client_secret="secret", save=False
    )
    instance = object.__new__(LCSClient)
    instance._tokens = {"refresh_token": "fake"}
    instance._client_id = "id"
    instance._client_secret = "secret"
    monkeypatch.setattr(client_module, "_save_tokens", lambda _tokens: None)
    instance._refresh()
    assert seen == [30, 30]


def test_setup_eof_exits_cleanly_and_does_not_request_network(monkeypatch, capsys):
    from rocketmatter_mcp.setup import oauth_flow

    monkeypatch.setattr(oauth_flow, "_capture", lambda *_args, **_kwargs: "")
    monkeypatch.setattr(
        oauth_flow.sys, "exit", lambda code: (_ for _ in ()).throw(SystemExit(code))
    )
    with pytest.raises(SystemExit) as caught:
        oauth_flow.main()
    assert caught.value.code == 1
    assert "all required" in capsys.readouterr().out


def test_setup_prompt_eof_is_actionable_without_traceback(monkeypatch, capsys):
    from rocketmatter_mcp.setup import oauth_flow

    monkeypatch.delenv("ROCKETMATTER_API_KEY", raising=False)
    monkeypatch.setattr(
        "builtins.input", lambda _prompt: (_ for _ in ()).throw(EOFError())
    )
    monkeypatch.setattr(
        oauth_flow.getpass, "getpass", lambda _prompt: (_ for _ in ()).throw(EOFError())
    )
    with pytest.raises(SystemExit) as caught:
        oauth_flow.main()
    output = capsys.readouterr().out
    assert caught.value.code == 1
    assert "all required" in output
    assert "Traceback" not in output


def test_setup_callback_timeout_exits_without_network(monkeypatch, capsys):
    from rocketmatter_mcp.setup import oauth_flow

    monkeypatch.setattr(oauth_flow, "_capture", lambda *_args, **_kwargs: "fake")
    monkeypatch.setattr(oauth_flow.credentials, "set_secret", lambda *_args: "file")
    monkeypatch.setattr(oauth_flow.credentials, "ENV_FILE", "/tmp/fake.env")
    monkeypatch.setattr(
        oauth_flow, "build_authorize_url", lambda *_args: "https://example.invalid"
    )
    monkeypatch.delenv("ROCKETMATTER_OAUTH_CODE", raising=False)
    monkeypatch.setattr(
        oauth_flow.LoopbackCallback,
        "receive",
        lambda self: (_ for _ in ()).throw(ValueError("timeout")),
    )
    monkeypatch.setattr(oauth_flow.sys, "argv", ["rocketmatter-mcp-setup"])
    monkeypatch.setattr(
        "builtins.input", lambda _prompt: (_ for _ in ()).throw(EOFError())
    )
    with pytest.raises(SystemExit) as caught:
        oauth_flow.main()
    output = capsys.readouterr().out
    assert caught.value.code == 1
    assert "valid OAuth callback" in output
    assert "Traceback" not in output


def test_setup_fake_bad_code_exits_safely(monkeypatch, capsys):
    from rocketmatter_mcp import client as client_module
    from rocketmatter_mcp.setup import oauth_flow

    class Response:
        ok = False
        status_code = 400
        headers = {}

        @staticmethod
        def json():
            return {"error": "invalid_grant", "message": "private vendor detail"}

    monkeypatch.setattr(client_module.requests, "post", lambda *_a, **_k: Response())
    monkeypatch.setattr(
        oauth_flow, "_capture", lambda name, *_a, **_k: "fake" if name != "" else ""
    )
    monkeypatch.setattr(oauth_flow.credentials, "set_secret", lambda *_a: "file")
    monkeypatch.setattr(oauth_flow.credentials, "ENV_FILE", "/tmp/fake.env")
    monkeypatch.setattr(
        oauth_flow, "build_authorize_url", lambda *_a: "https://example.invalid"
    )
    monkeypatch.setenv("ROCKETMATTER_OAUTH_CODE", "fake-code")
    monkeypatch.setattr(oauth_flow.sys, "argv", ["rocketmatter-mcp-setup"])
    with pytest.raises(SystemExit) as caught:
        oauth_flow.main()
    output = capsys.readouterr().out
    assert caught.value.code == 1
    assert "Authorization failed" in output
    assert "private vendor detail" not in output
    assert "Traceback" not in output


def test_verify_no_credentials_exits_with_safe_action(monkeypatch, capsys):
    from rocketmatter_mcp.setup import verify

    monkeypatch.setattr(
        verify,
        "LCSClient",
        lambda: (_ for _ in ()).throw(
            MissingCredentialsError(("ROCKETMATTER_API_KEY",))
        ),
    )
    with pytest.raises(SystemExit) as caught:
        verify.main()
    out = capsys.readouterr().out
    assert caught.value.code == 1
    assert "rocketmatter-mcp-setup" in out
    assert "Traceback" not in out


def test_verify_fake_bad_credentials_exits_with_safe_action(monkeypatch, capsys):
    from rocketmatter_mcp.setup import verify

    class BadCredentialsClient:
        def list_users(self, **_kwargs):
            raise AuthenticationError("private vendor payload")

    monkeypatch.setattr(verify, "LCSClient", BadCredentialsClient)
    with pytest.raises(SystemExit) as caught:
        verify.main()
    out = capsys.readouterr().out
    assert caught.value.code == 1
    assert "rocketmatter-mcp-setup" in out
    assert "private vendor payload" not in out
    assert "Traceback" not in out


@pytest.mark.parametrize(
    "reason",
    [
        "Rocket Matter access denied: private@example.invalid",
        "The operation is not permitted.",
    ],
)
def test_forbidden_reason_cannot_replace_permission_guidance(monkeypatch, reason):
    result = asyncio.run(_call(monkeypatch, _FakeClient(VendorHTTPError(403, reason))))
    assert (
        _text(result)
        == "HTTP 403: Rocket Matter access denied: the connected account lacks permission for this action (or the authorization expired; re-run rocketmatter-mcp-setup if so)."
    )


def _live_client_with_session(monkeypatch, response=None, failure=None):
    instance = object.__new__(LCSClient)
    monkeypatch.setattr(instance, "_token_valid", lambda: True)
    monkeypatch.setattr(instance, "_headers", lambda: {})
    calls = []

    class Session:
        def request(self, method, url, **kwargs):
            calls.append((method, url, kwargs))
            if failure is not None:
                raise failure
            return response

    session = Session()
    monkeypatch.setattr(instance, "session", session, raising=False)
    return instance, calls


@pytest.mark.parametrize("error_type", [requests.Timeout, requests.ConnectionError])
@pytest.mark.parametrize(
    ("tool", "arguments", "method"),
    [
        ("list_matters", {}, "GET"),
        ("create_matter", {"fields_json": "{}"}, "POST"),
        ("delete_matter", {"matter_id": "normal-id"}, "DELETE"),
    ],
)
def test_real_request_failure_reaches_sdk_with_method_safe_guidance(
    monkeypatch, error_type, tool, arguments, method
):
    client, calls = _live_client_with_session(
        monkeypatch, failure=error_type("private-url")
    )
    result = asyncio.run(_call(monkeypatch, client, tool, arguments))
    expected = (
        "The Rocket Matter read could not complete because of a timeout or connection failure. You may retry."
        if method == "GET"
        else "The operation outcome is unknown because the connection failed. Check whether it completed before retrying."
    )
    assert _text(result) == expected
    assert "retry shortly" not in _text(result).lower()
    assert len(calls) == 1 and calls[0][0] == method
    assert calls[0][2]["timeout"] == 30
    if method == "DELETE":
        assert (
            requests.Request(method, calls[0][1]).prepare().path_url
            == "/v1/matters/normal-id"
        )


@pytest.mark.parametrize(
    ("status", "body", "expected"),
    [
        (
            403,
            {"error": "private"},
            "HTTP 403: Rocket Matter access denied: the connected account lacks permission for this action (or the authorization expired; re-run rocketmatter-mcp-setup if so).",
        ),
        (
            429,
            {"error": "private"},
            "HTTP 429: Rate limit reached. Retry after 120 seconds.",
        ),
        (
            200,
            {"success": False, "message": "private"},
            "HTTP 200: The vendor reported that the request failed.",
        ),
    ],
)
def test_real_http_failures_are_errors_and_do_not_sleep(
    monkeypatch, status, body, expected
):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode()
    response.headers["Retry-After"] = "120"
    client, _ = _live_client_with_session(monkeypatch, response=response)
    sleeps = []
    monkeypatch.setattr("time.sleep", sleeps.append)
    result = asyncio.run(_call(monkeypatch, client))
    assert _text(result) == expected
    assert sleeps == []


@pytest.fixture(autouse=True)
def validated_callback_for_token_exchange_tests(monkeypatch):
    from rocketmatter_mcp.setup import oauth_flow

    class BoundCallback:
        def __init__(self, *args):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def receive(self):
            return "dummy-code"

    monkeypatch.setattr(oauth_flow, "LoopbackCallback", BoundCallback)
