## Why

Zernio provides social media management across 14+ platforms via a Python SDK and REST API, but their MCP server only supports stdio transport (Claude Desktop). There is no remote/hosted variant, so Claude.ai and Claude mobile cannot use it. Building a FastMCP wrapper with SSE/streamable-HTTP transport and deploying it at `mcp-zernio.cdit-dev.de` makes social media tools available everywhere Claude runs — following the established CDiT MCP server pattern (Stolperstein, Klartext, Bildsprache).

## What Changes

- New FastMCP server wrapping the Zernio REST API (`/v1/*` endpoints)
- 13 MCP tools covering accounts (list + health), profiles, posts (CRUD + unpublish + retry), media upload, analytics (per-post + insights), and queue preview
- Media upload accepts a **URL**, fetches bytes server-side, uploads via Zernio's presigned URL flow (`POST /v1/media/presign` → `PUT` to GCS), returns `publicUrl` for use in `posts_create`
- No thin wrapper aliases — `posts_create` documents immediate/scheduled/draft modes inline; `posts_list` documents status filters (including `failed`) in its docstring
- OAuth client_id + client_secret authentication (mandatory for Claude.ai MCP connectors)
- Deployed behind Caddy reverse proxy on Hetzner with SSE/streamable-HTTP transport

### Tool surface (13 tools)

| Tool | RO/Write | Purpose |
|------|----------|---------|
| `accounts_list` | RO | Connected social accounts with platform, username, displayName |
| `accounts_health` | RO | Token health / expiry status per account |
| `profiles_list` | RO | Brand profile groupings |
| `posts_create` | Write | Draft, schedule, or publish (3 modes documented in docstring) |
| `posts_get` | RO | Single post status lookup by ID |
| `posts_list` | RO | Filter/search posts by status, platform, date |
| `posts_delete` | Write | Delete draft/scheduled posts |
| `posts_unpublish` | Write | Remove published post from platform (keeps Zernio record) |
| `posts_retry` | Write | Retry failed posts |
| `media_upload` | Write | URL → presign → GCS upload → publicUrl |
| `analytics_posts` | RO | Per-post engagement metrics, sortable |
| `analytics_insights` | RO | Aggregated: best_time, content_decay, daily_metrics, posting_frequency |
| `queue_preview` | RO | Next upcoming queue slots for scheduling context |

### Design decisions from mcp-tool-reviewer audit

- **Cut 3 thin aliases** (`posts_publish_now`, `posts_cross_post`, `posts_list_failed`) — pre-filled params, not real tools. Documented as patterns in `posts_create`/`posts_list` docstrings instead.
- **Redesigned media_upload** — base64 is wrong (33% size overhead, context-window hostile, bypasses Zernio's GCS presign flow). Accept URL instead.
- **Added `posts_get`** — essential for post-creation status checks.
- **Added `accounts_health`** — token expiry checks ("why didn't my post go through?").
- **Added `posts_unpublish`** — distinct from `posts_delete` (draft-only); published posts need unpublish.
- **Split analytics** — `analytics_posts` (per-post) + `analytics_insights` (aggregated with type enum).
- **Added `queue_preview`** — scheduling context for mobile users.
- **Fixed naming** — consistent `noun_verb` pattern throughout.
- **Parameter ergonomics** — `posts_create` documents 3 modes with examples; API's confusing `source: "late"` renamed to `origin: "via_zernio"`.

## Capabilities

### New Capabilities

- `social-accounts`: List connected accounts, inspect token health, and browse profile (brand) groupings
- `post-management`: Create, get, list, delete, unpublish, and retry social media posts across platforms with self-describing publish modes (immediate/scheduled/draft)
- `media-upload`: Accept media URL, fetch bytes server-side, upload via Zernio's presigned GCS flow, return publicUrl for attachment to posts
- `social-analytics`: Per-post engagement metrics and aggregated insights (best posting time, content decay, daily metrics, posting frequency)
- `queue-management`: Preview upcoming queue slots for scheduling context
- `server-infrastructure`: FastMCP server setup, Zernio API client, OAuth authentication (client_id + client_secret for Claude.ai), SSE transport, and deployment configuration

### Modified Capabilities

(none — greenfield project)

## Impact

- **New dependencies**: `fastmcp`, `httpx`, `pydantic-settings`, Python 3.12+, `uv` for dependency management
- **Infrastructure**: New subdomain `mcp-zernio.cdit-dev.de` behind Caddy on Hetzner (nebula-1), new Komodo stack on ubuntu-smurf-mirror
- **Secrets**: `ZERNIO_API_KEY`, OAuth `CLIENT_ID` + `CLIENT_SECRET`, Keycloak issuer/audience — all via Komodo vault `[[VAR]]` syntax
- **External APIs**: Zernio REST API v1 (accounts, posts, media presign, analytics, queue)
- **Auth**: OAuth client_id + client_secret (mandatory for Claude.ai connectors) + Keycloak JWT from `cdit-mcp` realm
- **Caddy**: Two-handle pattern (`.well-known/oauth-protected-resource` rewrite + catch-all), `flush_interval -1` for SSE
- **Claude.ai config**: Register as custom MCP connector with OAuth credentials
