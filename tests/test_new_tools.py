"""Tests for all new tools (P0-P3 expansion)."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

API = "https://zernio.com/api"


# ── P0: Queue ──────────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_queue_create_slot():
    from zernio_mcp.tools.queue import queue_create_slot
    respx.post(f"{API}/v1/queue/slots").mock(return_value=httpx.Response(200, json={"slot": {"_id": "s1"}}))
    result = await queue_create_slot(profile_id="p1", name="Morning Post", day="monday", time="09:00", platform="twitter")
    assert result["slot"]["_id"] == "s1"


@respx.mock
@pytest.mark.asyncio
async def test_queue_list_slots():
    from zernio_mcp.tools.queue import queue_list_slots
    respx.get(f"{API}/v1/queue/slots").mock(return_value=httpx.Response(200, json={"slots": []}))
    result = await queue_list_slots()
    assert "slots" in result


@respx.mock
@pytest.mark.asyncio
async def test_queue_update_slot():
    from zernio_mcp.tools.queue import queue_update_slot
    respx.put(f"{API}/v1/queue/slots/s1").mock(return_value=httpx.Response(200, json={"updated": True}))
    result = await queue_update_slot(slot_id="s1", time="14:00")
    assert result["updated"] is True


@respx.mock
@pytest.mark.asyncio
async def test_queue_delete_slot():
    from zernio_mcp.tools.queue import queue_delete_slot
    respx.delete(f"{API}/v1/queue/slots/s1").mock(return_value=httpx.Response(200, json={"deleted": True}))
    result = await queue_delete_slot(slot_id="s1")
    assert result["deleted"] is True


@respx.mock
@pytest.mark.asyncio
async def test_queue_next_slot():
    from zernio_mcp.tools.queue import queue_next_slot
    respx.get(f"{API}/v1/queue/next-slot").mock(return_value=httpx.Response(200, json={"slot": {"datetime": "2026-04-01T09:00:00Z"}}))
    result = await queue_next_slot(profile_id="p1")
    assert "slot" in result


# ── P0: Posts Extended ─────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_posts_update():
    from zernio_mcp.tools.posts import posts_update
    respx.put(f"{API}/v1/posts/post1").mock(return_value=httpx.Response(200, json={"post": {"_id": "post1", "content": "updated"}}))
    result = await posts_update(post_id="post1", content="updated")
    assert result["post"]["content"] == "updated"


@respx.mock
@pytest.mark.asyncio
async def test_posts_bulk_upload():
    from zernio_mcp.tools.posts import posts_bulk_upload
    respx.post(f"{API}/v1/posts/bulk-upload").mock(return_value=httpx.Response(200, json={"created": 5, "failed": 0}))
    result = await posts_bulk_upload(csv_content="content,platform\nHello,twitter")
    assert result["created"] == 5


# ── P0: Validation ─────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_validate_post_length():
    from zernio_mcp.tools.validation import validate_post_length
    respx.post(f"{API}/v1/tools/validate/post-length").mock(return_value=httpx.Response(200, json={"valid": True, "remaining": 200}))
    result = await validate_post_length(content="Hello", platform="twitter")
    assert result["valid"] is True


@respx.mock
@pytest.mark.asyncio
async def test_validate_post():
    from zernio_mcp.tools.validation import validate_post
    respx.post(f"{API}/v1/tools/validate/post").mock(return_value=httpx.Response(200, json={"valid": True}))
    result = await validate_post(content="Hello", platforms=[{"platform": "twitter", "accountId": "a1"}])
    assert result["valid"] is True


@respx.mock
@pytest.mark.asyncio
async def test_validate_media():
    from zernio_mcp.tools.validation import validate_media
    respx.post(f"{API}/v1/tools/validate/media").mock(return_value=httpx.Response(200, json={"valid": True}))
    result = await validate_media(media_url="https://example.com/img.jpg", platform="instagram")
    assert result["valid"] is True


# ── P1: Profiles ───────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_profiles_create():
    from zernio_mcp.tools.profiles import profiles_create
    respx.post(f"{API}/v1/profiles").mock(return_value=httpx.Response(200, json={"_id": "p1"}))
    result = await profiles_create(name="Test Brand")
    assert result["_id"] == "p1"


@respx.mock
@pytest.mark.asyncio
async def test_profiles_get():
    from zernio_mcp.tools.profiles import profiles_get
    respx.get(f"{API}/v1/profiles/p1").mock(return_value=httpx.Response(200, json={"_id": "p1", "name": "Test"}))
    result = await profiles_get(profile_id="p1")
    assert result["name"] == "Test"


@respx.mock
@pytest.mark.asyncio
async def test_profiles_update():
    from zernio_mcp.tools.profiles import profiles_update
    respx.put(f"{API}/v1/profiles/p1").mock(return_value=httpx.Response(200, json={"updated": True}))
    result = await profiles_update(profile_id="p1", name="New Name")
    assert result["updated"] is True


@respx.mock
@pytest.mark.asyncio
async def test_profiles_delete():
    from zernio_mcp.tools.profiles import profiles_delete
    respx.delete(f"{API}/v1/profiles/p1").mock(return_value=httpx.Response(200, json={"deleted": True}))
    result = await profiles_delete(profile_id="p1")
    assert result["deleted"] is True


# ── P1: Account Management ────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_accounts_update():
    from zernio_mcp.tools.accounts import accounts_update
    respx.put(f"{API}/v1/accounts/a1").mock(return_value=httpx.Response(200, json={"updated": True}))
    result = await accounts_update(account_id="a1", settings={"key": "value"})
    assert result["updated"] is True


@respx.mock
@pytest.mark.asyncio
async def test_accounts_delete():
    from zernio_mcp.tools.accounts import accounts_delete
    respx.delete(f"{API}/v1/accounts/a1").mock(return_value=httpx.Response(200, json={"deleted": True}))
    result = await accounts_delete(account_id="a1")
    assert result["deleted"] is True


@respx.mock
@pytest.mark.asyncio
async def test_accounts_follower_stats():
    from zernio_mcp.tools.accounts import accounts_follower_stats
    respx.get(f"{API}/v1/accounts/follower-stats").mock(return_value=httpx.Response(200, json={"stats": []}))
    result = await accounts_follower_stats()
    assert "stats" in result


@respx.mock
@pytest.mark.asyncio
async def test_accounts_health_single():
    from zernio_mcp.tools.accounts import accounts_health
    respx.get(f"{API}/v1/accounts/a1/health").mock(return_value=httpx.Response(200, json={"status": "healthy"}))
    result = await accounts_health(account_id="a1")
    assert result["accounts"][0]["status"] == "healthy"


# ── P1: Content Research ──────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_research_download_youtube():
    from zernio_mcp.tools.research import research_download_post
    respx.get(f"{API}/v1/tools/youtube/download").mock(return_value=httpx.Response(200, json={"title": "Video"}))
    result = await research_download_post(url="https://www.youtube.com/watch?v=abc")
    assert result["title"] == "Video"


@respx.mock
@pytest.mark.asyncio
async def test_research_download_twitter():
    from zernio_mcp.tools.research import research_download_post
    respx.get(f"{API}/v1/tools/twitter/download").mock(return_value=httpx.Response(200, json={"text": "tweet"}))
    result = await research_download_post(url="https://x.com/user/status/123")
    assert result["text"] == "tweet"


@respx.mock
@pytest.mark.asyncio
async def test_research_download_instagram():
    from zernio_mcp.tools.research import research_download_post
    respx.get(f"{API}/v1/tools/instagram/download").mock(return_value=httpx.Response(200, json={"caption": "post"}))
    result = await research_download_post(url="https://www.instagram.com/p/abc123/")
    assert result["caption"] == "post"


@pytest.mark.asyncio
async def test_research_download_unknown_platform():
    from zernio_mcp.tools.research import research_download_post
    result = await research_download_post(url="https://unknown-site.com/post/123")
    assert "error" in result


@respx.mock
@pytest.mark.asyncio
async def test_youtube_transcript():
    from zernio_mcp.tools.research import youtube_transcript
    respx.get(f"{API}/v1/tools/youtube/transcript").mock(return_value=httpx.Response(200, json={"transcript": "hello world"}))
    result = await youtube_transcript(url="https://youtube.com/watch?v=abc")
    assert result["transcript"] == "hello world"


@respx.mock
@pytest.mark.asyncio
async def test_instagram_hashtag():
    from zernio_mcp.tools.research import instagram_hashtag
    respx.post(f"{API}/v1/tools/instagram/hashtag-checker").mock(return_value=httpx.Response(200, json={"count": 1000}))
    result = await instagram_hashtag(hashtag="coding")
    assert result["count"] == 1000


@respx.mock
@pytest.mark.asyncio
async def test_reddit_subreddit_rules():
    from zernio_mcp.tools.research import reddit_subreddit_rules
    respx.get(f"{API}/v1/tools/validate/subreddit").mock(return_value=httpx.Response(200, json={"rules": []}))
    result = await reddit_subreddit_rules(subreddit="python")
    assert "rules" in result


# ── P1: Platform Analytics ─────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_analytics_youtube_daily():
    from zernio_mcp.tools.analytics import analytics_youtube_daily
    respx.get(f"{API}/v1/analytics/youtube/daily-views").mock(return_value=httpx.Response(200, json={"views": []}))
    result = await analytics_youtube_daily(account_id="a1")
    assert "views" in result


@respx.mock
@pytest.mark.asyncio
async def test_analytics_instagram_with_demographics():
    from zernio_mcp.tools.analytics import analytics_instagram
    respx.get(f"{API}/v1/analytics/instagram/account-insights").mock(return_value=httpx.Response(200, json={"reach": 100}))
    respx.get(f"{API}/v1/analytics/instagram/demographics").mock(return_value=httpx.Response(200, json={"ages": []}))
    result = await analytics_instagram(account_id="a1", include_demographics=True)
    assert result["reach"] == 100
    assert "demographics" in result


@respx.mock
@pytest.mark.asyncio
async def test_analytics_instagram_without_demographics():
    from zernio_mcp.tools.analytics import analytics_instagram
    respx.get(f"{API}/v1/analytics/instagram/account-insights").mock(return_value=httpx.Response(200, json={"reach": 100}))
    result = await analytics_instagram(account_id="a1", include_demographics=False)
    assert result["reach"] == 100
    assert "demographics" not in result


# ── P1: Platform Helpers ───────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_reddit_search():
    from zernio_mcp.tools.platform_helpers import reddit_search
    respx.get(f"{API}/v1/reddit/search").mock(return_value=httpx.Response(200, json={"posts": []}))
    result = await reddit_search(query="python")
    assert "posts" in result


@respx.mock
@pytest.mark.asyncio
async def test_reddit_feed():
    from zernio_mcp.tools.platform_helpers import reddit_feed
    respx.get(f"{API}/v1/reddit/feed").mock(return_value=httpx.Response(200, json={"posts": []}))
    result = await reddit_feed(subreddit="python")
    assert "posts" in result


@respx.mock
@pytest.mark.asyncio
async def test_reddit_subreddits():
    from zernio_mcp.tools.platform_helpers import reddit_subreddits
    respx.get(f"{API}/v1/accounts/a1/reddit-subreddits").mock(return_value=httpx.Response(200, json={"subreddits": []}))
    result = await reddit_subreddits(account_id="a1")
    assert "subreddits" in result


@respx.mock
@pytest.mark.asyncio
async def test_reddit_flairs():
    from zernio_mcp.tools.platform_helpers import reddit_flairs
    respx.get(f"{API}/v1/accounts/a1/reddit-flairs").mock(return_value=httpx.Response(200, json={"flairs": []}))
    result = await reddit_flairs(account_id="a1", subreddit="python")
    assert "flairs" in result


@respx.mock
@pytest.mark.asyncio
async def test_linkedin_mentions():
    from zernio_mcp.tools.platform_helpers import linkedin_mentions
    respx.get(f"{API}/v1/accounts/a1/linkedin-mentions").mock(return_value=httpx.Response(200, json={"mentions": []}))
    result = await linkedin_mentions(account_id="a1")
    assert "mentions" in result


@respx.mock
@pytest.mark.asyncio
async def test_linkedin_org_analytics():
    from zernio_mcp.tools.platform_helpers import linkedin_org_analytics
    respx.get(f"{API}/v1/accounts/a1/linkedin-aggregate-analytics").mock(return_value=httpx.Response(200, json={"followers": 100}))
    result = await linkedin_org_analytics(account_id="a1")
    assert result["followers"] == 100


@respx.mock
@pytest.mark.asyncio
async def test_pinterest_boards():
    from zernio_mcp.tools.platform_helpers import pinterest_boards
    respx.get(f"{API}/v1/accounts/a1/pinterest-boards").mock(return_value=httpx.Response(200, json={"boards": []}))
    result = await pinterest_boards(account_id="a1")
    assert "boards" in result


@respx.mock
@pytest.mark.asyncio
async def test_youtube_playlists():
    from zernio_mcp.tools.platform_helpers import youtube_playlists
    respx.get(f"{API}/v1/accounts/a1/youtube-playlists").mock(return_value=httpx.Response(200, json={"playlists": []}))
    result = await youtube_playlists(account_id="a1")
    assert "playlists" in result


# ── P2: Inbox ──────────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_inbox_list():
    from zernio_mcp.tools.inbox import inbox_list
    respx.get(f"{API}/v1/inbox/conversations").mock(return_value=httpx.Response(200, json={"conversations": []}))
    result = await inbox_list()
    assert "conversations" in result


@respx.mock
@pytest.mark.asyncio
async def test_inbox_get_conversation_with_messages():
    from zernio_mcp.tools.inbox import inbox_get_conversation
    respx.get(f"{API}/v1/inbox/conversations/c1").mock(return_value=httpx.Response(200, json={"_id": "c1"}))
    respx.get(f"{API}/v1/inbox/conversations/c1/messages").mock(return_value=httpx.Response(200, json={"messages": [{"text": "hi"}]}))
    result = await inbox_get_conversation(conversation_id="c1")
    assert result["_id"] == "c1"
    assert len(result["messages"]) == 1


@respx.mock
@pytest.mark.asyncio
async def test_inbox_messages_send():
    from zernio_mcp.tools.inbox import inbox_messages_send
    respx.post(f"{API}/v1/inbox/conversations/c1/messages").mock(return_value=httpx.Response(200, json={"sent": True}))
    result = await inbox_messages_send(conversation_id="c1", content="Hello!")
    assert result["sent"] is True


@respx.mock
@pytest.mark.asyncio
async def test_inbox_message_edit():
    from zernio_mcp.tools.inbox import inbox_message_edit
    respx.patch(f"{API}/v1/inbox/conversations/c1/messages/m1").mock(return_value=httpx.Response(200, json={"updated": True}))
    result = await inbox_message_edit(conversation_id="c1", message_id="m1", content="edited")
    assert result["updated"] is True


@respx.mock
@pytest.mark.asyncio
async def test_inbox_message_delete():
    from zernio_mcp.tools.inbox import inbox_message_delete
    respx.delete(f"{API}/v1/inbox/conversations/c1/messages/m1").mock(return_value=httpx.Response(200, json={"deleted": True}))
    result = await inbox_message_delete(conversation_id="c1", message_id="m1")
    assert result["deleted"] is True


# ── P2: Comments ───────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_comments_list_all():
    from zernio_mcp.tools.comments import comments_list
    respx.get(f"{API}/v1/inbox/comments").mock(return_value=httpx.Response(200, json={"comments": []}))
    result = await comments_list()
    assert "comments" in result


@respx.mock
@pytest.mark.asyncio
async def test_comments_list_for_post():
    from zernio_mcp.tools.comments import comments_list
    respx.get(f"{API}/v1/inbox/comments/post1").mock(return_value=httpx.Response(200, json={"comments": [{"text": "nice"}]}))
    result = await comments_list(post_id="post1")
    assert len(result["comments"]) == 1


@respx.mock
@pytest.mark.asyncio
async def test_comments_reply():
    from zernio_mcp.tools.comments import comments_reply
    respx.post(f"{API}/v1/inbox/comments/post1").mock(return_value=httpx.Response(200, json={"replied": True}))
    result = await comments_reply(post_id="post1", comment_id="c1", content="thanks!")
    assert result["replied"] is True


@respx.mock
@pytest.mark.asyncio
async def test_comments_hide():
    from zernio_mcp.tools.comments import comments_hide
    respx.post(f"{API}/v1/inbox/comments/post1/c1/hide").mock(return_value=httpx.Response(200, json={"hidden": True}))
    result = await comments_hide(post_id="post1", comment_id="c1")
    assert result["hidden"] is True


# ── P2: Twitter ────────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_twitter_retweet():
    from zernio_mcp.tools.twitter import twitter_retweet
    respx.post(f"{API}/v1/twitter/retweet").mock(return_value=httpx.Response(200, json={"retweeted": True}))
    result = await twitter_retweet(account_id="a1", tweet_id="t1")
    assert result["retweeted"] is True


@respx.mock
@pytest.mark.asyncio
async def test_twitter_bookmark():
    from zernio_mcp.tools.twitter import twitter_bookmark
    respx.post(f"{API}/v1/twitter/bookmark").mock(return_value=httpx.Response(200, json={"bookmarked": True}))
    result = await twitter_bookmark(account_id="a1", tweet_id="t1")
    assert result["bookmarked"] is True


# ── P2: Reviews ────────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_reviews_list():
    from zernio_mcp.tools.reviews import reviews_list
    respx.get(f"{API}/v1/inbox/reviews").mock(return_value=httpx.Response(200, json={"reviews": []}))
    result = await reviews_list()
    assert "reviews" in result


@respx.mock
@pytest.mark.asyncio
async def test_reviews_reply():
    from zernio_mcp.tools.reviews import reviews_reply
    respx.post(f"{API}/v1/inbox/reviews/r1/reply").mock(return_value=httpx.Response(200, json={"replied": True}))
    result = await reviews_reply(review_id="r1", content="Thank you!")
    assert result["replied"] is True


# ── P2: Logs ───────────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_logs_posts():
    from zernio_mcp.tools.logs import logs_posts
    respx.get(f"{API}/v1/posts/logs").mock(return_value=httpx.Response(200, json={"logs": []}))
    result = await logs_posts()
    assert "logs" in result


@respx.mock
@pytest.mark.asyncio
async def test_logs_post_detail():
    from zernio_mcp.tools.logs import logs_post_detail
    respx.get(f"{API}/v1/posts/post1/logs").mock(return_value=httpx.Response(200, json={"logs": []}))
    result = await logs_post_detail(post_id="post1")
    assert "logs" in result


@respx.mock
@pytest.mark.asyncio
async def test_logs_connections():
    from zernio_mcp.tools.logs import logs_connections
    respx.get(f"{API}/v1/connections/logs").mock(return_value=httpx.Response(200, json={"logs": []}))
    result = await logs_connections()
    assert "logs" in result


# ── P2: Webhooks ───────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_webhooks_get():
    from zernio_mcp.tools.webhooks import webhooks_get
    respx.get(f"{API}/v1/webhooks/settings").mock(return_value=httpx.Response(200, json={"url": "https://example.com"}))
    result = await webhooks_get()
    assert result["url"] == "https://example.com"


@respx.mock
@pytest.mark.asyncio
async def test_webhooks_create():
    from zernio_mcp.tools.webhooks import webhooks_create
    respx.post(f"{API}/v1/webhooks/settings").mock(return_value=httpx.Response(200, json={"created": True}))
    result = await webhooks_create(url="https://example.com/hook", events=["post.published"])
    assert result["created"] is True


@respx.mock
@pytest.mark.asyncio
async def test_webhooks_test():
    from zernio_mcp.tools.webhooks import webhooks_test
    respx.post(f"{API}/v1/webhooks/test").mock(return_value=httpx.Response(200, json={"sent": True}))
    result = await webhooks_test()
    assert result["sent"] is True


@respx.mock
@pytest.mark.asyncio
async def test_webhooks_logs():
    from zernio_mcp.tools.webhooks import webhooks_logs
    respx.get(f"{API}/v1/webhooks/logs").mock(return_value=httpx.Response(200, json={"logs": []}))
    result = await webhooks_logs()
    assert "logs" in result


# ── P3: Broadcasts ─────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_broadcasts_list():
    from zernio_mcp.tools.broadcasts import broadcasts_list
    respx.get(f"{API}/v1/broadcasts").mock(return_value=httpx.Response(200, json={"broadcasts": []}))
    result = await broadcasts_list()
    assert "broadcasts" in result


@respx.mock
@pytest.mark.asyncio
async def test_broadcasts_create():
    from zernio_mcp.tools.broadcasts import broadcasts_create
    respx.post(f"{API}/v1/broadcasts").mock(return_value=httpx.Response(200, json={"_id": "b1"}))
    result = await broadcasts_create(name="Test", content="Hello!", account_ids=["a1"])
    assert result["_id"] == "b1"


@respx.mock
@pytest.mark.asyncio
async def test_broadcasts_delete():
    from zernio_mcp.tools.broadcasts import broadcasts_delete
    respx.delete(f"{API}/v1/broadcasts/b1").mock(return_value=httpx.Response(200, json={"deleted": True}))
    result = await broadcasts_delete(broadcast_id="b1")
    assert result["deleted"] is True


# ── P3: Contacts ───────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_contacts_list():
    from zernio_mcp.tools.contacts import contacts_list
    respx.get(f"{API}/v1/contacts").mock(return_value=httpx.Response(200, json={"contacts": []}))
    result = await contacts_list()
    assert "contacts" in result


@respx.mock
@pytest.mark.asyncio
async def test_contacts_create():
    from zernio_mcp.tools.contacts import contacts_create
    respx.post(f"{API}/v1/contacts").mock(return_value=httpx.Response(200, json={"_id": "c1"}))
    result = await contacts_create(name="John Doe")
    assert result["_id"] == "c1"


@respx.mock
@pytest.mark.asyncio
async def test_contacts_delete():
    from zernio_mcp.tools.contacts import contacts_delete
    respx.delete(f"{API}/v1/contacts/c1").mock(return_value=httpx.Response(200, json={"deleted": True}))
    result = await contacts_delete(contact_id="c1")
    assert result["deleted"] is True


# ── P3: Misc ───────────────────────────────────────────────────

@respx.mock
@pytest.mark.asyncio
async def test_usage_stats():
    from zernio_mcp.tools.misc import usage_stats
    respx.get(f"{API}/v1/usage-stats").mock(return_value=httpx.Response(200, json={"posts": 42}))
    result = await usage_stats()
    assert result["posts"] == 42


@respx.mock
@pytest.mark.asyncio
async def test_account_groups_list():
    from zernio_mcp.tools.misc import account_groups_list
    respx.get(f"{API}/v1/account-groups").mock(return_value=httpx.Response(200, json={"groups": []}))
    result = await account_groups_list()
    assert "groups" in result


@respx.mock
@pytest.mark.asyncio
async def test_account_groups_create():
    from zernio_mcp.tools.misc import account_groups_create
    respx.post(f"{API}/v1/account-groups").mock(return_value=httpx.Response(200, json={"_id": "g1"}))
    result = await account_groups_create(name="Group A", account_ids=["a1"])
    assert result["_id"] == "g1"


@respx.mock
@pytest.mark.asyncio
async def test_account_groups_delete():
    from zernio_mcp.tools.misc import account_groups_delete
    respx.delete(f"{API}/v1/account-groups/g1").mock(return_value=httpx.Response(200, json={"deleted": True}))
    result = await account_groups_delete(group_id="g1")
    assert result["deleted"] is True
