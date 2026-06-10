"""Pass-3 contract tests: the newly typed-output tools must keep their existing
unstructured TEXT shape and must never be rejected by FastMCP's output-schema
validation on either the success or the error path.

These exercise the tools end-to-end through an in-memory ``fastmcp.Client`` (the
same path real clients take), so they catch the failure mode the AccountList bug
exposed: a declared ``output_schema`` that the actual ``{"error": ...}`` (or a
sparse success) payload violates, which would surface to clients as a schema
error instead of the upstream message.

For each tool we assert:
  * ``result.is_error`` is False (FastMCP accepted the payload),
  * the unstructured text content equals ``json.dumps`` of the dict the tool
    returns — i.e. typing the output did NOT change the text shape, and
  * ``structured_content`` is present and equals that same dict (purely
    additive structured output).
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from fastmcp import Client

from zernio_mcp.server import mcp
from zernio_mcp.client import _cache

API = "https://zernio.com/api"


@pytest.fixture(autouse=True)
def _clear_cache():
    _cache.clear()
    yield
    _cache.clear()


async def _call(name: str, args: dict):
    async with Client(mcp) as client:
        return await client.call_tool(name, args)


def _assert_equivalent(result, expected_dict: dict):
    """The tool's text content and structured content both equal expected_dict."""
    assert result.is_error is False
    assert result.content, "expected at least one text content block"
    text = result.content[0].text
    # Text is the verbatim serialization of the returned dict — compare as JSON
    # so key-order / whitespace differences don't cause false failures.
    assert json.loads(text) == expected_dict
    # Structured content is purely additive and mirrors the returned dict.
    assert result.structured_content == expected_dict


# ---------------------------------------------------------------------------
# Success-path equivalence
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_analytics_insights_text_preserved():
    payload = {"bestHour": 14, "bestDay": "Tuesday"}
    respx.get(f"{API}/v1/analytics/best-time").mock(return_value=httpx.Response(200, json=payload))
    result = await _call("analytics_insights", {"type": "best_time"})
    _assert_equivalent(result, payload)


@respx.mock
@pytest.mark.asyncio
async def test_analytics_instagram_text_preserved():
    respx.get(f"{API}/v1/analytics/instagram/account-insights").mock(
        return_value=httpx.Response(200, json={"reach": 100, "impressions": 250})
    )
    respx.get(f"{API}/v1/analytics/instagram/demographics").mock(
        return_value=httpx.Response(200, json={"ages": []})
    )
    result = await _call("analytics_instagram", {"account_id": "a1"})
    _assert_equivalent(
        result, {"reach": 100, "impressions": 250, "demographics": {"ages": []}}
    )


@respx.mock
@pytest.mark.asyncio
async def test_inbox_list_text_preserved():
    payload = {
        "conversations": [
            {"_id": "c1", "platform": "twitter", "status": "unread",
             "participant": {"name": "Al"}}
        ]
    }
    respx.get(f"{API}/v1/inbox/conversations").mock(return_value=httpx.Response(200, json=payload))
    result = await _call("inbox_list", {})
    _assert_equivalent(result, payload)


@respx.mock
@pytest.mark.asyncio
async def test_inbox_get_conversation_text_preserved():
    respx.get(f"{API}/v1/inbox/conversations/c1").mock(
        return_value=httpx.Response(200, json={"_id": "c1", "platform": "twitter"})
    )
    respx.get(f"{API}/v1/inbox/conversations/c1/messages").mock(
        return_value=httpx.Response(
            200, json={"messages": [{"_id": "m1", "content": "Hi", "createdAt": "t"}]}
        )
    )
    result = await _call("inbox_get_conversation", {"conversation_id": "c1"})
    _assert_equivalent(
        result,
        {
            "_id": "c1",
            "platform": "twitter",
            "messages": [{"_id": "m1", "content": "Hi", "createdAt": "t"}],
        },
    )


@respx.mock
@pytest.mark.asyncio
async def test_comments_list_text_preserved():
    payload = {"comments": [{"_id": "x1", "platform": "ig", "content": "nice", "createdAt": "t"}]}
    respx.get(f"{API}/v1/inbox/comments").mock(return_value=httpx.Response(200, json=payload))
    result = await _call("comments_list", {})
    _assert_equivalent(result, payload)


@respx.mock
@pytest.mark.asyncio
async def test_logs_posts_text_preserved():
    payload = {"logs": [{"event": "published", "at": "t"}]}
    respx.get(f"{API}/v1/posts/logs").mock(return_value=httpx.Response(200, json=payload))
    result = await _call("logs_posts", {})
    _assert_equivalent(result, payload)


@respx.mock
@pytest.mark.asyncio
async def test_usage_stats_text_preserved():
    payload = {"posts": 42, "billing": {"plan": "pro"}}
    respx.get(f"{API}/v1/usage-stats").mock(return_value=httpx.Response(200, json=payload))
    result = await _call("usage_stats", {})
    _assert_equivalent(result, payload)


# ---------------------------------------------------------------------------
# Error-path: the {"error": ...} payload must pass output-schema validation
# (this is the regression the AccountList fix guards against, exercised live).
# ---------------------------------------------------------------------------


ERROR_CASES = [
    ("analytics_insights", {"type": "best_time"}, "GET", "/v1/analytics/best-time"),
    ("analytics_instagram", {"account_id": "a1"}, "GET", "/v1/analytics/instagram/account-insights"),
    ("inbox_list", {}, "GET", "/v1/inbox/conversations"),
    ("inbox_get_conversation", {"conversation_id": "c1"}, "GET", "/v1/inbox/conversations/c1"),
    ("comments_list", {}, "GET", "/v1/inbox/comments"),
    ("logs_posts", {}, "GET", "/v1/posts/logs"),
    ("usage_stats", {}, "GET", "/v1/usage-stats"),
]


@pytest.mark.parametrize("name,args,method,path", ERROR_CASES, ids=[c[0] for c in ERROR_CASES])
@respx.mock
@pytest.mark.asyncio
async def test_error_path_not_rejected_by_output_schema(name, args, method, path):
    """A 500 from upstream yields an ``{"error": ...}`` dict that FastMCP must
    accept (no ``is_error``) — the declared output_schema validates it."""
    respx.route(method=method, url=f"{API}{path}").mock(
        return_value=httpx.Response(500, json={"error": "boom"})
    )
    result = await _call(name, args)
    assert result.is_error is False
    body = json.loads(result.content[0].text)
    assert "error" in body
    assert "boom" in body["error"]
    # Sanity: the structured content carries the same error envelope.
    assert result.structured_content["error"] == body["error"]
