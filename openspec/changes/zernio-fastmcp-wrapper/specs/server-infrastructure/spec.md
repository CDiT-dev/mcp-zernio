## ADDED Requirements

### Requirement: OAuth authentication for Claude.ai connectors
The server MUST implement OAuth client_id + client_secret authentication as the primary auth mechanism. This is mandatory for Claude.ai custom MCP connectors. Keycloak JWT from the `cdit-mcp` realm SHALL be supported as secondary auth. No auth SHALL be required on stdio transport (local dev only).

#### Scenario: Claude.ai connector authenticates via OAuth
- **WHEN** a request arrives with valid OAuth client_id + client_secret
- **THEN** the request is authenticated and tool calls proceed

#### Scenario: Keycloak JWT authentication
- **WHEN** a request arrives with a valid JWT from the `cdit-mcp` Keycloak realm
- **THEN** the request is authenticated

#### Scenario: No auth on stdio
- **WHEN** the server is started with `transport=stdio`
- **THEN** no authentication is required

#### Scenario: Invalid credentials
- **WHEN** a request arrives with invalid OAuth credentials or expired JWT
- **THEN** the server returns 401 Unauthorized

### Requirement: Role-based access control for write tools
Write tools (`posts_create`, `posts_delete`, `posts_unpublish`, `posts_retry`, `media_upload`) SHALL require a specific Keycloak role (e.g., `zernio:write`). Read-only tools SHALL require only `zernio:read` or base realm membership. On SSE transport, the JWT MUST be re-validated on every tool invocation, not just at handshake, to ensure revoked tokens are caught mid-session.

#### Scenario: Write tool without write role
- **WHEN** a JWT-authenticated user without the `zernio:write` role calls `posts_create`
- **THEN** the server returns 403 Forbidden

#### Scenario: JWT revoked mid-SSE session
- **WHEN** a JWT is revoked in Keycloak while an SSE session is active
- **THEN** the next tool invocation on that session re-validates the JWT and returns 401

### Requirement: Zernio API client with error handling
The server SHALL use httpx AsyncClient (ephemeral, per-request) for all Zernio REST API calls. The client MUST:
- Set timeout to 30 seconds
- Implement exponential backoff on 429 (rate limit) responses (3 retries, 2^n seconds)
- Return sanitized error responses (no internal stack traces or raw API keys in error messages)
- Use `SecretStr` for the `ZERNIO_API_KEY` in config

#### Scenario: Zernio API returns 429
- **WHEN** the Zernio API returns HTTP 429
- **THEN** the client retries up to 3 times with exponential backoff (1s, 2s, 4s)

#### Scenario: Zernio API is down
- **WHEN** the Zernio API returns 5xx or times out
- **THEN** the tool returns a human-readable error: "Zernio API is currently unavailable. Please try again in a few minutes."

#### Scenario: API key not leaked in errors
- **WHEN** any error occurs during a Zernio API call
- **THEN** the error response MUST NOT contain the API key, request headers, or internal paths

### Requirement: PII stripping from tool responses
Before returning Zernio API data to the MCP caller, the server MUST strip fields that Claude does not need to perform its task (e.g., email addresses, phone numbers from account OAuth data). Only return fields necessary for tool functionality: IDs, platform names, usernames, display names, metrics, post content, and URLs.

#### Scenario: accounts_list strips email
- **WHEN** the Zernio API returns an email field in account data
- **THEN** the MCP tool response omits the email field

#### Scenario: analytics responses use metrics only
- **WHEN** `analytics_posts` returns engagement data
- **THEN** the response includes metric values and platform context but does not re-include full post content bodies

### Requirement: Configuration via pydantic-settings
The server SHALL use pydantic-settings `BaseSettings` for all configuration. Sensitive values (`ZERNIO_API_KEY`, `CLIENT_SECRET`) MUST use `SecretStr`. All config SHALL come from environment variables.

#### Scenario: Required env vars missing
- **WHEN** the server starts without `ZERNIO_API_KEY`
- **THEN** startup fails with a clear error message listing the missing variable

#### Scenario: Transport selection
- **WHEN** `MCP_TRANSPORT=http` is set
- **THEN** the server starts with SSE/streamable-HTTP transport on the configured host:port

### Requirement: Deployment follows CDiT pattern
The server SHALL be deployed as a Docker container on ubuntu-smurf-mirror via Komodo, behind Caddy on nebula-1. Caddy SHALL use the two-handle pattern (`.well-known/oauth-protected-resource` rewrite + catch-all) with `flush_interval -1` for SSE. DNS SHALL be an A record for `mcp-zernio.cdit-dev.de` pointing to 89.167.22.69 (nebula-1), grey cloud in Cloudflare. Secrets SHALL use Komodo vault `[[VAR]]` syntax.

#### Scenario: Docker container starts
- **WHEN** the container is started with required env vars
- **THEN** the FastMCP server is accessible on the configured port with health check at `/mcp`

#### Scenario: Non-root container execution
- **WHEN** the Docker container runs
- **THEN** the process MUST run as a non-root user (via `USER` directive in Dockerfile)

#### Scenario: Caddy proxies SSE correctly
- **WHEN** Claude.ai connects via SSE through Caddy
- **THEN** SSE events stream without buffering due to `flush_interval -1`

### Requirement: Project uses uv for dependency management
The project SHALL use `uv` for all Python dependency management: `uv sync` for installation, `uv run` for execution, `uv.lock` for the lockfile. No pip, poetry, or pipenv.

#### Scenario: Fresh clone setup
- **WHEN** a developer clones the repo and runs `uv sync`
- **THEN** all dependencies are installed and `uv run mcp-zernio` starts the server
