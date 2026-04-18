## Architecture

### Overview

The universal inbox is a browser-based SPA served directly from the existing FastMCP server via Starlette custom routes. It follows the same pattern as the existing `/upload` media page: inline HTML/JS/CSS, token-gated access, no separate frontend deployment.

```
Browser (PWA)
  |
  |-- GET /inbox              → HTML SPA shell
  |-- GET /inbox/api/stream   → Unified inbox data (conversations + comments + reviews)
  |-- GET /inbox/api/conv/:id → Single conversation with messages
  |-- POST /inbox/api/reply   → Send reply (DM or comment)
  |-- POST /inbox/api/action  → Perform action (archive, read, hide, delete, like, follow)
  |
  v
FastMCP Server (Starlette routes)
  |
  v
Zernio REST API (upstream, authenticated via ZERNIO_API_KEY)
```

### Why Not a Separate Frontend?

- Zero additional infrastructure — ships in the existing Docker image
- No CORS issues — same origin as the MCP server
- Auth is already solved (MCP_API_KEY token pattern from `/upload`)
- Deployment via existing Komodo stack, no CI changes

### Why Vanilla JS, Not React/Vue?

- The SPA is served as inline HTML (like `/upload`) — no build step, no bundler
- The UI is read-heavy with simple interactions (list, detail, reply)
- Keeps the Python package dependency-free on the frontend
- CDiT Design System tokens applied via inline CSS custom properties

---

## Server-Side Design

### Route Registration

New file: `src/zernio_mcp/inbox.py` — follows the pattern of `upload.py`.

```python
def register_inbox_routes(mcp) -> None:
    @mcp.custom_route("/inbox", methods=["GET"])
    async def inbox_page(request): ...

    @mcp.custom_route("/inbox/api/stream", methods=["GET"])
    async def inbox_stream(request): ...

    @mcp.custom_route("/inbox/api/conversations/{conv_id}", methods=["GET"])
    async def inbox_conversation(request): ...

    @mcp.custom_route("/inbox/api/reply", methods=["POST"])
    async def inbox_reply(request): ...

    @mcp.custom_route("/inbox/api/action", methods=["POST"])
    async def inbox_action(request): ...
```

Registered in `server.py` alongside `register_upload_routes(mcp)`.

### Authentication

Token-based, identical to `/upload`:

1. MCP tool `inbox_get_link()` generates a short-lived token (10 min TTL)
2. Browser opens `/inbox?token=<token>`
3. Server validates token, sets an `inbox_session` cookie (httponly, 24h TTL)
4. Subsequent API requests authenticated via cookie
5. Cookie refresh on each API call to extend session

No Keycloak/OAuth needed — this is a local tool, not a public-facing app.

### Unified Stream Endpoint (`/inbox/api/stream`)

Merges data from three Zernio API endpoints into one sorted stream:

| Source | Zernio Endpoint | Stream Item Type |
|--------|----------------|-----------------|
| DMs | `GET /v1/inbox/conversations` | `dm` |
| Comments | `GET /v1/inbox/comments` | `comment` |
| Reviews | `GET /v1/inbox/reviews` | `review` |

Query params:
- `type` — filter: `all`, `dm`, `comment`, `review`
- `platform` — filter: `twitter`, `instagram`, `linkedin`, `bluesky`, `facebook`, `google`
- `status` — filter: `unread`, `read`, `archived`
- `q` — search query (client-side filtering, Zernio API doesn't support server-side search)
- `limit` / `offset` — pagination

Response shape:
```json
{
  "items": [
    {
      "id": "conv_123",
      "type": "dm",
      "platform": "twitter",
      "participant": { "name": "Max Kleinert", "username": "maxkleinert", "initials": "MK" },
      "preview": "Love this thread on MCP servers! How...",
      "timestamp": "2026-04-12T10:41:00Z",
      "unread": true,
      "accountId": "69c2d4a36cb7b8cf4c96ed4a"
    }
  ],
  "total": 24,
  "unreadCounts": { "all": 24, "dm": 8, "comment": 12, "review": 4 }
}
```

### Action Endpoint (`/inbox/api/action`)

Unified action dispatcher:

```json
POST /inbox/api/action
{
  "action": "archive" | "read" | "hide" | "delete" | "like" | "follow" | "unhide",
  "itemId": "conv_123",
  "itemType": "dm" | "comment" | "review",
  "platformData": { "postId": "...", "commentId": "...", "accountId": "..." }
}
```

Maps to upstream Zernio API calls:
- `archive` / `read` → `PUT /v1/inbox/conversations/{id}`
- `hide` → `POST /v1/inbox/comments/{postId}/{commentId}/hide`
- `delete` (comment) → `DELETE /v1/inbox/comments/{postId}`
- `like` → `POST /v1/inbox/comments/{postId}/{commentId}/like`
- `follow` → `POST /v1/twitter/follow`
- `delete` (message) → `DELETE /v1/inbox/conversations/{convId}/messages/{msgId}`

### Reply Endpoint (`/inbox/api/reply`)

```json
POST /inbox/api/reply
{
  "itemId": "conv_123",
  "itemType": "dm" | "comment" | "review",
  "content": "Reply text",
  "private": false,
  "platformData": { "postId": "...", "commentId": "...", "conversationId": "..." }
}
```

Maps to:
- DM reply → `POST /v1/inbox/conversations/{id}/messages`
- Comment reply → `POST /v1/inbox/comments/{postId}`
- Private reply → `POST /v1/inbox/comments/{postId}/{commentId}/private-reply`
- Review reply → `POST /v1/inbox/reviews/{id}/reply`

---

## Client-Side Design

### SPA Structure

Single HTML file with embedded CSS and JS. Three main views managed via client-side routing with `history.pushState()`:

```
/inbox                    → List view (conversation stream)
/inbox/conv/:id           → Conversation detail (messages)
/inbox/archived           → Archived items
/inbox/sent               → Sent messages
```

### Layout — Desktop (>= 1024px)

Three-column layout:

| Column | Width | Content |
|--------|-------|---------|
| Sidebar | 260px | Logo, nav filters (All/Comments/DMs/Reviews/Archived/Sent), platform filter chips, notification opt-in |
| Conversation List | 380px | Search bar, scrollable conversation items with avatar, name, platform badge, preview, timestamp, unread indicator |
| Detail Panel | Remaining | Conversation header (name, platform, Open in App, Mark Read, Archive, +Follow), message bubbles, reply composer |

### Layout — Mobile (< 768px)

Single-column with view transitions:

1. **List view**: Header (Z logo + Inbox title + settings), horizontal filter tabs (All/Comments/DMs/Reviews), scrollable conversation items, pull-to-refresh indicator, bottom nav (Inbox/Posts/Open App)
2. **Detail view**: Back arrow + contact header + Open deeplink, message bubbles, quick action bar (Like/Retweet/Bookmark/Follow), reply composer with send button

Navigation: push/pop with `history.pushState()`, respects back button.

### Conversation Item Component

Each item in the conversation list:

| Element | Desktop | Mobile |
|---------|---------|--------|
| Avatar | 40x40, colored background, initials, 2px black border | Same |
| Name | Montserrat 14px semibold (unread) / 400 (read) | 15px |
| Platform badge | Background-colored pill, Space Mono 10px uppercase (TWITTER, IG, LI, BSKY, FB, GOOGLE) | 9px |
| Preview text | Montserrat 13px, dark (unread) / muted (read), single-line truncated | 14px |
| Timestamp | Space Mono 11px muted, relative ("2 min ago") + type ("DM", "Comment", "Review") | Same |
| Unread dot | 10px green square, 2px black border | Same |
| Selected state | Left 4px green border + cream background | Same |
| Hidden state | 40% opacity + "HIDDEN" badge (outlined, Space Mono 9px) | Same |

### Message Bubble Component

| Element | Incoming | Outgoing |
|---------|----------|----------|
| Background | White, 2px black border, 4px 4px 0px shadow | Green (primary), 2px black border, 4px 4px 0px shadow |
| Text | Montserrat 14px (desktop) / 15px (mobile), dark foreground | White |
| Alignment | Left-aligned, max-width 480px (desktop) / 300px (mobile) | Right-aligned |
| Avatar | 28x28 colored square with initials (desktop only) | 28x28 green square "CR" (desktop only) |
| Timestamp | Space Mono 11px muted, below bubble | + "Sent" suffix |
| Hover state | Three-dot (⋯) button appears top-right | Same, triggers edit/delete context menu |
| Failed state | 60% opacity + "Failed to send" red text + Retry button + Delete link | — |

### Date Separators

Messages grouped by date with separators:
```
——— Today ———
——— Yesterday ———
——— Apr 9 ———
```

Space Mono 11px muted, centered, horizontal rules.

### Context Menu — Desktop (Right-Click)

On conversation item (8 items, 3 groups):
1. Reply / Private Reply / Like
2. Mark as Read / Archive / Open in App
3. Hide Comment / Delete Comment (destructive, red text)

On sent message (2 items):
1. Edit Message / Delete Message (destructive, red text)

Style: White card, 2px black border, 4px hard shadow, 220px wide. Items: Montserrat 13px with icon prefix.

### Swipe Actions — Mobile

Swipe left reveals 4 action buttons (70px each):

| Button | Color | Icon | Action |
|--------|-------|------|--------|
| Read | Green (primary) | ✓ | Mark as read |
| Archive | Orange (accent) | ▣ | Archive conversation |
| Private | Gray (muted-fg) | ◟ | Send private reply |
| Delete | Red (destructive) | ✕ | Delete with confirmation dialog |

Haptic feedback at snap position. Spring animation on release.

### Delete Confirmation Dialog

Modal card (centered): White, 2px black border, 4px hard shadow.
- Title: "Delete this comment?" — Montserrat 16px semibold
- Body: "This will permanently remove the comment from the platform. This action cannot be undone." — Montserrat 14px muted
- Actions: Cancel (outline button) + Delete (red filled button with shadow)

### Reply Composer

| Element | Desktop | Mobile |
|---------|---------|--------|
| Container | Bottom of detail panel, white bg, 2px top border | Same |
| Text area | 2px black border, min-height 80px (desktop) / 44px (mobile) | Same |
| Send button | Green filled, 2px border, hard shadow, "Send" text | Arrow ↑ icon only |
| Context line | "Replying as @CaseyRomkes on Twitter" — Space Mono 11px | Hidden (shown in header) |
| Private toggle | "Reply publicly" / "Reply privately" — for comments only | Same |
| Attach media | "Attach media" link | Hidden on mobile |

### Review Detail View

Displayed when selecting a review-type item:

- Header: Avatar + name + ★★★★★ rating (Montserrat 16px orange) + "Google Review · 1 day ago" (Space Mono 12px) + "Open in Google" button
- Review body: Lora serif 16px italic, in a bordered card with shadow
- Reply composer: "Your Reply" label + text area + Reply button + "This reply will be public on Google Business" warning

### Archived View

Accessed via sidebar nav "Archived":
- Header: Back arrow + "Archived" title + item count badge
- Items: 65% opacity, "ARCHIVED" badge (outlined), archived date in timestamp ("Archived Apr 9")
- Each item has a "Restore" button (outlined, Space Mono 11px)

### Sent View

Accessed via sidebar nav "Sent":
- Same layout as archived but with sent messages
- Shows: recipient, platform, content preview, sent timestamp
- Status indicators: "Delivered", "Read" (if available from platform)

---

## Empty States

### Inbox Zero
- Green checkmark icon (64x64 square, 2px border)
- "All caught up" — Montserrat 20px semibold
- "No new messages, comments, or reviews waiting for your attention. We'll notify you when something arrives." — Montserrat 14px muted, centered, max-width 360px
- Two buttons: "View Archived" (outline) + "Create a Post" (green filled)

### No Search Results
- "No results for '{query}'" — Montserrat 18px semibold
- "Try a different search term or remove filters to see more conversations." — Montserrat 14px muted
- "Clear Filters" button (outlined)

### No Items in Filter
- "No {type} yet" — Montserrat 18px semibold
- Contextual help text per type

---

## Loading States

### Skeleton — Conversation List
4 skeleton items matching the conversation item layout:
- 40x40 gray square (avatar placeholder)
- 3 gray bars: name (120px) + badge (50px), preview (200-260px), timestamp (80-110px)
- 4th item at 50% opacity to suggest progressive loading
- Bars use `oklch(0.93 0.005 91)` (light) and `oklch(0.95 0.003 91)` (lighter)
- CSS `animate-pulse` on all placeholder bars

### Skeleton — Message Detail
- Header skeleton: avatar + 2 bars
- 3 message bubble skeletons alternating left/right

---

## Error States

### Connection Lost Banner
- Full-width red banner at top of content area
- Warning icon + "Unable to connect to Zernio. Your messages may not be up to date." — white text
- "Retry" button (white outline on red)
- Auto-retry every 30 seconds, banner persists until successful reconnection

### Failed Message (Inline)
- Message bubble at 60% opacity
- "Failed to send" — Space Mono 11px red
- "Retry" button (red outlined) + "Delete" text link
- Optimistic UI: message appears immediately, degrades if API call fails

### Auth Expired
- Full-page: "Session expired" + "Please request a new inbox link from Claude." + "Get New Link" button

---

## PWA Configuration

### manifest.json
```json
{
  "name": "Zernio Inbox",
  "short_name": "Inbox",
  "start_url": "/inbox",
  "display": "standalone",
  "background_color": "#faf8f0",
  "theme_color": "#2a9d4e",
  "icons": [
    { "src": "/inbox/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/inbox/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

### Service Worker

Minimal service worker for:
1. Push notification handling (receive + display + click-to-open)
2. Offline fallback page ("You're offline. Messages will sync when you reconnect.")
3. App badge management via `navigator.setAppBadge(count)`

No offline data caching — the inbox is real-time, stale data is worse than no data.

### Push Notifications

**Server-side**: New polling loop in the MCP server that checks for new items every 60 seconds and sends push via Web Push API (VAPID keys stored in env).

**Notification payload**:
```json
{
  "title": "Max Kleinert via Twitter DM",
  "body": "Love this thread on MCP servers! How did you handle the auth layer?",
  "tag": "conv_123",
  "data": { "url": "/inbox/conv/conv_123" },
  "actions": [
    { "action": "reply", "title": "Reply", "type": "text" },
    { "action": "archive", "title": "Archive" }
  ]
}
```

**Platform behavior**:

| Feature | iOS (Safari 16.4+) | Android (Chrome) |
|---------|--------------------|--------------------|
| Notification display | Lock screen, Notification Center, Apple Watch | Notification shade |
| Tap action | Opens `/inbox/conv/conv_123` | Same |
| Action buttons | Ignored (tap-only) | Reply + Archive buttons shown |
| Inline reply | Not supported | Supported (type: "text") |
| App badge | `navigator.setAppBadge(count)` — iOS 18+ | Supported |
| Stacked/grouped | By `tag` prefix | By `tag` prefix |

**Notification types**:

| Event | Title | Body |
|-------|-------|------|
| New DM | "{name} via {platform} DM" | Message preview (truncated 100 chars) |
| New comment | "New comment on {platform}" | "{name}: {comment preview}" |
| New review | "New {rating}★ review on Google" | "{name}: {review preview}" |
| Reply to your comment | "{name} replied on {platform}" | Reply preview |

**Opt-in UX**: Pre-permission card shown in inbox sidebar (desktop) or as a banner (mobile). Card explains what they'll get. "Enable" button triggers `Notification.requestPermission()`. "Not now" dismisses for 7 days (stored in localStorage).

### Pull to Refresh (Mobile)

- Touch-drag down from top triggers refresh
- Shows "↻ Pull to refresh · Updated 30s ago" indicator
- `overscroll-behavior: contain` on the scroll container to prevent browser's native pull-to-refresh from interfering
- Polls `/inbox/api/stream` and diffs against current state
- Optimistic: new items slide in from top with `cardItem` animation variant

---

## Data Flow

### Polling Strategy

- **Active tab**: Poll every 15 seconds
- **Background tab**: Poll every 60 seconds (detected via `document.hidden`)
- **After action**: Immediate re-fetch of affected items
- **Rate limit safety**: Max 4 requests/second across all endpoints (Zernio rate limit is likely higher, but defensive)
- **Dedup**: Use item `id` + `updatedAt` to avoid re-rendering unchanged items

### Optimistic Updates

All actions update the UI immediately before the API call completes:
- Archive → item slides out of list
- Mark Read → unread dot removed, name weight changes to 400
- Delete → item removed (after confirmation dialog)
- Hide → item fades to 40% opacity + "HIDDEN" badge appears
- Reply → message bubble appears immediately, "Sending..." status, degrades to "Failed" if API errors

### Deep Linking / URL State

Every view state is reflected in the URL:
```
/inbox                        → All messages, no selection
/inbox?type=dm&platform=twitter → Filtered view
/inbox/conv/conv_123          → Conversation detail
/inbox/archived               → Archived view
/inbox/sent                   → Sent view
```

Browser back button works naturally. Shareable URLs.

---

## Design System Compliance

All UI follows CDiT Design System 2026 (MX-Brutalist):

| Property | Value |
|----------|-------|
| Border radius | 0px — always |
| Shadows | 4px 4px 0px, hard-offset, no blur. Black in light mode. |
| Borders | 2px solid black |
| Fonts | Montserrat (primary), Space Mono (data/timestamps), Lora (review quotes) |
| Colors | oklch semantic tokens only — never hardcoded hex |
| Icons | Lucide-style outline icons, 1.5px stroke |
| Animation | ease-out 150-200ms for micro-interactions, stagger 50ms for lists |
| Reduced motion | All animations respect `prefers-reduced-motion: reduce` |

### Platform Badge Colors

| Platform | Background Color |
|----------|-----------------|
| Twitter | `oklch(0.1759 0.0275 161.2531)` (dark foreground) |
| Instagram | `oklch(0.6088 0.2498 29.2339)` (secondary/red) |
| LinkedIn | `oklch(0.3 0.1 230)` (dark blue) |
| Bluesky | `oklch(0.55 0.15 250)` (blue) |
| Facebook | `oklch(0.45 0.15 260)` (purple-blue) |
| Google | `oklch(0.7721 0.1727 64.1585)` (accent/orange) |

All badges use white text, Space Mono 10px (desktop) / 9px (mobile), uppercase.
