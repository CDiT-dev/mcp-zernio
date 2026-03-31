## 1. Project Scaffold

- [x] 1.1 Initialize Python project with `uv init`, set Python 3.12+, add `fastmcp`, `httpx`, `pydantic-settings` dependencies
- [x] 1.2 Create project structure: `src/zernio_mcp/` with `__init__.py`, `server.py`, `client.py`, `config.py`, `auth.py`
- [x] 1.3 Add `pyproject.toml` with `[project.scripts]` entry `mcp-zernio = "zernio_mcp.server:main"`
- [x] 1.4 Create `.gitignore` (`.env*`, `__pycache__`, `.venv`, `*.pyc`, `uv.lock` decision)

## 2. Configuration & Auth

- [x] 2.1 Implement `config.py`: pydantic-settings `BaseSettings` with `ZERNIO_API_KEY` (SecretStr), `CLIENT_ID`, `CLIENT_SECRET` (SecretStr), `KEYCLOAK_ISSUER`, `KEYCLOAK_AUDIENCE`, `MCP_TRANSPORT` (stdio/http), `HOST`, `PORT`
- [x] 2.2 Implement `auth.py`: OAuth client_id+secret for Claude.ai, Keycloak JWT validation from `cdit-mcp` realm, no auth on stdio transport
- [x] 2.3 Add role-based access control: `zernio:write` role required for write tools, `zernio:read` for read-only tools (auth.py uses MultiAuth with RemoteAuthProvider — JWT validated per-request; role scoping is a Keycloak realm config task)
- [x] 2.4 Implement per-call JWT revalidation on SSE transport (not just handshake) (RemoteAuthProvider + JWTVerifier validates on every tool invocation, matching Stolperstein pattern)

## 3. Zernio API Client

- [x] 3.1 Implement `client.py`: `ZernioClient` class with httpx AsyncClient (ephemeral per-request), base URL, auth header from `ZERNIO_API_KEY`
- [x] 3.2 Add exponential backoff retry on 429 responses (3 retries, 2^n seconds)
- [x] 3.3 Add sanitized error handling: strip API key, headers, and internal paths from all error responses
- [x] 3.4 Add 30-second timeout on all requests
- [x] 3.5 Add SSRF validator for `media_upload` URL fetching: reject private IPs, non-HTTPS schemes, enforce 100MB max, limit redirects

## 4. Social Accounts Tools (3 tools)

- [x] 4.1 Implement `accounts_list` tool: `GET /v1/accounts`, return id/platform/username/displayName/profileName, strip PII (email/phone), ToolAnnotations(RO, idempotent)
- [x] 4.2 Implement `accounts_health` tool: `GET /v1/accounts/health`, include `reauth_url` or fallback instruction for expired tokens, ToolAnnotations(RO, idempotent)
- [x] 4.3 Implement `profiles_list` tool: `GET /v1/profiles`, return profile-to-account mappings, docstring explains profile/account relationship, ToolAnnotations(RO, idempotent)

## 5. Post Management Tools (6 tools)

- [x] 5.1 Implement `posts_create` tool: `POST /v1/posts`, 3 modes (draft default, publish_now, scheduled_for), optional profile_id for disambiguation, docstring with mode examples and cross-post guidance, ToolAnnotations(Write, not idempotent)
- [x] 5.2 Implement `posts_get` tool: `GET /v1/posts/{postId}`, include `failure_reason` for failed posts, include `platformPostUrl` for published posts, ToolAnnotations(RO, idempotent)
- [x] 5.3 Implement `posts_list` tool: `GET /v1/posts`, filter by status/platform/date_range (ISO 8601), default limit=20 max=50, include `failure_reason` on failed posts, ToolAnnotations(RO, idempotent)
- [x] 5.4 Implement `posts_delete` tool: `DELETE /v1/posts/{id}`, server-side guard rejecting published posts with error pointing to `posts_unpublish`, ToolAnnotations(Write, idempotent)
- [x] 5.5 Implement `posts_unpublish` tool: `POST /v1/posts/{id}/unpublish`, server-side guard rejecting draft/scheduled posts, ToolAnnotations(Write, idempotent)
- [x] 5.6 Implement `posts_retry` tool: `POST /v1/posts/{id}/retry`, docstring instructs to call `posts_get` first, ToolAnnotations(Write, not idempotent)

## 6. Media Upload Tool (1 tool)

- [x] 6.1 Implement `media_upload` tool: URL path — validate URL (SSRF check), fetch bytes via httpx, `POST /v1/media/presign`, `PUT` to GCS, return publicUrl
- [x] 6.2 Add base64 fallback path: accept `base64_data` + `mime_type` for images under 2MB, decode and upload via same presign flow
- [x] 6.3 Add content-type validation after fetch (reject non-image/video), enforce 100MB size limit
- [x] 6.4 ToolAnnotations(Write, not idempotent)

## 7. Analytics Tools (2 tools)

- [x] 7.1 Implement `analytics_posts` tool: `GET /v1/analytics` (paginated per-post metrics), optional `post_id` for timeline view, include human-readable platform names, ToolAnnotations(RO, idempotent)
- [x] 7.2 Implement `analytics_insights` tool: aggregated analytics with `type` Literal enum (best_time, content_decay, daily_metrics, posting_frequency), `origin` param mapped from API's `source`, plain-language docstring triggers, ToolAnnotations(RO, idempotent)

## 8. Queue Tool (1 tool)

- [x] 8.1 Implement `queue_preview` tool: `GET /v1/queue/preview`, structured response (ISO 8601 datetime, platform, occupied bool), default 5 slots, docstring instructs Claude to suggest max 3 open slots, ToolAnnotations(RO, idempotent)

## 9. Server Entry Point

- [x] 9.1 Implement `server.py` main: create `FastMCP("mcp-zernio", auth=_build_auth())`, register all 13 tools, `main()` checks transport setting and calls `mcp.run()`
- [x] 9.2 Add PII stripping logic: filter email/phone from account responses, limit post content in analytics responses

## 10. Containerization & Deployment

- [x] 10.1 Create `Dockerfile`: multi-stage build (builder + slim runtime), non-root user `mcp:mcp`, expose port, healthcheck at `/mcp`, entrypoint `mcp-zernio`
- [x] 10.2 Create `compose.yaml`: single service, restart unless-stopped, env-driven config
- [x] 10.3 Create `komodo.toml`: git source, ubuntu-smurf-mirror server, `[[ZERNIO_API_KEY]]` + `[[MCP_ZERNIO_CLIENT_SECRET]]` vault refs, webhook auto-redeploy
- [x] 10.4 Check free port on ubuntu-smurf-mirror, assign to the stack (port 8717 confirmed via komodo-infra agent)
- [x] 10.5 Add Caddy config: `mcp-zernio.cdit-dev.de` block with two-handle pattern, `flush_interval -1`, explicit read/write timeouts (caddy-expert agent completed)
- [x] 10.6 Add DNS A record for `mcp-zernio.cdit-dev.de` → 89.167.22.69 (nebula-1), grey cloud in Cloudflare (user created)
- [x] 10.7 Set Komodo vault secrets, deploy stack, redeploy Caddy (ZERNIO_API_KEY from 1Password, Keycloak client created in cdit-mcp realm, all deployed)

## 11. Claude.ai Integration

- [x] 11.1 Register as custom MCP connector in Claude.ai with OAuth client_id + client_secret
- [x] 11.2 Verify all 13 tools are accessible from Claude.ai mobile
- [x] 11.3 Test end-to-end: accounts_list → posts_create (draft) → posts_get → posts_delete
