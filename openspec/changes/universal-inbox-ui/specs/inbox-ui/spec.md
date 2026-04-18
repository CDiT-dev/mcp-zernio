## ADDED Requirements

### INBOX-UI-001: SPA Shell and Routing

The MCP server MUST serve a single-page application at `GET /inbox` that:
- Returns an HTML page with embedded CSS and JS (no external dependencies)
- Requires a valid session token (via `?token=` query param or `inbox_session` cookie)
- Returns 403 with "Session expired" message if token is invalid/expired
- Supports client-side routing via `history.pushState()` for:
  - `/inbox` — main stream view
  - `/inbox/conv/:id` — conversation detail
  - `/inbox/archived` — archived items
  - `/inbox/sent` — sent messages
- Respects browser back/forward buttons
- Each route is deep-linkable and shareable

### INBOX-UI-002: Desktop Layout (>= 1024px)

The desktop view MUST render a three-column layout:

**Sidebar (260px fixed)**:
- Logo: Green "Z" square (32x32) + "Inbox" text (Montserrat 18px semibold)
- Navigation filters with unread counts:
  - All Messages (active: green background, white text, hard shadow)
  - Comments
  - Direct Messages
  - Reviews
  - Divider line
  - Archived (no count)
  - Sent (no count)
- Platform filter chips at bottom: All (active: dark fill) / Twitter / Instagram / LinkedIn / Bluesky
- Notification opt-in card (if not yet enabled)

**Conversation List (380px fixed)**:
- Search input at top (2px black border, placeholder "Search conversations...")
- Scrollable list of conversation items
- Each item shows: avatar, name, platform badge, preview text, timestamp, unread indicator
- Selected item: left 4px green border + cream background

**Detail Panel (remaining width)**:
- Header: avatar + name + "@handle · Platform Type" + action buttons (Mark Read, Archive, + Follow)
- Scrollable message area with date separators
- Reply composer at bottom

### INBOX-UI-003: Mobile Layout (< 768px)

The mobile view MUST render as a single-column PWA-optimized layout:

**List View**:
- Status bar (9:41, battery indicator)
- App header: Z logo (28x28) + "Inbox" (20px semibold) + settings icon
- Horizontal scrollable filter tabs: All 24 / Comments 12 / DMs 8 / Reviews 4
  - Active tab: green fill, white text, hard shadow
  - Inactive: black border, white fill
- Conversation list (same item components as desktop, 15px body text)
- Pull-to-refresh indicator: "↻ Pull to refresh · Updated {time} ago"
- Bottom navigation bar: Inbox (active, green) / Posts / Open App (deeplink to Zernio web)

**Detail View** (push navigation):
- Back arrow (←) + avatar (32x32) + name + "@handle · Platform Type" + "Open" deeplink button
- Message bubbles (max-width 300px)
- Quick action bar: Like / Retweet / Bookmark / + Follow (green fill)
- Reply composer: text input + send button (green, ↑ icon)

### INBOX-UI-004: Conversation Item Component

Each conversation item MUST display:

| Element | Unread State | Read State |
|---------|-------------|------------|
| Avatar | 40x40, platform-colored background, 2-letter initials, 2px black border | Same |
| Name | Montserrat 14-15px **semibold** | Montserrat 14-15px **regular** |
| Platform badge | Colored pill, white text, Space Mono 9-10px uppercase | Same |
| Preview | Montserrat 13-14px, **dark** foreground, single-line truncated | **Muted** foreground |
| Timestamp | Space Mono 11px muted, relative format + type label | Same |
| Unread dot | 10px green square, 2px black border | **Hidden** |

**Hidden state**: entire item at 40% opacity + "HIDDEN" outlined badge next to platform badge.

**Archived state**: 65% opacity + "ARCHIVED" outlined badge + "Archived {date}" in timestamp.

### INBOX-UI-005: Message Bubbles

Messages MUST render as:

| Property | Incoming | Outgoing |
|----------|----------|----------|
| Background | White (`oklch(1.0 0 0)`) | Green (`oklch(0.5687 0.1498 151.938)`) |
| Text color | Dark foreground | White |
| Border | 2px solid black | 2px solid black |
| Shadow | 4px 4px 0px black | 4px 4px 0px black |
| Alignment | Left | Right |
| Max width | 480px (desktop) / 300px (mobile) | Same |
| Avatar | 28x28 with initials (desktop only) | 28x28 green "CR" (desktop only) |
| Timestamp | Below bubble, Space Mono 11px/10px | + "Sent" suffix |

**Date separators** between message groups: "Today", "Yesterday", or "Apr 9" format. Space Mono 11px muted, centered with horizontal rules.

**Hover state** (desktop): Three-dot (⋯) button appears top-right of bubble (24x24, white, 2px black border).

**Failed message state**: 60% opacity + "Failed to send" red text + "Retry" red outlined button + "Delete" text link.

### INBOX-UI-006: Context Menu — Desktop Right-Click

**On conversation item** (220px wide card, 2px black border, 4px hard shadow):

Group 1 — Actions:
- ↩ Reply
- ◟ Private Reply (comments only)
- ♡ Like (comments only)

Group 2 — Management:
- ✓ Mark as Read
- ▣ Archive
- ⇗ Open in App

Group 3 — Moderation (destructive):
- ◉ Hide Comment (muted text, comments only)
- ✕ Delete Comment (red text, comments only)

Groups separated by 1px divider lines.

**On sent message** (180px wide):
- ✎ Edit Message
- ✕ Delete Message (red text)

### INBOX-UI-007: Swipe Actions — Mobile

Swiping left on a conversation item reveals 4 action buttons (70px each):

| Position | Label | Background | Icon | Action |
|----------|-------|-----------|------|--------|
| 1 | Read | Green (primary) | ✓ | Mark as read |
| 2 | Archive | Orange (accent) | ▣ | Archive conversation |
| 3 | Private | Gray (muted-fg) | ◟ | Send private reply |
| 4 | Delete | Red (destructive) | ✕ | Delete (triggers confirmation) |

Labels: Montserrat 10px semibold, white/dark text. Icons: 16px.

The conversation item slides left by 280px to reveal the actions behind it.

**Long-press on sent message** (mobile): Shows Edit / Delete options.

### INBOX-UI-008: Delete Confirmation Dialog

When Delete is triggered, a modal dialog MUST appear:

- Card: white, 2px black border, 4px hard shadow, centered
- Title: "Delete this comment?" — Montserrat 16px semibold
- Body: "This will permanently remove the comment from the platform. This action cannot be undone." — Montserrat 14px muted
- Actions: "Cancel" (outline button) + "Delete" (red filled button with shadow)
- Clicking outside or Cancel dismisses without action
- Delete MUST require explicit confirmation — no single-tap delete

### INBOX-UI-009: Review Detail View

When a review-type item is selected, the detail panel MUST show:

- Header: avatar (48x48) + name (18px semibold) + star rating (★★★★★ orange) + "Google Review · {time}" + "Open in Google" button
- Review body: Lora serif 16px italic, in a bordered card with 4px hard shadow
- Reply composer:
  - "Your Reply" label (Montserrat 14px semibold)
  - Text area (2px border, min-height 80px)
  - "Reply" button (green filled)
  - Warning: "This reply will be public on Google Business" (Space Mono 11px muted)

### INBOX-UI-010: Reply Composer

The reply composer MUST:

- Display the current reply context: "Replying as @{username} on {Platform}" (Space Mono 11px)
- Support text input with platform-appropriate character counting where relevant
- Show a "Reply publicly" / "Reply privately" toggle for comments (where private reply is supported)
- Include an "Attach media" link (desktop only)
- Desktop: "Send" text button (green, hard shadow)
- Mobile: Arrow ↑ icon button (green, hard shadow)
- Disable send button when input is empty

### INBOX-UI-011: Archived View

The archived view MUST:

- Show a header: back arrow + "Archived" + item count badge
- List archived items at 65% opacity
- Each item shows an "ARCHIVED" outlined badge and archive date ("Archived Apr 9")
- Each item has a "Restore" button (outlined, Space Mono 11px) that moves it back to the main inbox
- Confirm before bulk-restoring if multiple items selected

### INBOX-UI-012: Empty States

**Inbox Zero** (no active items):
- Green checkmark icon (64x64 square, 2px border)
- "All caught up" — Montserrat 20px semibold
- Helpful description — Montserrat 14px muted, centered, max-width 360px
- Two action buttons: "View Archived" (outline) + "Create a Post" (green filled)

**No search results**:
- "No results for '{query}'" — Montserrat 18px semibold
- Help text + "Clear Filters" button

**No items in filter category**:
- "No {type} yet" with contextual guidance

### INBOX-UI-013: Loading States

**Conversation list skeleton**:
- 4 skeleton items matching conversation item layout dimensions
- Gray placeholder bars (`oklch(0.93 0.005 91)`) with CSS `animate-pulse`
- Varying widths per row to look natural
- 4th item at 50% opacity to suggest progressive loading

**Message detail skeleton**:
- Header skeleton: avatar placeholder + 2 text bars
- 3 message bubble skeletons alternating left/right alignment

### INBOX-UI-014: Error States

**Connection lost**:
- Full-width red banner at top of content area
- ⚠ icon + "Unable to connect to Zernio. Your messages may not be up to date." — white text
- "Retry" button (white outline on red background)
- Auto-retry every 30 seconds

**Failed message** (inline):
- Message bubble at 60% opacity
- "Failed to send" — red text + "Retry" button (red outline) + "Delete" link
- Optimistic: shown only after API failure, not pre-emptively

**Auth expired**:
- Full-page: "Session expired" heading + "Please request a new inbox link from Claude." + "Get New Link" button

### INBOX-UI-015: PWA Configuration

The inbox MUST be installable as a PWA:

- `manifest.json` served at `/inbox/manifest.json` with:
  - `name`: "Zernio Inbox"
  - `short_name`: "Inbox"
  - `display`: "standalone"
  - `start_url`: "/inbox"
  - `theme_color`: primary green
  - `background_color`: background cream
  - App icons (192x192, 512x512)

- Service worker registered for:
  - Push notification handling
  - Offline fallback page
  - App badge management

- Mobile meta tags: `apple-mobile-web-app-capable`, `viewport` with `viewport-fit=cover`

### INBOX-UI-016: Push Notifications

**Opt-in flow**:
- Pre-permission card shown in sidebar (desktop) or as a dismissible banner (mobile)
- "Never miss a message" heading + description of what they'll get
- "Enable" button triggers `Notification.requestPermission()`
- "Not now" dismisses for 7 days (localStorage)
- Only triggered after user gesture (required for iOS)

**Notification content**:

| Event | Title | Body |
|-------|-------|------|
| New DM | "{name} via {platform} DM" | Message preview (max 100 chars) |
| New comment | "New comment on {platform}" | "{name}: {comment}" |
| New review | "New {rating}★ review" | "{name}: {review}" |

**Platform behavior**:
- iOS: Tap opens conversation in PWA. No action buttons (Safari ignores them). Stacked by tag.
- Android: Reply + Archive action buttons. Inline text reply supported. Badge count on icon.
- All: `navigator.setAppBadge(unreadCount)` updated on each poll. Cleared when inbox is opened.

### INBOX-UI-017: Polling and Data Refresh

- Active tab: poll every 15 seconds
- Background tab (`document.hidden`): poll every 60 seconds
- After any action: immediate re-fetch of affected items
- Pull-to-refresh (mobile): manual trigger, shows spinner + last-updated timestamp
- Rate limit: max 4 requests/second to Zernio API
- Dedup: compare `id` + `updatedAt` to avoid re-rendering unchanged items

### INBOX-UI-018: Optimistic Updates

All user actions MUST update the UI immediately:
- Archive → item slides out with animation
- Mark Read → unread dot removed, name weight changes
- Delete → item removed (after confirmation)
- Hide → item fades to 40% opacity + badge appears
- Reply → message bubble appears with "Sending..." status
- Like → heart icon fills

If the API call fails, the UI MUST roll back to previous state and show an error toast.

### INBOX-UI-019: Keyboard Shortcuts (Desktop)

| Key | Action |
|-----|--------|
| `j` / `k` | Move selection up/down in conversation list |
| `Enter` | Open selected conversation |
| `Escape` | Back to list / close context menu |
| `r` | Focus reply composer |
| `e` | Archive selected |
| `u` | Toggle read/unread |
| `?` | Show keyboard shortcut help |

### INBOX-UI-020: Design System Compliance

All UI elements MUST follow CDiT Design System 2026:
- Border radius: 0px always
- Shadows: 4px 4px 0px hard-offset, no blur. Black in light mode, golden (`hsl(45 100% 80%)`) in dark mode.
- Borders: 2px solid black (light mode), 2px solid cream (dark mode)
- Fonts: Montserrat (UI), Space Mono (data), Lora (editorial/reviews)
- Colors: oklch semantic tokens only — never hardcode hex
- Icons: Lucide SVG icons only, outline style, 1.5px stroke. NO emoji characters as icons (no ⚙, ←, ✓, etc. — use Lucide `settings`, `arrow-left`, `check`, etc.)
- Animations: 150-200ms ease-out, respect `prefers-reduced-motion`
- Min body text: 16px on mobile
- `tabular-nums` for counts and timestamps

### INBOX-UI-021: Sent Messages View

The inbox MUST include a "Sent" view accessible from the sidebar navigation:

- Header: back arrow + "Sent" + message count badge
- List of sent messages showing:
  - Recipient name + platform badge
  - Message content preview (truncated)
  - Sent timestamp (Space Mono 11px)
  - Delivery status indicator: "Sent", "Delivered", "Read" (where platform provides this data), "Failed" (red)
- Each item links to the full conversation detail
- Failed messages show a "Retry" action
- Items at normal opacity (not dimmed like archived)

### INBOX-UI-022: Auth Expired Page

When the session token is invalid or expired, the inbox MUST show a full-page error:

- Centered card (max-width 480px), white, 2px black border, 4px hard shadow
- Red "X" icon (64x64 square, Lucide `x-circle`)
- "Session expired" — Montserrat 20px semibold
- "Your inbox session has expired. Request a new link from Claude to continue." — Montserrat 14px muted, centered
- "Get New Link" button (green primary, hard shadow) — this is informational since the user needs to ask Claude for a new token
- "What happened?" expandable explanation: "Inbox sessions last 24 hours for security. Ask Claude: 'open my inbox' to get a fresh link."

This page MUST NOT expose any API keys, tokens, or internal error details.

### INBOX-UI-023: Toast / Undo Snackbar

All user actions MUST show a transient toast notification confirming the action:

| Action | Toast text | Undo? |
|--------|-----------|-------|
| Archive | "Conversation archived" | Yes — "Undo" |
| Mark Read | "Marked as read" | Yes — "Undo" |
| Mark Unread | "Marked as unread" | Yes — "Undo" |
| Hide comment | "Comment hidden" | Yes — "Undo" |
| Delete comment | "Comment deleted" | No (destructive, already confirmed) |
| Like | "Liked" | No |
| Follow | "Following @{username}" | No |
| Reply sent | "Reply sent" | No |
| Reply failed | "Failed to send. Tap to retry." | No (shows retry) |

Toast component:
- Position: bottom-center, above bottom nav on mobile (bottom: 80px mobile, 24px desktop)
- Style: white card, 2px black border, 4px hard shadow
- Content: Montserrat 14px + optional "Undo" link (green primary text, semibold)
- Auto-dismiss: 5 seconds
- Manual dismiss: tap/click anywhere on toast
- Accessible: `role="status"` + `aria-live="polite"`
- Max 1 toast visible at a time — new toast replaces current

Undo behavior:
- "Undo" reverses the action via the same API endpoint (e.g., unarchive, mark unread, unhide)
- Undo MUST work within the 5-second window before the toast disappears
- After undo, show a new toast: "Undone"

### INBOX-UI-024: Dark Mode

The inbox MUST support dark mode following CDiT Design System 2026 dark theme:

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| Page background | `oklch(0.9923 0.0104 91.4994)` (warm cream) | `oklch(0.1649 0.0308 162.2739)` (near-black green) |
| Card/surface | `oklch(1.0 0 0)` (white) | `oklch(0.2283 0.0445 158.2398)` (dark green) |
| Primary text | `oklch(0.1759 0.0275 161.2531)` (deep teal-black) | `oklch(0.9809 0.0260 91.6197)` (bright cream) |
| Muted text | `oklch(0.4500 0.0200 161.0)` (mid-green-gray) | `oklch(0.7000 0.0200 91.0)` (light tan) |
| Borders | `oklch(0 0 0)` (black) | `oklch(0.9809 0.0260 91.6197)` (cream) |
| Shadows | `4px 4px 0px hsl(0 0% 0% / 1)` (black) | `4px 4px 0px hsl(45 100% 80% / 1)` (golden) |
| Primary action | `oklch(0.5687 0.1498 151.938)` (green) | `oklch(0.8484 0.2275 151.1487)` (bright cyan-green) |
| Destructive | `oklch(0.5799 0.2380 29.2339)` (red) | `oklch(0.6280 0.2577 29.2339)` (bright red) |
| Accent | `oklch(0.7721 0.1727 64.1585)` (orange) | `oklch(0.7951 0.1631 68.6392)` (bright orange) |
| Ring/focus | Green (primary) | `oklch(0.7951 0.1631 68.6392)` (orange) |
| Outgoing msg | Green primary | Bright cyan-green primary (dark mode) |
| Incoming msg | White card | Dark green card |
| Skeleton bars | `oklch(0.93 0.005 91)` | `oklch(0.28 0.03 160)` |

Dark mode activation:
- Follows system preference via `prefers-color-scheme: dark` media query
- Optional manual toggle in settings (gear icon in header)
- Preference stored in localStorage
- All color tokens defined as CSS custom properties on `:root` and `.dark`
- Letter spacing increases to 0.04em in dark mode (per CDiT spec)

Platform badge colors remain constant across themes (they're brand colors, not theme tokens).
