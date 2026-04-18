## Why

The MCP server already wraps all of Zernio's inbox and comment APIs (6 inbox tools, 6 comment tools), but interacting with conversations through an LLM tool-call loop is slow and awkward for high-volume engagement work. Comments, DMs, and reactions across 11 connected accounts need a unified, visual interface — one that loads fast, shows everything in a single stream, and lets you respond inline without switching platforms. Zernio's own web UI exists but doesn't match the responsiveness or unified-stream UX that tools like Intercom pioneered.

Since the MCP server already serves custom HTML routes (the `/upload` media page), we can host a full inbox UI on the same server — no separate frontend deployment, no CORS, direct access to all Zernio APIs through the existing authenticated client.

## What Changes

- Add a `/inbox` HTML route to the MCP server serving a single-page app
- Unified stream view combining comments, DMs, and reactions across all platforms
- Real-time or near-real-time updates via polling (Zernio API doesn't offer webhooks for inbox events to the client)
- Inline reply, like, hide, and delete actions from the stream
- Platform and conversation type filters (comments vs DMs, per-platform)
- Conversation threading: click a comment or DM to see full context
- Responsive layout — works on desktop and mobile
- Token-gated access reusing the existing `MCP_API_KEY` auth pattern

## Capabilities

### New Capabilities
- `inbox-ui`: The browser-based universal inbox single-page app — route registration, HTML/JS/CSS serving, auth gating, and the client-side application that consumes Zernio APIs
- `inbox-api-proxy`: Server-side proxy routes that expose Zernio inbox/comment/reaction data to the browser UI with proper auth, pagination, and error handling — avoids exposing the raw Zernio API key to the browser

### Modified Capabilities
None — existing MCP tools remain unchanged. The UI consumes the same Zernio REST API endpoints the tools already wrap.

## Impact

- **Server**: New Starlette routes on the FastMCP server (`/inbox` GET for the SPA, `/inbox/api/*` for proxied data)
- **Auth**: Browser sessions need a lightweight auth gate (token in URL param or cookie, similar to `/upload` pattern)
- **Dependencies**: No new Python deps — Starlette (via FastMCP) handles routing; UI is vanilla JS or a lightweight framework bundled inline
- **Performance**: Polling interval needs tuning to avoid hitting Zernio API rate limits across 11 accounts
- **Deployment**: Ships with existing Docker image, no separate infrastructure
