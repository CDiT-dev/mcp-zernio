"""E2E tests for MCP tools using respx to mock the Zernio API."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from zernio_mcp.tools.accounts import accounts_list, accounts_health
from zernio_mcp.tools.profiles import profiles_list
from zernio_mcp.tools.posts import posts_create, posts_get, posts_list, posts_delete, posts_unpublish, posts_retry, MediaItem, ThreadItem
from zernio_mcp.tools.media import media_upload, media_get_upload_link, media_check_upload
from zernio_mcp.tools.analytics import analytics_posts, analytics_insights
from zernio_mcp.tools.queue import queue_preview

API_BASE = "https://zernio.com/api"


@respx.mock
@pytest.mark.asyncio
async def test_accounts_list_strips_pii():
    respx.get(f"{API_BASE}/v1/accounts").mock(
        return_value=httpx.Response(200, json={
            "accounts": [
                {"_id": "a1", "platform": "twitter", "username": "test", "email": "secret@test.com"}
            ]
        })
    )
    result = await accounts_list()
    assert len(result["accounts"]) == 1
    assert "email" not in result["accounts"][0]
    assert result["accounts"][0]["username"] == "test"


@respx.mock
@pytest.mark.asyncio
async def test_accounts_health_adds_reauth():
    respx.get(f"{API_BASE}/v1/accounts/health").mock(
        return_value=httpx.Response(200, json={
            "accounts": [
                {"_id": "a1", "platform": "instagram", "status": "expired"}
            ]
        })
    )
    result = await accounts_health()
    assert result["accounts"][0]["status"] == "expired"
    assert "reauth_instructions" in result["accounts"][0]
    assert "app.zernio.com" in result["accounts"][0]["reauth_instructions"]


@respx.mock
@pytest.mark.asyncio
async def test_profiles_list():
    respx.get(f"{API_BASE}/v1/profiles").mock(
        return_value=httpx.Response(200, json={"profiles": [{"_id": "p1", "name": "Brand A"}]})
    )
    result = await profiles_list()
    assert "profiles" in result


@respx.mock
@pytest.mark.asyncio
async def test_posts_create_draft_by_default():
    respx.post(f"{API_BASE}/v1/posts").mock(
        return_value=httpx.Response(200, json={
            "post": {"_id": "post1", "status": "draft"}
        })
    )
    result = await posts_create(
        content="Hello world",
        platforms=[{"platform": "twitter", "accountId": "a1"}],
    )
    assert result["post"]["status"] == "draft"
    # Verify the request body did NOT include publishNow
    req = respx.calls.last.request
    body = json.loads(req.content)
    assert "publishNow" not in body
    assert "scheduledFor" not in body


@respx.mock
@pytest.mark.asyncio
async def test_posts_create_immediate_publish():
    respx.post(f"{API_BASE}/v1/posts").mock(
        return_value=httpx.Response(200, json={
            "post": {"_id": "post1", "status": "published", "platformPostUrl": "https://x.com/..."}
        })
    )
    result = await posts_create(
        content="Hello world",
        platforms=[{"platform": "twitter", "accountId": "a1"}],
        publish_now=True,
    )
    req = respx.calls.last.request
    body = json.loads(req.content)
    assert body["publishNow"] is True


@respx.mock
@pytest.mark.asyncio
async def test_posts_create_scheduled():
    respx.post(f"{API_BASE}/v1/posts").mock(
        return_value=httpx.Response(200, json={
            "post": {"_id": "post1", "status": "scheduled"}
        })
    )
    result = await posts_create(
        content="Scheduled post",
        platforms=[{"platform": "linkedin", "accountId": "a2"}],
        scheduled_for="2026-04-01T09:00:00Z",
    )
    req = respx.calls.last.request
    body = json.loads(req.content)
    assert body["scheduledFor"] == "2026-04-01T09:00:00Z"
    assert "publishNow" not in body


@respx.mock
@pytest.mark.asyncio
async def test_posts_get_with_failure_reason():
    respx.get(f"{API_BASE}/v1/posts/post1").mock(
        return_value=httpx.Response(200, json={
            "post": {"_id": "post1", "status": "failed", "failure_reason": "Image too large"}
        })
    )
    result = await posts_get("post1")
    assert result["post"]["failure_reason"] == "Image too large"


@respx.mock
@pytest.mark.asyncio
async def test_posts_list_with_status_filter():
    respx.get(f"{API_BASE}/v1/posts").mock(
        return_value=httpx.Response(200, json={"posts": []})
    )
    result = await posts_list(status="failed")
    req = respx.calls.last.request
    assert "status=failed" in str(req.url)


@respx.mock
@pytest.mark.asyncio
async def test_posts_list_caps_limit():
    respx.get(f"{API_BASE}/v1/posts").mock(
        return_value=httpx.Response(200, json={"posts": []})
    )
    await posts_list(limit=100)
    req = respx.calls.last.request
    assert "limit=50" in str(req.url)


@respx.mock
@pytest.mark.asyncio
async def test_posts_delete_rejects_published():
    """API error on published post redirects to posts_unpublish."""
    respx.delete(f"{API_BASE}/v1/posts/post1").mock(
        return_value=httpx.Response(409, json={"error": "Cannot delete published post"})
    )
    result = await posts_delete("post1")
    assert "error" in result
    assert "posts_unpublish" in result["error"]


@respx.mock
@pytest.mark.asyncio
async def test_posts_delete_allows_draft():
    respx.delete(f"{API_BASE}/v1/posts/post1").mock(
        return_value=httpx.Response(200, json={"deleted": True})
    )
    result = await posts_delete("post1")
    assert result.get("deleted") is True


@respx.mock
@pytest.mark.asyncio
async def test_posts_unpublish_rejects_draft():
    """API error on draft post redirects to posts_delete."""
    respx.post(f"{API_BASE}/v1/posts/post1/unpublish").mock(
        return_value=httpx.Response(422, json={"error": "Cannot unpublish draft post"})
    )
    result = await posts_unpublish("post1")
    assert "error" in result
    assert "posts_delete" in result["error"]


@respx.mock
@pytest.mark.asyncio
async def test_posts_retry():
    respx.post(f"{API_BASE}/v1/posts/post1/retry").mock(
        return_value=httpx.Response(200, json={
            "post": {"_id": "post1", "status": "published"}
        })
    )
    result = await posts_retry("post1")
    assert result["post"]["status"] == "published"


@pytest.mark.asyncio
async def test_media_upload_ssrf_private_ip():
    result = await media_upload(url="https://192.168.1.1/image.jpg")
    assert "error" in result
    assert "non-public" in result["error"]


@pytest.mark.asyncio
async def test_media_upload_ssrf_http_scheme():
    result = await media_upload(url="http://example.com/image.jpg")
    assert "error" in result
    assert "HTTPS" in result["error"]


@pytest.mark.asyncio
async def test_media_get_upload_link():
    """media_get_upload_link returns a URL and token."""
    result = await media_get_upload_link()
    assert "uploadPageUrl" in result
    assert "token" in result
    assert "/upload?token=" in result["uploadPageUrl"]


@pytest.mark.asyncio
async def test_media_check_upload_pending():
    """media_check_upload returns pending for unknown tokens."""
    result = await media_check_upload(token="nonexistent")
    assert result["status"] == "pending"


@pytest.mark.asyncio
async def test_media_check_upload_completed():
    """media_check_upload returns publicUrl after upload completes."""
    from zernio_mcp.upload import _upload_results
    import time
    _upload_results["test-token"] = ("https://cdn.zernio.com/test.png", time.monotonic())
    result = await media_check_upload(token="test-token")
    assert result["publicUrl"] == "https://cdn.zernio.com/test.png"


@respx.mock
@pytest.mark.asyncio
async def test_analytics_posts():
    respx.get(f"{API_BASE}/v1/analytics").mock(
        return_value=httpx.Response(200, json={"posts": [{"likes": 42}]})
    )
    result = await analytics_posts()
    assert result["posts"][0]["likes"] == 42


@respx.mock
@pytest.mark.asyncio
async def test_analytics_insights_best_time():
    respx.get(f"{API_BASE}/v1/analytics/best-time").mock(
        return_value=httpx.Response(200, json={"bestHour": 14, "bestDay": "Tuesday"})
    )
    result = await analytics_insights(type="best_time")
    assert result["bestHour"] == 14


@respx.mock
@pytest.mark.asyncio
async def test_analytics_insights_maps_origin():
    """Verify 'via_zernio' is mapped to 'late' in API call."""
    respx.get(f"{API_BASE}/v1/analytics/daily-metrics").mock(
        return_value=httpx.Response(200, json={"metrics": []})
    )
    await analytics_insights(type="daily_metrics", origin="via_zernio")
    req = respx.calls.last.request
    assert "source=late" in str(req.url)


@respx.mock
@pytest.mark.asyncio
async def test_queue_preview():
    respx.get(f"{API_BASE}/v1/queue/preview").mock(
        return_value=httpx.Response(200, json={
            "slots": [
                {"datetime": "2026-04-01T14:00:00Z", "platform": "twitter", "occupied": False}
            ]
        })
    )
    result = await queue_preview(profile_id="p1")
    assert result["slots"][0]["occupied"] is False


@respx.mock
@pytest.mark.asyncio
async def test_api_error_does_not_leak_key():
    """Verify API errors don't contain the API key."""
    respx.get(f"{API_BASE}/v1/accounts").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )
    result = await accounts_list()
    assert "error" in result
    assert "test-key-for-testing" not in result["error"]


# ---------------------------------------------------------------------------
# Thread items (Twitter/X and Bluesky)
# ---------------------------------------------------------------------------


@respx.mock
@pytest.mark.asyncio
async def test_posts_create_thread_twitter():
    """Thread items produce correct API payload for Twitter."""
    respx.post(f"{API_BASE}/v1/posts").mock(
        return_value=httpx.Response(200, json={
            "post": {"_id": "post_thread", "status": "published"}
        })
    )
    result = await posts_create(
        platforms=[{"platform": "twitter", "accountId": "a1"}],
        publish_now=True,
        thread_items=[
            ThreadItem(content="First tweet"),
            ThreadItem(content="Second tweet", media_items=[MediaItem(url="https://img.test/1.jpg", type="image")]),
            ThreadItem(content="Third tweet"),
        ],
    )
    assert result["post"]["_id"] == "post_thread"
    req = respx.calls.last.request
    body = json.loads(req.content)
    assert body["content"] == ""
    assert body["publishNow"] is True
    psd = body["platforms"][0]["platformSpecificData"]
    assert len(psd["threadItems"]) == 3
    assert psd["threadItems"][0]["content"] == "First tweet"
    assert psd["threadItems"][1]["mediaItems"] == [{"url": "https://img.test/1.jpg", "type": "image"}]
    assert "mediaItems" not in psd["threadItems"][0]


@respx.mock
@pytest.mark.asyncio
async def test_posts_create_thread_bluesky():
    """Thread items work for Bluesky."""
    respx.post(f"{API_BASE}/v1/posts").mock(
        return_value=httpx.Response(200, json={
            "post": {"_id": "post_bsky", "status": "draft"}
        })
    )
    result = await posts_create(
        platforms=[{"platform": "bluesky", "accountId": "b1"}],
        thread_items=[
            ThreadItem(content="Skeet one"),
            ThreadItem(content="Skeet two"),
        ],
    )
    req = respx.calls.last.request
    body = json.loads(req.content)
    psd = body["platforms"][0]["platformSpecificData"]
    assert len(psd["threadItems"]) == 2
    assert body["content"] == ""


@pytest.mark.asyncio
async def test_posts_create_thread_rejects_unsupported_platform():
    """Threads with non-twitter/bluesky platforms return an error."""
    result = await posts_create(
        platforms=[{"platform": "instagram", "accountId": "i1"}],
        thread_items=[
            ThreadItem(content="Nope"),
            ThreadItem(content="Also nope"),
        ],
    )
    assert "error" in result
    assert "instagram" in result["error"]


@pytest.mark.asyncio
async def test_posts_create_thread_rejects_content():
    """Threads with top-level content return an error."""
    result = await posts_create(
        content="This should fail",
        platforms=[{"platform": "twitter", "accountId": "a1"}],
        thread_items=[
            ThreadItem(content="First"),
            ThreadItem(content="Second"),
        ],
    )
    assert "error" in result
    assert "mutually exclusive" in result["error"]


@pytest.mark.asyncio
async def test_posts_create_thread_rejects_media_items():
    """Threads with top-level media_items return an error."""
    result = await posts_create(
        platforms=[{"platform": "twitter", "accountId": "a1"}],
        media_items=[MediaItem(url="https://img.test/1.jpg", type="image")],
        thread_items=[
            ThreadItem(content="First"),
            ThreadItem(content="Second"),
        ],
    )
    assert "error" in result
    assert "mutually exclusive" in result["error"]


@pytest.mark.asyncio
async def test_posts_create_thread_rejects_too_few_items():
    """Single-item thread_items returns an error (min 2 required)."""
    result = await posts_create(
        platforms=[{"platform": "twitter", "accountId": "a1"}],
        thread_items=[ThreadItem(content="Only one")],
    )
    assert "error" in result
    assert "at least 2" in result["error"]


@pytest.mark.asyncio
async def test_posts_create_thread_rejects_too_many_items():
    """More than 25 thread_items returns an error."""
    result = await posts_create(
        platforms=[{"platform": "twitter", "accountId": "a1"}],
        thread_items=[ThreadItem(content=f"Item {i}") for i in range(26)],
    )
    assert "error" in result
    assert "25" in result["error"]


@respx.mock
@pytest.mark.asyncio
async def test_posts_create_thread_cross_post():
    """Thread cross-posted to both Twitter and Bluesky."""
    respx.post(f"{API_BASE}/v1/posts").mock(
        return_value=httpx.Response(200, json={
            "post": {"_id": "post_cross", "status": "published"}
        })
    )
    result = await posts_create(
        platforms=[
            {"platform": "twitter", "accountId": "a1"},
            {"platform": "bluesky", "accountId": "b1"},
        ],
        publish_now=True,
        thread_items=[
            ThreadItem(content="Thread post 1"),
            ThreadItem(content="Thread post 2"),
        ],
    )
    req = respx.calls.last.request
    body = json.loads(req.content)
    for p in body["platforms"]:
        assert "threadItems" in p["platformSpecificData"]
        assert len(p["platformSpecificData"]["threadItems"]) == 2
