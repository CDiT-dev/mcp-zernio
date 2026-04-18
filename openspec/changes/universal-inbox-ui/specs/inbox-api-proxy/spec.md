## ADDED Requirements

### PROXY-001: Route Registration

The inbox API proxy MUST be registered as custom Starlette routes on the FastMCP server in a new file `src/zernio_mcp/inbox.py`, following the pattern of `upload.py`.

Routes:
- `GET /inbox` — serve the SPA HTML
- `GET /inbox/api/stream` — unified inbox stream
- `GET /inbox/api/conversations/{conv_id}` — single conversation with messages
- `POST /inbox/api/reply` — send reply (DM, comment, or review)
- `POST /inbox/api/action` — perform action (archive, read, hide, delete, like, follow)
- `GET /inbox/manifest.json` — PWA manifest
- `GET /inbox/sw.js` — service worker
- `POST /inbox/api/push/subscribe` — register push subscription
- `POST /inbox/api/push/unsubscribe` — remove push subscription

All `/inbox/api/*` routes MUST require a valid session (cookie or token).

### PROXY-002: Authentication

**Token generation**: A new MCP tool `inbox_get_link()` MUST generate a short-lived token (10 min TTL) and return a URL to `/inbox?token=<token>`.

**Session flow**:
1. Browser opens `/inbox?token=<token>`
2. Server validates token against `_inbox_tokens` dict (same pattern as `_upload_tokens`)
3. On valid token: set `inbox_session` cookie (httponly, secure, samesite=lax, 24h TTL)
4. Consume the token (one-time use)
5. Subsequent requests authenticated via cookie
6. Cookie TTL refreshed on each successful API call

**Invalid session**: Return `401 {"error": "Session expired"}` for API routes, redirect to error page for HTML route.

The Zernio API key (`ZERNIO_API_KEY`) MUST never be exposed to the browser. All upstream API calls go through the proxy.

### PROXY-003: Unified Stream Endpoint

`GET /inbox/api/stream` MUST merge data from three Zernio API endpoints:

| Source | Upstream Endpoint | Item Type |
|--------|------------------|-----------|
| DM conversations | `GET /v1/inbox/conversations` | `dm` |
| Comments | `GET /v1/inbox/comments` | `comment` |
| Reviews | `GET /v1/inbox/reviews` | `review` |

**Query parameters**:
- `type` (string, optional): `all` (default), `dm`, `comment`, `review`
- `platform` (string, optional): `twitter`, `instagram`, `linkedin`, `bluesky`, `facebook`, `google`
- `status` (string, optional): `unread`, `read`, `archived`
- `q` (string, optional): search query (applied as client-side filter on `participant.name` and `preview`)
- `limit` (int, optional, default 50, max 100): items per page
- `offset` (int, optional, default 0): pagination offset

**Response format**:
```json
{
  "items": [
    {
      "id": "string",
      "type": "dm | comment | review",
      "platform": "string",
      "participant": {
        "name": "string",
        "username": "string",
        "initials": "string"
      },
      "preview": "string (max 100 chars)",
      "content": "string (full text)",
      "timestamp": "ISO 8601",
      "unread": true,
      "hidden": false,
      "accountId": "string",
      "platformData": {
        "postId": "string (comments only)",
        "commentId": "string (comments only)",
        "conversationId": "string (DMs only)",
        "reviewId": "string (reviews only)",
        "rating": 5,
        "platformPostUrl": "string (deeplink to native platform)"
      }
    }
  ],
  "total": 24,
  "unreadCounts": {
    "all": 24,
    "dm": 8,
    "comment": 12,
    "review": 4
  },
  "lastUpdated": "ISO 8601"
}
```

Items MUST be sorted by `timestamp` descending (newest first).

The server MUST make the three upstream API calls concurrently (asyncio.gather) and merge results.

### PROXY-004: Conversation Detail Endpoint

`GET /inbox/api/conversations/{conv_id}` MUST return a single conversation with its messages.

**For DMs**: calls `GET /v1/inbox/conversations/{id}` + `GET /v1/inbox/conversations/{id}/messages`.

**For comments**: calls `GET /v1/inbox/comments/{postId}` to get the comment thread.

**For reviews**: calls `GET /v1/inbox/reviews` filtered to the specific review.

**Response format**:
```json
{
  "conversation": {
    "id": "string",
    "type": "dm | comment | review",
    "platform": "string",
    "participant": { "name": "string", "username": "string", "initials": "string" },
    "accountId": "string",
    "status": "unread | read | archived",
    "platformPostUrl": "string"
  },
  "messages": [
    {
      "id": "string",
      "content": "string",
      "sender": "them | me",
      "timestamp": "ISO 8601",
      "status": "sent | delivered | read | failed",
      "editable": true,
      "deletable": true
    }
  ]
}
```

Messages MUST be sorted by `timestamp` ascending (oldest first).

### PROXY-005: Reply Endpoint

`POST /inbox/api/reply` MUST accept:

```json
{
  "itemId": "string",
  "itemType": "dm | comment | review",
  "content": "string (required, non-empty)",
  "private": false,
  "platformData": {
    "conversationId": "string (DMs)",
    "postId": "string (comments)",
    "commentId": "string (comments/private reply)",
    "reviewId": "string (reviews)"
  }
}
```

**Routing**:
- `dm` → `POST /v1/inbox/conversations/{conversationId}/messages` with `{"content": "..."}`
- `comment` + `private: false` → `POST /v1/inbox/comments/{postId}` with `{"commentId": "...", "content": "..."}`
- `comment` + `private: true` → `POST /v1/inbox/comments/{postId}/{commentId}/private-reply` with `{"content": "..."}`
- `review` → `POST /v1/inbox/reviews/{reviewId}/reply` with `{"content": "..."}`

**Validation**:
- `content` MUST be non-empty string
- `itemType` MUST be one of `dm`, `comment`, `review`
- Required `platformData` fields depend on `itemType`
- Return 400 with clear error message for invalid input

**Response**: `{"success": true, "messageId": "string"}` or `{"error": "string"}`

### PROXY-006: Action Endpoint

`POST /inbox/api/action` MUST accept:

```json
{
  "action": "archive | read | unread | hide | unhide | delete | like | follow",
  "itemId": "string",
  "itemType": "dm | comment | review",
  "platformData": {
    "conversationId": "string",
    "postId": "string",
    "commentId": "string",
    "accountId": "string",
    "messageId": "string"
  }
}
```

**Routing**:

| Action | Item Type | Upstream Call |
|--------|-----------|-------------|
| `archive` | dm | `PUT /v1/inbox/conversations/{id}` with `{"status": "archived"}` |
| `read` | dm | `PUT /v1/inbox/conversations/{id}` with `{"status": "read"}` |
| `unread` | dm | `PUT /v1/inbox/conversations/{id}` with `{"status": "unread"}` |
| `hide` | comment | `POST /v1/inbox/comments/{postId}/{commentId}/hide` |
| `delete` | comment | `DELETE /v1/inbox/comments/{postId}` with `commentId` param |
| `delete` | dm (message) | `DELETE /v1/inbox/conversations/{convId}/messages/{msgId}` |
| `like` | comment | `POST /v1/inbox/comments/{postId}/{commentId}/like` |
| `follow` | dm (twitter) | `POST /v1/twitter/follow` with `accountId` |

**Validation**:
- `action` MUST be one of the allowed values
- Platform-specific actions (follow, retweet) MUST only work for supported platforms
- `delete` action MUST NOT be called without prior confirmation on the client side (the API has no undo)

**Response**: `{"success": true}` or `{"error": "string"}`

### PROXY-007: Message Edit Endpoint

`PATCH /inbox/api/messages/{message_id}` MUST accept:

```json
{
  "conversationId": "string",
  "content": "string (required, non-empty)"
}
```

Maps to: `PATCH /v1/inbox/conversations/{conversationId}/messages/{messageId}` with `{"content": "..."}`.

### PROXY-008: Push Notification Subscription

`POST /inbox/api/push/subscribe` MUST accept a standard Web Push subscription object:

```json
{
  "endpoint": "string",
  "keys": {
    "p256dh": "string",
    "auth": "string"
  }
}
```

Store in an in-memory dict keyed by endpoint (same pattern as `_upload_results`). For persistence across restarts, optionally store in a JSON file at `/data/push_subscriptions.json`.

`POST /inbox/api/push/unsubscribe` removes the subscription by endpoint.

### PROXY-009: Push Notification Delivery

The server MUST implement a background polling loop that:

1. Runs every 60 seconds when at least one push subscription is registered
2. Fetches the unified stream with `status=unread`
3. Compares against a `_last_notified` dict to identify new items
4. Sends Web Push notifications for new items using the `pywebpush` library

**VAPID keys**: Read from environment variables `VAPID_PRIVATE_KEY` and `VAPID_PUBLIC_KEY`. If not set, push features are disabled (no error, just no push).

**Notification payload**: JSON with `title`, `body`, `tag`, `data.url`, and `actions` array (for Android).

**Rate limiting**: Maximum 1 notification per conversation per 5 minutes to avoid spam during active conversations.

### PROXY-010: Error Handling

All proxy endpoints MUST:

- Catch `ZernioAPIError` and return `{"error": "string"}` with appropriate HTTP status
- Never expose the Zernio API key in error messages
- Return 401 for expired/invalid sessions
- Return 400 for invalid input with descriptive error messages
- Return 502 for upstream Zernio API failures with "Unable to connect to Zernio" message
- Log errors server-side for debugging

### PROXY-011: CORS and Security

- All `/inbox/*` routes are same-origin (served from the same server) — no CORS headers needed
- Session cookies MUST be `httponly`, `secure` (in production), `samesite=lax`
- All user input (reply content, search queries) MUST be validated and sanitized before passing to upstream API
- Rate limit: max 20 actions per minute per session to prevent abuse
