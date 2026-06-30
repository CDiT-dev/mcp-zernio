# mcp-zernio

> **Internal / proprietary.** This repository is private and not licensed for
> redistribution. See "License" below.

FastMCP wrapper around the [Zernio](https://zernio.com) social media management
API. Exposes ~90 tools, 3 resources, and 3 guided prompts for posting,
scheduling, inbox/comment management, analytics, and account/profile
administration across Twitter/X, Bluesky, LinkedIn, Facebook, Instagram,
Threads, TikTok, YouTube, Pinterest, and Reddit.

It is part of the CDiT MCP fleet (`mcp-<service>` convention, `src/zernio_mcp/`
layout, hatchling build, `fastmcp>=3.4.2,<4.0.0`).

## What it does

The server is a thin, typed proxy over the Zernio REST API. Almost every write
needs an `accountId` (and often a `profileId`), so the model is steered to
resolve those from resources before spending tool calls.

| Domain | Module | Tools (examples) |
|---|---|---|
| Accounts & groups | `tools/accounts.py` | list / update / delete accounts, follower stats, health, account groups |
| Profiles (brand groupings) | `tools/profiles.py` | profiles CRUD |
| Posts | `tools/posts.py` | create / update / schedule / delete / unpublish / retry / bulk upload |
| Queue & scheduling | `tools/queue.py` | slots CRUD, schedule, preview, next slot, clear |
| Inbox (DMs) | `tools/inbox.py` | list, get conversation, send / edit / delete message |
| Comments | `tools/comments.py` | list, reply, private reply, like, hide, delete |
| Analytics | `tools/analytics.py` | posts, insights, Instagram, YouTube daily |
| Broadcasts | `tools/broadcasts.py` | CRUD |
| Contacts (CRM) | `tools/contacts.py` | CRUD |
| Reviews | `tools/reviews.py` | list, reply |
| Webhooks | `tools/webhooks.py` | CRUD, test, logs |
| Twitter engagement | `tools/twitter.py` | follow, retweet, bookmark |
| Platform helpers | `tools/platform_helpers.py` | Reddit/Pinterest/Instagram/LinkedIn/YouTube helpers |
| Research | `tools/research.py` | feed/search/download helpers |
| Media | `tools/media.py` | upload link, upload, check upload |
| Validation | `tools/validation.py` | validate post, post length, media |
| Logs | `tools/logs.py` | post logs, post detail, connection logs |
| Misc | `tools/misc.py` | usage stats, account-group helpers |

**Resources** (`zernio://` scheme, `resources.py`):
`zernio://accounts`, `zernio://profiles`, `zernio://platforms` (static taxonomy
of per-platform character limits and quirks).

**Prompts** (`prompts.py`): `draft_cross_platform_campaign`, `triage_inbox`,
`weekly_analytics_review`.

**Tool annotations** are set deliberately: `readOnlyHint` for safe reads,
`destructiveHint` for irreversible deletes/unpublishes, `idempotentHint` for
safe-to-retry calls, `openWorldHint` for calls that hit external platforms.

### Inbox web UI

Beyond MCP tools, the HTTP server mounts a browser-based universal inbox at
`/inbox` (`inbox.py`, `inbox_app_*.py`, `inbox_html.py`) and a browser media
upload route (`upload.py`). The inbox is protected by a passphrase
(`INBOX_PASSPHRASE`) with optional magic-link login via Resend
(`RESEND_API_KEY` + `INBOX_EMAIL`); magic links are disabled when the Resend key
is empty.

## Configuration

All config comes from environment variables (`config.py`, pydantic-settings).
Locally, put them in `.env` (gitignored).

| Variable | Required | Default | Notes |
|---|---|---|---|
| `ZERNIO_API_KEY` | yes | — | Zernio API key (secret) |
| `ZERNIO_API_BASE` | no | `https://zernio.com/api` | API base URL |
| `MCP_TRANSPORT` | no | `stdio` | `stdio` or `http` |
| `HOST` | no | `127.0.0.1` | bind host (HTTP) |
| `PORT` | no | `8717` | bind port (HTTP) |
| `MCP_API_KEY` | http only | — | Bearer token; **required** when `MCP_TRANSPORT=http` (server refuses to start unauthenticated) |
| `PUBLIC_URL` | no | `https://mcp-zernio.cdit-dev.de` | external URL used in OAuth metadata |
| `INBOX_PASSPHRASE` | no | — | passphrase for `/inbox` |
| `RESEND_API_KEY` | no | — | Resend key for inbox magic links |
| `INBOX_EMAIL` | no | — | recipient for magic-link delivery |

## Run locally

```bash
uv sync
# stdio (desktop client / local)
ZERNIO_API_KEY=... uv run mcp-zernio
# HTTP (portal-style)
ZERNIO_API_KEY=... MCP_API_KEY=... MCP_TRANSPORT=http uv run mcp-zernio
```

Health checks: `GET /health` and `GET /healthz` return service status, version,
and uptime.

## Auth

- **In-app**: HTTP transport uses a static bearer token (`MCP_API_KEY`) verified
  with a timing-safe compare (`auth.py`). Startup fails fast if the token is
  missing in HTTP mode.
- **At the edge**: in production the container sits behind Caddy with Keycloak
  OIDC (the Komodo stack passes `KEYCLOAK_ISSUER` / `KEYCLOAK_AUDIENCE`). See
  the fleet auth architecture reference for the OIDCProxy pattern.

## Tests

```bash
uv run pytest -q
```

Currently 201 passing, 3 skipped. The suite uses `respx` to mock the Zernio API
(no live calls) and `pytest-asyncio` in auto mode.

## Deployment

Containerized (`Dockerfile`, multi-stage uv build, non-root `mcp` user,
Docker `HEALTHCHECK`). Deployed via Komodo (`komodo.toml`) as a git-based
Docker Compose stack on the CDiT Hetzner fleet, behind Caddy at
`https://mcp-zernio.cdit-dev.de`. Releases are tag-driven via
`.github/workflows/release.yml` (auto version bump on `main`); pushing to `main`
triggers a Komodo redeploy. Secrets are injected from the Komodo vault using
`[[VAR]]` syntax — never commit real keys.

## Layout

```
src/zernio_mcp/
  server.py            FastMCP instance, lifespan, health routes, main()
  config.py            pydantic-settings env config
  auth.py              BearerTokenVerifier
  client.py            shared httpx client + ZernioAPIError
  resources.py         zernio:// resources + platform taxonomy
  prompts.py           guided multi-step prompts
  models.py            typed output models
  inbox*.py, upload.py HTTP routes (inbox UI + media upload)
  tools/               ~90 @mcp.tool definitions grouped by domain
openspec/              spec-driven OpenSpec changes
tests/                 respx-mocked unit tests
```

## License

Proprietary / internal — no open-source license is granted. Do not distribute.
