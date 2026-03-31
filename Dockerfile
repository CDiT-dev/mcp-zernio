FROM python:3.12-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/
RUN uv sync --frozen --no-dev

# --- Runtime ---
FROM python:3.12-slim

RUN groupadd -r mcp && useradd -r -g mcp -d /app mcp

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ src/

ENV PATH="/app/.venv/bin:$PATH" \
    MCP_TRANSPORT=http \
    HOST=0.0.0.0 \
    PORT=8717

EXPOSE 8717

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import httpx; httpx.get('http://localhost:8717/mcp')" || exit 1

USER mcp
ENTRYPOINT ["mcp-zernio"]
