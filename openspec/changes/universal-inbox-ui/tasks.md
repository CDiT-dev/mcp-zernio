## Phase 1: Server Infrastructure

- [ ] **Create `src/zernio_mcp/inbox.py`** — new file following `upload.py` pattern. Register all `/inbox/*` routes with `register_inbox_routes(mcp)`. Wire it in `server.py` alongside `register_upload_routes`. (PROXY-001)
- [ ] **Implement token-based auth** — `inbox_get_link()` generates token, `/inbox` validates and sets `inbox_session` cookie (httponly, 24h TTL), cookie refresh on API calls. Reuse `_upload_tokens` pattern. (PROXY-002)
- [ ] **Add `inbox_get_link` MCP tool** — new tool in `src/zernio_mcp/tools/misc.py` that calls `create_inbox_token()` and returns `{"inboxUrl": "https://.../inbox?token=..."}`. (PROXY-002)
- [ ] **Implement unified stream endpoint** — `GET /inbox/api/stream` merges conversations + comments + reviews via `asyncio.gather`. Support `type`, `platform`, `status`, `q`, `limit`, `offset` query params. Sort by timestamp desc. Return `unreadCounts`. (PROXY-003)
- [ ] **Implement conversation detail endpoint** — `GET /inbox/api/conversations/{conv_id}` returns conversation metadata + messages. Route to correct upstream endpoint based on item type (DM vs comment vs review). (PROXY-004)
- [ ] **Implement reply endpoint** — `POST /inbox/api/reply` routes to correct Zernio endpoint based on `itemType` and `private` flag. Validate required fields per item type. (PROXY-005)
- [ ] **Implement action endpoint** — `POST /inbox/api/action` dispatches to correct upstream call based on `action` + `itemType`. Validate action/platform compatibility. (PROXY-006)
- [ ] **Implement message edit endpoint** — `PATCH /inbox/api/messages/{id}` proxies to Zernio message edit API. (PROXY-007)
- [ ] **Implement error handling** — catch `ZernioAPIError`, sanitize error messages, return appropriate HTTP status codes. Never expose API key. (PROXY-010)
- [ ] **Write tests for all proxy endpoints** — respx-mocked tests for stream, conversation, reply, action, edit, and auth flow. Test error cases and validation.

## Phase 2: SPA Shell & Core Layout

- [ ] **Create SPA HTML shell** — inline HTML/CSS/JS served from `GET /inbox`. Include CDiT Design System tokens as CSS custom properties (oklch colors, Montserrat/Space Mono/Lora fonts, 0px border-radius, hard shadows). (INBOX-UI-001, INBOX-UI-020)
- [ ] **Implement client-side router** — `history.pushState()` routing for `/inbox`, `/inbox/conv/:id`, `/inbox/archived`, `/inbox/sent`. Handle browser back/forward. (INBOX-UI-001)
- [ ] **Build desktop three-column layout** — sidebar (260px) + conversation list (380px) + detail panel (flex). CSS flexbox, responsive breakpoint at 1024px. (INBOX-UI-002)
- [ ] **Build mobile single-column layout** — header, filter tabs, conversation list, bottom nav. Breakpoint < 768px. View transitions between list and detail. (INBOX-UI-003)
- [ ] **Implement responsive breakpoints** — test at 390px (mobile), 768px (tablet), 1024px (desktop), 1440px (wide). Use `min-h-dvh` on mobile. (INBOX-UI-003)

## Phase 3: UI Components

- [ ] **Build conversation item component** — avatar (initials, platform color), name (weight varies by read state), platform badge (colored pill), preview text (truncated), timestamp (relative), unread dot. (INBOX-UI-004)
- [ ] **Build message bubble component** — incoming (white) vs outgoing (green), 2px border, 4px hard shadow, max-width constraints, timestamp below. Desktop: include 28x28 avatar. (INBOX-UI-005)
- [ ] **Build date separator component** — "Today" / "Yesterday" / "Apr 9" with horizontal rules. Space Mono 11px muted centered. (INBOX-UI-005)
- [ ] **Build reply composer** — text area, send button (text on desktop, ↑ icon on mobile), "Replying as @handle on Platform" context line, public/private toggle for comments, "Attach media" link. Disable send when empty. (INBOX-UI-010)
- [ ] **Build sidebar navigation** — filter items with unread counts (All Messages, Comments, DMs, Reviews), divider, Archived + Sent links. Active state: green fill + shadow. Platform filter chips at bottom. (INBOX-UI-002)
- [ ] **Build mobile filter tabs** — horizontal scrollable pills. Active: green fill + shadow. Inactive: black border. Include counts. (INBOX-UI-003)
- [ ] **Build search input** — 2px black border, placeholder text, client-side filtering of conversation list. (INBOX-UI-002)
- [ ] **Build mobile bottom nav** — Inbox (active) / Posts / Open App. Fixed to bottom, safe area padding. (INBOX-UI-003)

## Phase 4: Interaction Patterns

- [ ] **Implement desktop context menu** — right-click on conversation item shows 8-item menu (Reply, Private Reply, Like, Mark Read, Archive, Open in App, Hide, Delete). Right-click on sent message shows Edit/Delete. 220px/180px card with hard shadow. (INBOX-UI-006)
- [ ] **Implement mobile swipe actions** — swipe left reveals Read/Archive/Private/Delete buttons (70px each, colored backgrounds). Spring animation on release. Item slides 280px left. (INBOX-UI-007)
- [ ] **Implement delete confirmation dialog** — modal card with title, description, Cancel + Delete buttons. Required before any delete action. Dismiss on Cancel or click-outside. (INBOX-UI-008)
- [ ] **Implement mobile long-press** — on sent messages, show Edit/Delete options. (INBOX-UI-007)
- [ ] **Implement optimistic updates** — all actions update UI immediately. Roll back on API failure with error toast. Archive slides item out, read removes dot, hide fades to 40%, reply appears with "Sending..." status. (INBOX-UI-018)
- [ ] **Implement keyboard shortcuts** — j/k navigate list, Enter opens conversation, Escape goes back, r focuses reply, e archives, u toggles read. ? shows help overlay. (INBOX-UI-019)

## Phase 5: Special Views

- [ ] **Build review detail view** — star rating header (orange ★), review body in Lora serif italic card, reply composer with "public on Google Business" warning, "Open in Google" deeplink. (INBOX-UI-009)
- [ ] **Build archived view** — header with back arrow + count badge, items at 65% opacity + "ARCHIVED" badge + archive date, Restore button per item. (INBOX-UI-011)
- [ ] **Build sent messages view** — similar to archived, shows sent messages with recipient, platform, delivery status. (INBOX-UI-011)
- [ ] **Build hidden comment state** — 40% opacity + "HIDDEN" outlined badge next to platform badge, "Hidden" in timestamp line. (INBOX-UI-004)

## Phase 6: Loading, Empty & Error States

- [ ] **Build loading skeletons** — conversation list: 4 skeleton items with gray bars, varying widths, 4th at 50% opacity, CSS animate-pulse. Message detail: header + 3 bubble skeletons. (INBOX-UI-013)
- [ ] **Build empty states** — Inbox Zero: green checkmark + "All caught up" + action buttons. No search results: query echo + "Clear Filters". No items in filter. (INBOX-UI-012)
- [ ] **Build error banner** — connection lost: red full-width banner with ⚠ icon + retry button. Auto-retry every 30s. (INBOX-UI-014)
- [ ] **Build failed message state** — bubble at 60% opacity + "Failed to send" red text + Retry/Delete. (INBOX-UI-014)
- [ ] **Build auth expired page** — full-page: "Session expired" + instructions to get new link from Claude. (INBOX-UI-014)

## Phase 7: PWA & Push Notifications

- [ ] **Create PWA manifest** — `/inbox/manifest.json` with name, icons, display standalone, theme/background colors. Serve as Starlette route. (INBOX-UI-015)
- [ ] **Create service worker** — `/inbox/sw.js` for push notification handling, click-to-open routing, offline fallback page, badge management. (INBOX-UI-015)
- [ ] **Add mobile meta tags** — `apple-mobile-web-app-capable`, viewport with `viewport-fit=cover`, theme-color meta tag. (INBOX-UI-015)
- [ ] **Build notification opt-in card** — pre-permission UI: bell icon + "Never miss a message" + description + Enable button + "Not now" (dismisses 7 days). (INBOX-UI-016)
- [ ] **Implement push subscription flow** — `Notification.requestPermission()` → `pushManager.subscribe()` → `POST /inbox/api/push/subscribe`. (PROXY-008)
- [ ] **Implement server-side push delivery** — background polling loop (60s), detect new unread items, send via `pywebpush` with VAPID keys. Rate limit: 1 notification per conversation per 5 min. (PROXY-009)
- [ ] **Implement notification payloads** — DM: "{name} via {platform} DM" + preview. Comment: "New comment on {platform}" + author:text. Review: "New ★ review" + preview. Include `tag` for grouping and `data.url` for deeplink. Android: add Reply/Archive action buttons. (INBOX-UI-016)
- [ ] **Implement app badge** — `navigator.setAppBadge(unreadCount)` updated on each poll. Clear when inbox is opened. (INBOX-UI-016)
- [ ] **Add `pywebpush` dependency** — add to `pyproject.toml` dependencies. Add `VAPID_PRIVATE_KEY` and `VAPID_PUBLIC_KEY` env vars to config. (PROXY-009)

## Phase 8: Data & Polling

- [ ] **Implement polling strategy** — active tab: 15s interval. Background tab: 60s (detect via `document.hidden`). After action: immediate re-fetch. (INBOX-UI-017)
- [ ] **Implement pull-to-refresh** — touch-drag down triggers manual poll. Show "↻ Pull to refresh · Updated {time} ago" indicator. Use `overscroll-behavior: contain`. (INBOX-UI-017)
- [ ] **Implement deduplication** — compare `id` + `updatedAt` on each poll to avoid re-rendering unchanged items. New items slide in from top with animation. (INBOX-UI-017)
- [ ] **Implement client-side search** — filter conversation list by `participant.name` and `preview` text. Debounce 300ms. Show "No results" empty state. (PROXY-003)

## Phase 9: Missing Must-Haves

- [ ] **Build sent messages view** — header with back arrow + "Sent" + count badge. List of sent messages with recipient, platform badge, content preview, sent timestamp, delivery status indicator (Sent/Delivered/Read/Failed). Failed messages show Retry. Link each item to full conversation. (INBOX-UI-021)
- [ ] **Build auth expired page** — full-page centered card: red X icon (Lucide `x-circle`, 64x64), "Session expired" heading, explanation text, "Get New Link" informational button, expandable "What happened?" section. Must not expose tokens or internal errors. (INBOX-UI-022)
- [ ] **Build toast/undo snackbar component** — bottom-center positioned (above bottom nav on mobile). White card, 2px border, 4px hard shadow. Montserrat 14px text + optional "Undo" link (green semibold). Auto-dismiss 5s. `role="status"` + `aria-live="polite"`. Max 1 toast at a time. (INBOX-UI-023)
- [ ] **Wire toast to all actions** — archive ("Conversation archived" + Undo), mark read/unread (+ Undo), hide comment (+ Undo), delete ("Comment deleted", no undo), like ("Liked"), follow ("Following @handle"), reply sent/failed. Undo calls reverse API endpoint within 5s window. (INBOX-UI-023)
- [ ] **Implement dark mode** — define all color tokens as CSS custom properties on `:root` (light) and `.dark` (dark). Dark mode: near-black green background, cream text/borders, golden hard-offset shadows, bright cyan-green primary. Follow `prefers-color-scheme: dark` by default, optional manual toggle via settings icon. Store preference in localStorage. Increase letter-spacing to 0.04em. Platform badge colors stay constant. (INBOX-UI-024)
- [ ] **Design dark mode artboard** — create at least one dark mode variant in Paper (mobile list view) to verify token mapping and contrast. (INBOX-UI-024)
- [ ] **Replace all emoji icons with Lucide SVGs** — settings (⚙ → `settings`), back arrow (← → `arrow-left`), send (↑ → `send`), checkmark (✓ → `check`), close (✕ → `x`), archive (▣ → `archive`), private (◟ → `lock`), open link (⇗ → `external-link`), bell (🔔 → `bell`), dots menu (⋯ → `more-horizontal`), edit (✎ → `pencil`), like (♡ → `heart`), retweet (↺ → `repeat`), bookmark (⊛ → `bookmark`), follow (+ → `user-plus`). (INBOX-UI-020)

## Phase 10: Polish & Testing

- [ ] **Implement animations** — list entrance stagger (50ms), message bubble entrance, archive slide-out, swipe spring, context menu fade-in, toast slide-up. All 150-200ms ease-out. Respect `prefers-reduced-motion`. (INBOX-UI-020)
- [ ] **Test on iOS Safari PWA** — install to Home Screen, verify push notifications (tap-only), badge count, pull-to-refresh, swipe actions, back button navigation.
- [ ] **Test on Android Chrome PWA** — install, verify actionable notifications (Reply/Archive buttons), inline reply, badge, all interactions.
- [ ] **Test responsive breakpoints** — 390px, 768px, 1024px, 1440px. Verify layout transitions, no horizontal scroll, touch targets >= 44px.
- [ ] **Accessibility audit** — aria-labels on icon buttons, focus management for context menu/dialog, keyboard navigation, color contrast 4.5:1 minimum, screen reader testing.
- [ ] **Add integration tests** — end-to-end tests for: create session → load inbox → select conversation → send reply → archive → verify state.
