## Why

The MVP shipped with 13 tools covering the core posting workflow, but the Zernio API exposes 120+ endpoints. Key gaps block common mobile workflows: you can't edit a scheduled post, can't set up recurring queue slots, can't validate content before cross-posting, can't research competitor content, can't manage DMs/comments, and can't manage multiple brand profiles. This change adds ~80+ tools covering P0 through P3 to make the MCP server a comprehensive social media management tool from Claude mobile.

## What Changes

### P0 — Core workflow gaps (10 tools)

- **Queue CRUD**: Create, list, update, delete recurring time slots + get next available slot (5 tools)
- **Posts update + bulk upload**: Edit draft/scheduled posts, CSV bulk import (2 tools)
- **Validation tools**: Pre-flight checks for post length, full post validation, media validation (3 tools)

### P1 — Useful extensions (~29 tools)

- **Profile CRUD**: Create, get, update, delete brand profiles (4 tools)
- **Account management**: Update, delete accounts, follower stats, single-account health (4 tools)
- **Content download/research**: Download post info from YouTube, Instagram, TikTok, Twitter, Facebook, LinkedIn, Bluesky + YouTube transcript + Instagram hashtag checker + subreddit validator (10 tools)
- **Platform-specific analytics**: YouTube daily views, Instagram insights + demographics, post engagement timeline (4 tools)
- **Platform helpers**: Reddit search/feed/subreddits/flairs, LinkedIn mentions/org analytics, Pinterest boards, YouTube playlists (8 tools)

### P2 — Advanced features (~30 tools)

- **Inbox/Conversations**: List, get, update conversations + list/send/edit/delete messages + typing indicator + reactions (9 tools)
- **Comments**: List, reply, delete, hide, like comments + private reply (7 tools)
- **Twitter engagement**: Retweet, unretweet, bookmark, follow (4 tools)
- **Reviews**: List reviews, reply to reviews (2 tools)
- **Logs/Debugging**: Post logs, per-post logs, connection logs (3 tools)
- **Webhooks**: CRUD + test + logs (6 tools)

### P3 — Niche/Enterprise (selected, ~15 tools)

- **Broadcasts**: Create, list, get, update, delete broadcast campaigns (5 tools)
- **Contacts CRM**: List, create, get, update, delete contacts (5 tools)
- **Usage stats**: Get usage/billing statistics (1 tool)
- **Direct media upload**: Alternative upload path via `/v1/media/upload-direct` (1 tool)
- **Account groups**: List, create, delete account groups (3 tools)

## Capabilities

### New Capabilities

- `queue-crud`: Full queue slot management — create, list, update, delete recurring time slots, get next available slot
- `posts-extended`: Edit draft/scheduled posts and CSV bulk import
- `validation-tools`: Pre-flight content and media validation against platform-specific limits
- `profile-crud`: Full brand profile lifecycle — create, get, update, delete
- `account-management`: Account settings updates, disconnection, follower stats, single-account health
- `content-research`: Download and inspect posts from 7 platforms + YouTube transcripts + Instagram hashtag analysis + subreddit validation
- `platform-analytics`: Platform-specific analytics — YouTube daily views, Instagram insights/demographics, per-post engagement timeline
- `platform-helpers`: Platform-specific context — Reddit (search, feed, subreddits, flairs), LinkedIn (mentions, org analytics), Pinterest (boards), YouTube (playlists)
- `inbox-conversations`: Full DM/conversation management — list, read, reply, edit, delete messages, typing indicators, reactions
- `comments-management`: Comment lifecycle — list, reply, delete, hide, like, private reply
- `twitter-engagement`: Twitter-specific actions — retweet, unretweet, bookmark, follow
- `reviews-management`: Google Business reviews — list and reply
- `activity-logs`: Post activity logs, per-post logs, connection event logs
- `webhooks-management`: Webhook CRUD, testing, and delivery logs
- `broadcasts`: Broadcast campaign lifecycle — create, list, get, update, delete
- `contacts-crm`: Contact management — list, create, get, update, delete
- `usage-and-groups`: Usage stats, account groups management, direct media upload

### Modified Capabilities

(none — all additive)

## Impact

- **server.py**: Grows from 13 to ~95 tools — consider splitting into tool modules at this scale
- **client.py**: Add `put` and `patch` methods to ZernioClient
- **Tests**: ~80+ new unit tests (one per tool minimum) + smoke tests for key endpoints per phase
- **Deployment**: Same stack, same auth — just more tools registered
- **No new dependencies**: All tools use existing httpx client against Zernio REST API
