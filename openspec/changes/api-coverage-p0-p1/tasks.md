## 0. Architecture Refactor

- [ ] 0.1 Create `src/zernio_mcp/tools/` package with `__init__.py`
- [ ] 0.2 Move existing 13 tools from server.py into tool modules (accounts.py, posts.py, media.py, analytics.py, queue.py)
- [ ] 0.3 Update server.py to import tool modules via `tools/__init__.py`
- [ ] 0.4 Add `put` and `patch` methods to `ZernioClient` in client.py
- [ ] 0.5 Add `cache_invalidate(key)` function to client.py — call in write tools that affect cached data (profiles, queue)
- [ ] 0.6 Verify existing 37 tests still pass after refactor

## 1. P0 — Queue CRUD (5 tools → tools/queue.py)

- [ ] 1.1 Implement `queue_create_slot`: `POST /v1/queue/slots`, invalidate queue cache, ToolAnnotations(Write, not idempotent)
- [ ] 1.2 Implement `queue_list_slots`: `GET /v1/queue/slots`, cached 60s by profile_id, ToolAnnotations(RO, idempotent)
- [ ] 1.3 Implement `queue_update_slot`: `PUT /v1/queue/slots`, invalidate queue cache, ToolAnnotations(Write, idempotent)
- [ ] 1.4 Implement `queue_delete_slot`: `DELETE /v1/queue/slots`, invalidate queue cache, ToolAnnotations(Write, idempotent)
- [ ] 1.5 Implement `queue_next_slot`: `GET /v1/queue/next-slot`, cached 60s by profile_id, ToolAnnotations(RO, idempotent)
- [ ] 1.6 Unit tests for all 5 queue tools including cache invalidation

## 2. P0 — Posts Extended (2 tools → tools/posts.py)

- [ ] 2.1 Implement `posts_update`: `PUT /v1/posts/{postId}`, ToolAnnotations(Write, idempotent)
- [ ] 2.2 Implement `posts_bulk_upload`: `POST /v1/posts/bulk-upload`, docstring: "use for 5+ posts; for fewer use posts_create", ToolAnnotations(Write, not idempotent)
- [ ] 2.3 Unit tests for posts_update and posts_bulk_upload

## 3. P0 — Validation Tools (3 tools → tools/validation.py)

- [ ] 3.1 Implement `validate_post_length`: `POST /v1/tools/validate/post-length`, docstring: "fast text-only check", ToolAnnotations(RO, idempotent)
- [ ] 3.2 Implement `validate_post`: `POST /v1/tools/validate/post`, docstring: "full pre-flight incl. media + platform config", ToolAnnotations(RO, idempotent)
- [ ] 3.3 Implement `validate_media`: `POST /v1/tools/validate/media`, ToolAnnotations(RO, idempotent)
- [ ] 3.4 Unit tests for all 3 validation tools

## 4. P1 — Profile CRUD (4 tools → tools/profiles.py)

- [ ] 4.1 Implement `profiles_create`: `POST /v1/profiles`, invalidate profiles_list cache, ToolAnnotations(Write, not idempotent)
- [ ] 4.2 Implement `profiles_get`: `GET /v1/profiles/{profileId}`, ToolAnnotations(RO, idempotent)
- [ ] 4.3 Implement `profiles_update`: `PUT /v1/profiles/{profileId}`, invalidate profiles_list cache, ToolAnnotations(Write, idempotent)
- [ ] 4.4 Implement `profiles_delete`: `DELETE /v1/profiles/{profileId}`, invalidate profiles_list cache, ToolAnnotations(Write, idempotent)
- [ ] 4.5 Unit tests for all 4 profile CRUD tools incl. cache invalidation

## 5. P1 — Account Management (3 tools → tools/accounts.py)

- [ ] 5.1 Implement `accounts_update`: `PUT /v1/accounts/{accountId}`, invalidate accounts_list cache, ToolAnnotations(Write, idempotent)
- [ ] 5.2 Implement `accounts_delete`: `DELETE /v1/accounts/{accountId}`, invalidate accounts_list cache, ToolAnnotations(Write, idempotent)
- [ ] 5.3 Implement `accounts_follower_stats`: `GET /v1/accounts/follower-stats`, cached 60s, ToolAnnotations(RO, idempotent)
- [ ] 5.4 Merge `accounts_health_single` into existing `accounts_health(account_id: str | None = None)` — optional param routes to `/v1/accounts/{accountId}/health` when given
- [ ] 5.5 Unit tests for all account management changes

## 6. P1 — Content Research (4 tools → tools/research.py)

- [ ] 6.1 Implement `research_download_post`: single tool that auto-detects platform from URL, routes to `/v1/tools/{platform}/download`. Supports YouTube, Instagram, TikTok, Twitter/X, Facebook, LinkedIn, Bluesky. ToolAnnotations(RO, idempotent)
- [ ] 6.2 Implement `youtube_transcript`: `GET /v1/tools/youtube/transcript`, ToolAnnotations(RO, idempotent)
- [ ] 6.3 Implement `instagram_hashtag`: `POST /v1/tools/instagram/hashtag-checker`, ToolAnnotations(RO, idempotent)
- [ ] 6.4 Implement `reddit_subreddit_rules`: `GET /v1/tools/validate/subreddit`, ToolAnnotations(RO, idempotent)
- [ ] 6.5 Unit tests for all 4 content research tools (research_download_post tested with multiple platform URLs)

## 7. P1 — Platform Analytics (3 tools → tools/analytics.py)

- [ ] 7.1 Implement `analytics_youtube_daily`: `GET /v1/analytics/youtube/daily-views`, ToolAnnotations(RO, idempotent)
- [ ] 7.2 Implement `analytics_instagram`: merged insights + demographics — calls both `/v1/analytics/instagram/account-insights` and `/v1/analytics/instagram/demographics` (when include_demographics=True), returns combined result. Cached 300s for demographics. ToolAnnotations(RO, idempotent)
- [ ] 7.3 Update `analytics_posts` docstring to make post_id→timeline branch explicit (NO new tool — `analytics_post_timeline` is already covered)
- [ ] 7.4 Unit tests for analytics_youtube_daily and analytics_instagram

## 8. P1 — Platform Helpers (8 tools → tools/platform_helpers.py)

- [ ] 8.1 Implement `reddit_search`: `GET /v1/reddit/search`, ToolAnnotations(RO, idempotent)
- [ ] 8.2 Implement `reddit_feed`: `GET /v1/reddit/feed`, ToolAnnotations(RO, idempotent)
- [ ] 8.3 Implement `reddit_subreddits`: `GET /v1/accounts/{accountId}/reddit-subreddits`, cached 60s, ToolAnnotations(RO, idempotent)
- [ ] 8.4 Implement `reddit_flairs`: `GET /v1/accounts/{accountId}/reddit-flairs`, cached 60s, ToolAnnotations(RO, idempotent)
- [ ] 8.5 Implement `linkedin_mentions`: `GET /v1/accounts/{accountId}/linkedin-mentions`, ToolAnnotations(RO, idempotent)
- [ ] 8.6 Implement `linkedin_org_analytics`: `GET /v1/accounts/{accountId}/linkedin-aggregate-analytics`, cached 300s, ToolAnnotations(RO, idempotent)
- [ ] 8.7 Implement `pinterest_boards`: `GET /v1/accounts/{accountId}/pinterest-boards`, cached 60s, ToolAnnotations(RO, idempotent)
- [ ] 8.8 Implement `youtube_playlists`: `GET /v1/accounts/{accountId}/youtube-playlists`, cached 60s, ToolAnnotations(RO, idempotent)
- [ ] 8.9 Unit tests for all 8 platform helpers

## 9. P2 — Inbox / Conversations (7 tools → tools/inbox.py)

- [ ] 9.1 Implement `inbox_list`: `GET /v1/inbox/conversations`, ToolAnnotations(RO, idempotent)
- [ ] 9.2 Implement `inbox_get_conversation`: merged get+messages — `GET /v1/inbox/conversations/{id}` + `GET .../messages` when include_messages=True (default). Single call returns full context. ToolAnnotations(RO, idempotent)
- [ ] 9.3 Implement `inbox_update`: `PUT /v1/inbox/conversations/{id}`, ToolAnnotations(Write, idempotent)
- [ ] 9.4 Implement `inbox_messages_send`: `POST /v1/inbox/conversations/{id}/messages`, docstring: "confirm message content with user before sending", ToolAnnotations(Write, not idempotent)
- [ ] 9.5 Implement `inbox_message_edit`: `PATCH /v1/inbox/conversations/{id}/messages/{mid}`, ToolAnnotations(Write, idempotent)
- [ ] 9.6 Implement `inbox_message_delete`: `DELETE /v1/inbox/conversations/{id}/messages/{mid}`, ToolAnnotations(Write, idempotent)
- [ ] 9.7 Unit tests for all 7 inbox tools (note: inbox_typing and inbox_react cut — not useful for LLM)

## 10. P2 — Comments (6 tools → tools/comments.py)

- [ ] 10.1 Implement `comments_list`: `GET /v1/inbox/comments`, with optional post_id param — when given, routes to `/v1/inbox/comments/{postId}`. Merged list+list_for_post. ToolAnnotations(RO, idempotent)
- [ ] 10.2 Implement `comments_reply`: `POST /v1/inbox/comments/{postId}`, docstring: "confirm reply with user", ToolAnnotations(Write, not idempotent)
- [ ] 10.3 Implement `comments_delete`: `DELETE /v1/inbox/comments/{postId}`, ToolAnnotations(Write, idempotent)
- [ ] 10.4 Implement `comments_hide`: `POST /v1/inbox/comments/{postId}/{commentId}/hide`, ToolAnnotations(Write, idempotent)
- [ ] 10.5 Implement `comments_like`: `POST /v1/inbox/comments/{postId}/{commentId}/like`, ToolAnnotations(Write, not idempotent)
- [ ] 10.6 Implement `comments_private_reply`: `POST /v1/inbox/comments/{postId}/{commentId}/private-reply`, docstring: "confirm with user", ToolAnnotations(Write, not idempotent)
- [ ] 10.7 Unit tests for all 6 comments tools

## 11. P2 — Twitter Engagement (4 tools → tools/twitter.py)

- [ ] 11.1 Implement `twitter_retweet`: `POST /v1/twitter/retweet`, docstring: "publicly visible action — confirm with user", ToolAnnotations(Write, not idempotent)
- [ ] 11.2 Implement `twitter_unretweet`: `DELETE /v1/twitter/retweet`, ToolAnnotations(Write, idempotent)
- [ ] 11.3 Implement `twitter_bookmark`: `POST /v1/twitter/bookmark`, ToolAnnotations(Write, not idempotent)
- [ ] 11.4 Implement `twitter_follow`: `POST /v1/twitter/follow`, docstring: "publicly visible — confirm with user", ToolAnnotations(Write, not idempotent)
- [ ] 11.5 Unit tests for all 4 twitter engagement tools

## 12. P2 — Reviews (2 tools → tools/reviews.py)

- [ ] 12.1 Implement `reviews_list`: `GET /v1/inbox/reviews`, ToolAnnotations(RO, idempotent)
- [ ] 12.2 Implement `reviews_reply`: `POST /v1/inbox/reviews/{id}/reply`, docstring: "publicly visible — confirm with user", ToolAnnotations(Write, not idempotent)
- [ ] 12.3 Unit tests for both review tools

## 13. P2 — Activity Logs (3 tools → tools/logs.py)

- [ ] 13.1 Implement `logs_posts`: `GET /v1/posts/logs`, ToolAnnotations(RO, idempotent)
- [ ] 13.2 Implement `logs_post_detail`: `GET /v1/posts/{postId}/logs`, ToolAnnotations(RO, idempotent)
- [ ] 13.3 Implement `logs_connections`: `GET /v1/connections/logs`, ToolAnnotations(RO, idempotent)
- [ ] 13.4 Unit tests for all 3 log tools

## 14. P2 — Webhooks (6 tools → tools/webhooks.py)

- [ ] 14.1 Implement `webhooks_get`: `GET /v1/webhooks/settings`, ToolAnnotations(RO, idempotent)
- [ ] 14.2 Implement `webhooks_create`: `POST /v1/webhooks/settings`, ToolAnnotations(Write, not idempotent)
- [ ] 14.3 Implement `webhooks_update`: `PUT /v1/webhooks/settings`, ToolAnnotations(Write, idempotent)
- [ ] 14.4 Implement `webhooks_delete`: `DELETE /v1/webhooks/settings`, ToolAnnotations(Write, idempotent)
- [ ] 14.5 Implement `webhooks_test`: `POST /v1/webhooks/test`, ToolAnnotations(Write, not idempotent)
- [ ] 14.6 Implement `webhooks_logs`: `GET /v1/webhooks/logs`, ToolAnnotations(RO, idempotent)
- [ ] 14.7 Unit tests for all 6 webhook tools

## 15. P3 — Broadcasts (5 tools → tools/broadcasts.py)

- [ ] 15.1 Implement `broadcasts_list`: `GET /v1/broadcasts`, ToolAnnotations(RO, idempotent)
- [ ] 15.2 Implement `broadcasts_create`: `POST /v1/broadcasts`, ToolAnnotations(Write, not idempotent)
- [ ] 15.3 Implement `broadcasts_get`: `GET /v1/broadcasts/{id}`, ToolAnnotations(RO, idempotent)
- [ ] 15.4 Implement `broadcasts_update`: `PUT /v1/broadcasts/{id}`, ToolAnnotations(Write, idempotent)
- [ ] 15.5 Implement `broadcasts_delete`: `DELETE /v1/broadcasts/{id}`, ToolAnnotations(Write, idempotent)
- [ ] 15.6 Unit tests for all 5 broadcast tools

## 16. P3 — Contacts CRM (5 tools → tools/contacts.py)

- [ ] 16.1 Implement `contacts_list`: `GET /v1/contacts`, cached 60s, ToolAnnotations(RO, idempotent)
- [ ] 16.2 Implement `contacts_create`: `POST /v1/contacts`, invalidate contacts cache, ToolAnnotations(Write, not idempotent)
- [ ] 16.3 Implement `contacts_get`: `GET /v1/contacts/{id}`, ToolAnnotations(RO, idempotent)
- [ ] 16.4 Implement `contacts_update`: `PUT /v1/contacts/{id}`, ToolAnnotations(Write, idempotent)
- [ ] 16.5 Implement `contacts_delete`: `DELETE /v1/contacts/{id}`, invalidate contacts cache, ToolAnnotations(Write, idempotent)
- [ ] 16.6 Unit tests for all 5 contact tools

## 17. P3 — Usage, Groups, Direct Upload (5 tools → tools/misc.py)

- [ ] 17.1 Implement `usage_stats`: `GET /v1/usage-stats`, ToolAnnotations(RO, idempotent)
- [ ] 17.2 Implement `media_upload_direct`: `POST /v1/media/upload-direct`, docstring: "alternative to media_upload for smaller files — same presign flow handles large files", ToolAnnotations(Write, not idempotent)
- [ ] 17.3 Implement `account_groups_list`: `GET /v1/account-groups`, ToolAnnotations(RO, idempotent)
- [ ] 17.4 Implement `account_groups_create`: `POST /v1/account-groups`, ToolAnnotations(Write, not idempotent)
- [ ] 17.5 Implement `account_groups_delete`: `DELETE /v1/account-groups/{id}`, ToolAnnotations(Write, idempotent)
- [ ] 17.6 Unit tests for all 5 misc tools

## 18. Smoke Tests

- [ ] 18.1 Add smoke tests for P0: queue_list_slots, validate_post_length
- [ ] 18.2 Add smoke tests for P1: accounts_follower_stats, profiles_get
- [ ] 18.3 Add smoke tests for P2: inbox_list, comments_list
- [ ] 18.4 Add smoke tests for P3: contacts_list, usage_stats

## 19. Deploy

- [ ] 19.1 Commit, push, and redeploy via Komodo
- [ ] 19.2 Verify all ~83 tools appear in Claude.ai MCP connector
