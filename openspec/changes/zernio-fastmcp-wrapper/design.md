## Context

CDiT operates several Python/FastMCP MCP servers (Stolperstein, Watermelon, Lexoffice) following an identical infrastructure pattern. This server wraps the Zernio REST API to expose social media management tools via Claude.ai/mobile. The Zernio API is well-documented (OpenAPI spec, LLM-optimized docs) and uses standard REST patterns with API key auth.

The primary user is Casey on Claude mobile — quick social media tasks: post, check status, review analytics. Secondary use: any Claude.ai session with the MCP connector enabled.

## Goals / Non-Goals

**Goals:**
- 13 MCP tools covering the full social media lifecycle (accounts → posts → analytics)
- OAuth client+secret auth for Claude.ai connector (mandatory)
- Presigned URL media upload flow (no base64)
- Self-describing tools that Claude picks correctly on first try
- Deployed at `mcp-zernio.cdit-dev.de` following CDiT infra pattern exactly

**Non-Goals:**
- Crisp MCP integration (separate server)
- Queue management beyond `queue_preview` (v2)
- Webhook setup or real-time notifications
- Messages, comments, or reviews endpoints
- Multi-tenant support (single Zernio API key)

## Decisions

### 1. Direct REST API vs. `zernio-sdk` Python package

**Decision: Direct REST via httpx.**

The `zernio-sdk` Python package wraps the same REST API but adds a dependency we don't control, may lag behind API changes, and its MCP extension (`zernio-sdk[mcp]`) is stdio-only. Using httpx directly gives us full control over request shaping, error handling, and the presigned upload flow.

*Alternative considered:* `pip install zernio-sdk` — rejected because it adds an opaque dependency layer over a simple REST API and doesn't expose presign endpoints cleanly.

### 2. Auth: OAuth client_id + client_secret

**Decision: OAuth mandatory for Claude.ai, Keycloak JWT as secondary.**

Claude.ai custom MCP connectors ONLY work with OAuth (client_id + client_secret). This is a hard requirement. We follow the Stolperstein MultiAuth pattern: OAuth for Claude.ai, Keycloak JWT from `cdit-mcp` realm for other clients, no auth on stdio for local dev.

*Alternative considered:* Bearer token only — rejected because Claude.ai connectors don't support it.

### 3. Media upload: URL-based presign flow

**Decision: Accept URL → fetch server-side → presign → PUT to GCS → return publicUrl.**

Base64 was rejected after mcp-tool-reviewer audit: 33% size overhead, context-window hostile, bypasses Zernio's optimized GCS presign flow. The URL approach:
1. Tool accepts a publicly accessible URL
2. Server fetches bytes with httpx (with SSRF protections — see Risks)
3. Calls `POST /v1/media/presign` to get upload URL
4. Streams bytes to GCS via `PUT`
5. Returns `publicUrl` for use in `posts_create`

*Alternative considered:* Base64 input — rejected. Also considered: `POST /v1/media/upload-direct` (simpler but doesn't support all file types per API docs).

### 4. Flat server.py, no tool sub-modules

**Decision: All 13 tools in a single `server.py`.**

Follows the Stolperstein pattern. 13 tools is manageable in one file. Each tool is a thin async function that calls the Zernio client and returns a dict. The Zernio HTTP client lives in a separate `client.py` module.

### 5. Analytics split: two tools, not one

**Decision: `analytics_posts` (per-post metrics) + `analytics_insights` (aggregated with type enum).**

Six Zernio analytics endpoints collapse into two tools: per-post metrics (sortable, paginated) and aggregated insights (best_time, content_decay, daily_metrics, posting_frequency selected via `type` parameter). This keeps the surface small while giving the LLM clear semantic separation.

### 6. Parameter naming: remap confusing API values

**Decision: Rename `source: "late"` → `origin: "via_zernio"` in tool params.**

The Zernio API uses `"late"` to mean "posted via Zernio" — confusing for LLMs and humans. Our wrapper maps user-friendly enum values to API values server-side. Similar remapping for any other non-obvious API params.

### 7. Deployment: identical to Stolperstein

**Decision: Docker on ubuntu-smurf-mirror, Komodo stack, Caddy on nebula-1.**

No innovation on infrastructure. Copy the exact pattern:
- `Dockerfile`: multi-stage build, non-root user, `/data` volume (if needed for caching)
- `compose.yaml`: single service, env-driven config
- `komodo.toml`: git source, `[[SECRET]]` vault refs, webhook auto-redeploy
- Caddy: two-handle pattern, `flush_interval -1`, DNS A record to 89.167.22.69
- Port: TBD (check what's free on ubuntu-smurf-mirror)

### 8. Python tooling: uv

**Decision: uv for all dependency management.**

`uv sync` for deps, `uv run` for execution, `uv.lock` for lockfile. No pip/poetry/pipenv.

## Project structure

```
mcp-zernio/
├── src/zernio_mcp/
│   ├── __init__.py
│   ├── server.py          # FastMCP instance + 13 tool definitions
│   ├── client.py          # ZernioClient (httpx async, all REST calls)
│   ├── config.py          # Settings (pydantic-settings BaseSettings)
│   └── auth.py            # OAuth + Keycloak MultiAuth setup
├── Dockerfile
├── compose.yaml
├── komodo.toml
├── pyproject.toml          # uv project, fastmcp + httpx + pydantic-settings
└── README.md
```

## Risks / Trade-offs

### [SSRF via media_upload URL] → Whitelist + validation
The `media_upload` tool fetches arbitrary URLs server-side. Mitigations:
- Reject private/internal IPs (10.x, 172.16-31.x, 192.168.x, 127.x, ::1, link-local)
- Reject non-HTTP(S) schemes
- Set strict httpx timeout (30s) and max response size (5GB cap from Zernio, enforce 100MB practical limit)
- No redirect following (or limit to same-origin redirects)

### [Single API key = full account access] → Accept for v1
One `ZERNIO_API_KEY` grants full write access to all connected social accounts. This is inherent to Zernio's API design. Mitigation: key stored in Komodo vault, never logged, SecretStr in config. Future: per-user key support if multi-tenant needed.

### [Accidental publishing] → posts_create defaults to draft
`posts_create` defaults to draft mode (neither `publishNow` nor `scheduledFor` set). Immediate publish requires explicit `publish_now=True`. Claude's tool call must include the flag intentionally.

### [Zernio API rate limits] → httpx retry with backoff
Unknown rate limits for the Zernio API. Implement exponential backoff on 429 responses. Default `posts_list` limit capped at 20 (API allows 100 but wasteful for context window).

### [OAuth token management] → Follow Stolperstein pattern exactly
OAuth token refresh, JWKS caching, and token validation follow the proven Stolperstein implementation. No custom crypto.

## Open Questions

1. **Port allocation**: Which port is free on ubuntu-smurf-mirror? Need to check before deployment.
2. **Zernio API rate limits**: Not documented — test during development, add defensive throttling.
3. **Media size limit**: Zernio says 5GB, but practical MCP limit for URL-fetched media? Start with 100MB cap.
4. **Queue endpoints**: `queue_preview` is in scope but the full queue management API is deferred — confirm this is sufficient for MVP.
