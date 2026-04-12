"""Tests for inbox proxy endpoints: token auth, stream, reply, and actions."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from zernio_mcp.tools.inbox import (
    inbox_list,
    inbox_get_conversation,
    inbox_update,
    inbox_messages_send,
    inbox_message_edit,
    inbox_message_delete,
)
from zernio_mcp.tools.comments import (
    comments_list,
    comments_reply,
    comments_delete,
    comments_hide,
    comments_like,
    comments_private_reply,
)
from zernio_mcp.tools.reviews import reviews_list, reviews_reply
from zernio_mcp.tools.twitter import twitter_follow

API_BASE = "https://zernio.com/api"


# ---------------------------------------------------------------------------
# Auth / token tests
# ---------------------------------------------------------------------------


def test_create_inbox_token():
    """create_inbox_token returns a unique token string."""
    from zernio_mcp.inbox import create_inbox_token, _inbox_tokens

    token = create_inbox_token()
    assert isinstance(token, str)
    assert len(token) > 20
    assert token in _inbox_tokens


def test_create_inbox_token_unique():
    """Each call creates a different token."""
    from zernio_mcp.inbox import create_inbox_token

    t1 = create_inbox_token()
    t2 = create_inbox_token()
    assert t1 != t2


# ---------------------------------------------------------------------------
# MCP tool: inbox_get_link
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_inbox_get_link():
    """inbox_get_link returns a URL with a valid token."""
    from zernio_mcp.tools.misc import inbox_get_link

    result = await inbox_get_link()
    assert "inboxUrl" in result
    assert "/inbox?token=" in result["inboxUrl"]
    assert "expiresIn" in result


# ---------------------------------------------------------------------------
# Stream endpoint tests (mock Zernio API with respx)
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_stream_merges_sources():
    """Stream endpoint merges conversations, comments, and reviews."""
    # Mock conversations
    respx.get(f"{API_BASE}/v1/inbox/conversations").mock(
        return_value=httpx.Response(200, json={
            "conversations": [
                {
                    "_id": "conv1",
                    "platform": "twitter",
                    "participant": {"name": "Alice", "username": "alice"},
                    "lastMessage": "Hey there",
                    "updatedAt": "2026-04-11T10:00:00Z",
                    "unread": True,
                }
            ]
        })
    )
    # Mock comments
    respx.get(f"{API_BASE}/v1/inbox/comments").mock(
        return_value=httpx.Response(200, json={
            "comments": [
                {
                    "_id": "com1",
                    "platform": "instagram",
                    "author": {"name": "Bob", "username": "bob"},
                    "content": "Nice post!",
                    "createdAt": "2026-04-11T11:00:00Z",
                }
            ]
        })
    )
    # Mock reviews
    respx.get(f"{API_BASE}/v1/inbox/reviews").mock(
        return_value=httpx.Response(200, json={
            "reviews": [
                {
                    "_id": "rev1",
                    "platform": "google",
                    "author": {"name": "Carol"},
                    "content": "Great service",
                    "rating": 5,
                    "createdAt": "2026-04-11T09:00:00Z",
                }
            ]
        })
    )

    # Call the individual list tools and verify all three return data
    convs = await inbox_list()
    assert "conversations" in convs
    assert len(convs["conversations"]) == 1
    assert convs["conversations"][0]["_id"] == "conv1"

    coms = await comments_list()
    assert "comments" in coms
    assert len(coms["comments"]) == 1
    assert coms["comments"][0]["_id"] == "com1"

    revs = await reviews_list()
    assert "reviews" in revs
    assert len(revs["reviews"]) == 1
    assert revs["reviews"][0]["_id"] == "rev1"


@respx.mock
@pytest.mark.asyncio
async def test_stream_filters_by_type():
    """Passing status filter returns only matching conversations."""
    respx.get(f"{API_BASE}/v1/inbox/conversations").mock(
        return_value=httpx.Response(200, json={
            "conversations": [
                {"_id": "conv1", "platform": "twitter", "status": "unread"},
            ]
        })
    )
    result = await inbox_list(status="unread")
    req = respx.calls.last.request
    assert "status=unread" in str(req.url)
    assert result["conversations"][0]["status"] == "unread"


@respx.mock
@pytest.mark.asyncio
async def test_stream_filters_by_platform():
    """Passing platform filter returns only matching items."""
    respx.get(f"{API_BASE}/v1/inbox/conversations").mock(
        return_value=httpx.Response(200, json={
            "conversations": [
                {"_id": "conv1", "platform": "twitter"},
            ]
        })
    )
    result = await inbox_list(platform="twitter")
    req = respx.calls.last.request
    assert "platform=twitter" in str(req.url)
    assert result["conversations"][0]["platform"] == "twitter"


# ---------------------------------------------------------------------------
# Reply tests
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_reply_dm():
    """Sending a DM reply calls the correct endpoint."""
    respx.post(f"{API_BASE}/v1/inbox/conversations/conv1/messages").mock(
        return_value=httpx.Response(200, json={"success": True, "message": {"_id": "msg1"}})
    )
    result = await inbox_messages_send("conv1", "Hello!")
    assert result["success"] is True
    req = respx.calls.last.request
    body = json.loads(req.content)
    assert body["content"] == "Hello!"


@respx.mock
@pytest.mark.asyncio
async def test_reply_comment():
    """Replying to a comment calls the correct endpoint."""
    respx.post(f"{API_BASE}/v1/inbox/comments/post1").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await comments_reply("post1", "com1", "Thanks!")
    assert result["success"] is True
    req = respx.calls.last.request
    body = json.loads(req.content)
    assert body["commentId"] == "com1"
    assert body["content"] == "Thanks!"


@respx.mock
@pytest.mark.asyncio
async def test_reply_private():
    """Private reply sends to the correct endpoint."""
    respx.post(f"{API_BASE}/v1/inbox/comments/post1/com1/private-reply").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await comments_private_reply("post1", "com1", "Private message")
    assert result["success"] is True
    req = respx.calls.last.request
    body = json.loads(req.content)
    assert body["content"] == "Private message"


# ---------------------------------------------------------------------------
# Action tests
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_action_archive():
    """Archiving a conversation calls PUT with status=archived."""
    respx.put(f"{API_BASE}/v1/inbox/conversations/conv1").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await inbox_update("conv1", "archived")
    assert result["success"] is True
    req = respx.calls.last.request
    body = json.loads(req.content)
    assert body["status"] == "archived"


@respx.mock
@pytest.mark.asyncio
async def test_action_hide():
    """Hiding a comment calls the hide endpoint."""
    respx.post(f"{API_BASE}/v1/inbox/comments/post1/com1/hide").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await comments_hide("post1", "com1")
    assert result["success"] is True


@respx.mock
@pytest.mark.asyncio
async def test_action_delete_comment():
    """Deleting a comment calls the delete endpoint."""
    respx.delete(f"{API_BASE}/v1/inbox/comments/post1").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await comments_delete("post1", "com1")
    assert result["success"] is True
    req = respx.calls.last.request
    assert "commentId=com1" in str(req.url)


@respx.mock
@pytest.mark.asyncio
async def test_action_like():
    """Liking a comment calls the like endpoint."""
    respx.post(f"{API_BASE}/v1/inbox/comments/post1/com1/like").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await comments_like("post1", "com1")
    assert result["success"] is True


@respx.mock
@pytest.mark.asyncio
async def test_action_follow():
    """Following a Twitter user calls the follow endpoint."""
    respx.post(f"{API_BASE}/v1/twitter/follow").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    result = await twitter_follow("a1", "user123")
    assert result["success"] is True
    req = respx.calls.last.request
    body = json.loads(req.content)
    assert body["accountId"] == "a1"
    assert body["targetUserId"] == "user123"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_reply_dm_api_error():
    """DM reply returns error dict on API failure."""
    respx.post(f"{API_BASE}/v1/inbox/conversations/conv1/messages").mock(
        return_value=httpx.Response(403, json={"error": "Conversation not found"})
    )
    result = await inbox_messages_send("conv1", "Hello!")
    assert "error" in result


@respx.mock
@pytest.mark.asyncio
async def test_action_archive_api_error():
    """Archive returns error dict on API failure."""
    respx.put(f"{API_BASE}/v1/inbox/conversations/conv1").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )
    result = await inbox_update("conv1", "archived")
    assert "error" in result
    assert "test-key-for-testing" not in result["error"]


@respx.mock
@pytest.mark.asyncio
async def test_get_conversation_with_messages():
    """inbox_get_conversation fetches both conversation and messages."""
    respx.get(f"{API_BASE}/v1/inbox/conversations/conv1").mock(
        return_value=httpx.Response(200, json={
            "_id": "conv1", "platform": "twitter", "participant": {"name": "Alice"},
        })
    )
    respx.get(f"{API_BASE}/v1/inbox/conversations/conv1/messages").mock(
        return_value=httpx.Response(200, json={
            "messages": [
                {"_id": "msg1", "content": "Hi", "createdAt": "2026-04-11T10:00:00Z"},
            ]
        })
    )
    result = await inbox_get_conversation("conv1")
    assert result["_id"] == "conv1"
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert result["messages"][0]["content"] == "Hi"


@respx.mock
@pytest.mark.asyncio
async def test_get_conversation_without_messages():
    """inbox_get_conversation with include_messages=False skips message fetch."""
    respx.get(f"{API_BASE}/v1/inbox/conversations/conv1").mock(
        return_value=httpx.Response(200, json={
            "_id": "conv1", "platform": "twitter",
        })
    )
    result = await inbox_get_conversation("conv1", include_messages=False)
    assert result["_id"] == "conv1"
    assert "messages" not in result
    # Only one request should have been made (no messages endpoint call)
    assert len(respx.calls) == 1
