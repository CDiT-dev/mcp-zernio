## Context

The mcp-zernio server is deployed and working with 13 tools. This change adds ~80+ more tools covering P0-P3 of the Zernio API. The server already has a shared httpx client with connection pooling, TTL caching, async SSRF validation, and the Stolperstein auth pattern. All new tools follow the exact same pattern as existing ones.

## Goals / Non-Goals

**Goals:**
- Add ~80 tools covering P0 (queue, posts, validation), P1 (profiles, accounts, content research, analytics, platform helpers), P2 (inbox, comments, engagement, logs, webhooks), and P3 (broadcasts, contacts, usage, groups)
- Add `put` and `patch` methods to ZernioClient
- Split server.py into tool modules at this scale (~95 tools total)
- Unit test every new tool with respx mocks
- Smoke test key endpoints per phase against real API
- Keep ToolAnnotations on every tool

**Non-Goals:**
- WhatsApp Business API (20+ endpoints — separate concern)
- Sequences / drip automation (complex workflow, not suited for MCP)
- Comment automations (rule-based, better managed in Zernio UI)
- OAuth connection flows (doesn't make sense in MCP)
- Changing auth, deployment, or infrastructure

## Decisions

### 1. Add PUT and PATCH methods to ZernioClient

```python
async def put(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    return await self._request("PUT", path, json_body=body)

async def patch(self, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    return await self._request("PATCH", path, json_body=body)
```

### 2. Split server.py into tool modules

At ~95 tools, a flat server.py is unwieldy. Split into modules per capability:

```
src/zernio_mcp/
├── server.py              # FastMCP instance, lifespan, main() — imports all tool modules
├── client.py              # ZernioClient (unchanged except put/patch)
├── config.py              # Settings (unchanged)
├── auth.py                # Auth (unchanged)
└── tools/
    ├── __init__.py         # registers all tool modules with the mcp instance
    ├── accounts.py         # accounts_list, accounts_health, accounts_update, accounts_delete, accounts_follower_stats, accounts_health_single
    ├── profiles.py         # profiles_list, profiles_create, profiles_get, profiles_update, profiles_delete
    ├── posts.py            # posts_create, posts_get, posts_list, posts_delete, posts_unpublish, posts_retry, posts_update, posts_bulk_upload
    ├── media.py            # media_upload, media_upload_direct
    ├── queue.py            # queue_preview, queue_create_slot, queue_list_slots, queue_update_slot, queue_delete_slot, queue_next_slot
    ├── analytics.py        # analytics_posts, analytics_insights, analytics_youtube_daily, analytics_instagram_insights, analytics_instagram_demographics, analytics_post_timeline
    ├── validation.py       # validate_post_length, validate_post, validate_media
    ├── content_research.py # tool_*_download (7), tool_youtube_transcript, tool_instagram_hashtag, validate_subreddit
    ├── platform_helpers.py # reddit_*, linkedin_*, pinterest_boards, youtube_playlists
    ├── inbox.py            # inbox_list, inbox_get, inbox_update, inbox_messages_list, inbox_messages_send, inbox_message_edit, inbox_message_delete, inbox_typing, inbox_react
    ├── comments.py         # comments_list, comments_list_post, comments_reply, comments_delete, comments_hide, comments_like, comments_private_reply
    ├── twitter.py          # twitter_retweet, twitter_unretweet, twitter_bookmark, twitter_follow
    ├── reviews.py          # reviews_list, reviews_reply
    ├── logs.py             # logs_posts, logs_post_detail, logs_connections
    ├── webhooks.py         # webhooks_get, webhooks_create, webhooks_update, webhooks_delete, webhooks_test, webhooks_logs
    ├── broadcasts.py       # broadcasts_list, broadcasts_create, broadcasts_get, broadcasts_update, broadcasts_delete
    ├── contacts.py         # contacts_list, contacts_create, contacts_get, contacts_update, contacts_delete
    └── misc.py             # usage_stats, account_groups_list, account_groups_create, account_groups_delete
```

Each module imports `mcp` from `server.py` and registers its tools with `@mcp.tool()`. The `tools/__init__.py` imports all modules to trigger registration.

### 3. Content download tools: unified naming pattern

All platform download tools follow `tool_{platform}_download` naming with identical docstring pattern:

"Download post information from {platform}. Accepts a post URL and returns metadata including content, media URLs, engagement metrics, and author info."

### 4. Test strategy

- **Unit tests**: One test per tool minimum, using respx mocks. Organized by module (`tests/test_accounts.py`, `tests/test_posts.py`, etc.)
- **Smoke tests**: Expand `test_smoke.py` to cover key endpoints per phase: queue_list_slots (P0), accounts_follower_stats (P1), inbox_list (P2), contacts_list (P3)
- **Cache**: Add `accounts_follower_stats` and `contacts_list` to the 60s TTL cache

### 5. CRUD pattern consistency

All CRUD groups (profiles, contacts, broadcasts, account_groups) follow the same pattern:
- `{noun}_list` — GET collection, paginated
- `{noun}_create` — POST
- `{noun}_get` — GET by ID
- `{noun}_update` — PUT by ID
- `{noun}_delete` — DELETE by ID

## Risks / Trade-offs

### [95 tools is a very large surface] → Module split + good naming mitigates
Claude.ai handles large tool surfaces well when naming is consistent. The `noun_verb` pattern and module grouping keep it navigable. ToolAnnotations clearly signal read vs write.

### [Inbox/DM tools can send messages to real people] → Same draft-default pattern
Write tools that send messages (inbox_messages_send, comments_reply, comments_private_reply) need clear docstrings warning Claude to confirm content with the user before sending.

### [Twitter engagement tools are one-way actions] → Docstring warnings
Retweet, follow, bookmark are publicly visible actions. Docstrings must instruct Claude to confirm before executing.
