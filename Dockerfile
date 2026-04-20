FROM python:3.14-slim AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/
RUN uv sync --frozen --no-dev

# --- Runtime ---
FROM python:3.14-slim

RUN groupadd -r mcp && useradd -r -g mcp -d /app mcp

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src/ src/

ENV PATH="/app/.venv/bin:$PATH" \
    MCP_TRANSPORT=http \
    HOST=0.0.0.0 \
    PORT=8717

EXPOSE 8717

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python3 -c "import urllib.request,json,sys; r=urllib.request.urlopen('http://localhost:8000/health',timeout=3); d=json.loads(r.read()); sys.exit(0 if d.get('status')=='healthy' else 1)"

USER mcp
ENTRYPOINT ["mcp-zernio"]
