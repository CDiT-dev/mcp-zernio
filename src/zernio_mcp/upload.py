"""Browser-based media upload routes.

Provides a drag-and-drop upload page at /upload so users can upload images
from Claude.ai without passing base64 through the MCP tool call (which
crashes the session due to payload size limits).

Flow:
  1. Claude calls media_get_upload_link() -> returns URL to /upload page
  2. User opens the link, drops an image
  3. Browser POSTs multipart form to /upload
  4. Server presigns + uploads to GCS, returns publicUrl
  5. User copies URL back (or Claude picks it up from tool context)
"""

from __future__ import annotations

import secrets
import time

from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse

from zernio_mcp.client import (
    ALLOWED_MEDIA_TYPES,
    MAX_MEDIA_SIZE,
    ZernioAPIError,
    ZernioClient,
    get_shared_client,
)
from zernio_mcp.config import settings

# In-memory store for completed uploads so the tool can retrieve the URL.
# Key: upload token, Value: (publicUrl, timestamp)
_upload_results: dict[str, tuple[str, float]] = {}
_RESULT_TTL = 600  # 10 minutes

# Pending upload tokens (valid for 10 min)
_upload_tokens: dict[str, float] = {}


def _cleanup_expired() -> None:
    now = time.monotonic()
    for store in (_upload_results, _upload_tokens):
        expired = [k for k, v in store.items()
                   if (now - (v[1] if isinstance(v, tuple) else v)) > _RESULT_TTL]
        for k in expired:
            del store[k]


def create_upload_token() -> str:
    """Create a short-lived token that authorizes one upload."""
    _cleanup_expired()
    token = secrets.token_urlsafe(32)
    _upload_tokens[token] = time.monotonic()
    return token


def get_upload_result(token: str) -> str | None:
    """Retrieve the publicUrl for a completed upload, if available."""
    _cleanup_expired()
    entry = _upload_results.get(token)
    if entry:
        return entry[0]
    return None


_UPLOAD_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Upload Media — Zernio</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0a0a0a; color: #e5e5e5;
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; padding: 1rem;
  }
  .card {
    background: #171717; border: 1px solid #262626; border-radius: 12px;
    padding: 2rem; max-width: 480px; width: 100%; text-align: center;
  }
  h1 { font-size: 1.25rem; margin-bottom: 0.5rem; }
  p.sub { color: #a3a3a3; font-size: 0.875rem; margin-bottom: 1.5rem; }
  .drop {
    border: 2px dashed #404040; border-radius: 8px; padding: 3rem 1rem;
    cursor: pointer; transition: border-color 0.2s, background 0.2s;
  }
  .drop.over { border-color: #3b82f6; background: rgba(59,130,246,0.05); }
  .drop input { display: none; }
  .drop-label { color: #a3a3a3; font-size: 0.875rem; }
  .drop-label strong { color: #e5e5e5; }
  .preview { margin-top: 1rem; max-width: 100%; max-height: 200px; border-radius: 6px; }
  .result {
    margin-top: 1rem; padding: 0.75rem; background: #1e1e1e;
    border-radius: 6px; word-break: break-all; font-size: 0.8rem;
    font-family: monospace; user-select: all; color: #4ade80;
  }
  .btn {
    margin-top: 1rem; padding: 0.5rem 1.25rem; border: none;
    border-radius: 6px; font-size: 0.875rem; cursor: pointer;
    background: #3b82f6; color: #fff; transition: opacity 0.2s;
  }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn.copy { background: #22c55e; }
  .error { color: #f87171; margin-top: 0.75rem; font-size: 0.85rem; }
  .spinner { display: none; margin: 1rem auto 0; width: 24px; height: 24px;
    border: 3px solid #333; border-top-color: #3b82f6;
    border-radius: 50%; animation: spin 0.6s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="card">
  <h1>Upload Media</h1>
  <p class="sub">Drop an image or video to get a public URL for Zernio posts.</p>
  <div class="drop" id="drop">
    <input type="file" id="file" accept="image/*,video/*">
    <p class="drop-label"><strong>Click or drag</strong> a file here</p>
  </div>
  <div class="spinner" id="spinner"></div>
  <div class="error" id="error"></div>
  <div class="result" id="result" style="display:none"></div>
  <button class="btn copy" id="copyBtn" style="display:none">Copy URL</button>
</div>
<script>
const TOKEN = "__TOKEN__";
const drop = document.getElementById("drop");
const fileInput = document.getElementById("file");
const spinner = document.getElementById("spinner");
const errorEl = document.getElementById("error");
const resultEl = document.getElementById("result");
const copyBtn = document.getElementById("copyBtn");

drop.addEventListener("click", () => fileInput.click());
drop.addEventListener("dragover", e => { e.preventDefault(); drop.classList.add("over"); });
drop.addEventListener("dragleave", () => drop.classList.remove("over"));
drop.addEventListener("drop", e => {
  e.preventDefault(); drop.classList.remove("over");
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

async function handleFile(file) {
  errorEl.textContent = "";
  resultEl.style.display = "none";
  copyBtn.style.display = "none";

  // Show preview for images
  if (file.type.startsWith("image/")) {
    let existing = drop.querySelector(".preview");
    if (existing) existing.remove();
    const img = document.createElement("img");
    img.className = "preview";
    img.src = URL.createObjectURL(file);
    drop.appendChild(img);
  }

  spinner.style.display = "block";
  const form = new FormData();
  form.append("file", file);
  form.append("token", TOKEN);

  try {
    const resp = await fetch("./upload", { method: "POST", body: form });
    const data = await resp.json();
    spinner.style.display = "none";
    if (data.error) {
      errorEl.textContent = data.error;
    } else {
      resultEl.textContent = data.publicUrl;
      resultEl.style.display = "block";
      copyBtn.style.display = "inline-block";
    }
  } catch (e) {
    spinner.style.display = "none";
    errorEl.textContent = "Upload failed: " + e.message;
  }
}

copyBtn.addEventListener("click", () => {
  navigator.clipboard.writeText(resultEl.textContent);
  copyBtn.textContent = "Copied!";
  setTimeout(() => copyBtn.textContent = "Copy URL", 1500);
});
</script>
</body>
</html>
"""


def register_upload_routes(mcp) -> None:
    """Register /upload GET and POST routes on the FastMCP server."""

    @mcp.custom_route("/upload", methods=["GET"])
    async def upload_page(request: Request) -> HTMLResponse:
        token = request.query_params.get("token", "")
        if not token or token not in _upload_tokens:
            return HTMLResponse(
                "<h1>Invalid or expired upload link</h1>"
                "<p>Please request a new upload link from Claude.</p>",
                status_code=403,
            )
        html = _UPLOAD_HTML.replace("__TOKEN__", token)
        return HTMLResponse(html)

    @mcp.custom_route("/upload", methods=["POST"])
    async def upload_handler(request: Request) -> JSONResponse:
        form = await request.form()
        token = form.get("token", "")
        if not token or token not in _upload_tokens:
            return JSONResponse({"error": "Invalid or expired upload token"}, status_code=403)

        upload = form.get("file")
        if not upload or not hasattr(upload, "read"):
            return JSONResponse({"error": "No file provided"}, status_code=400)

        content_type = upload.content_type or ""
        if content_type not in ALLOWED_MEDIA_TYPES:
            return JSONResponse(
                {"error": f"Unsupported file type: {content_type}. "
                          f"Supported: {', '.join(sorted(ALLOWED_MEDIA_TYPES))}"},
                status_code=400,
            )

        data = await upload.read()
        if len(data) > MAX_MEDIA_SIZE:
            return JSONResponse(
                {"error": f"File too large ({len(data) / 1024 / 1024:.1f}MB). Max: 100MB."},
                status_code=400,
            )

        try:
            c = ZernioClient(http_client=get_shared_client())
            ext = content_type.split("/")[-1].replace("quicktime", "mov")
            file_name = upload.filename or f"upload.{ext}"
            presign = await c.presign_media(file_name, content_type)
            await c.upload_to_gcs(presign["uploadUrl"], data, content_type)
        except ZernioAPIError as e:
            return JSONResponse({"error": e.message}, status_code=500)

        public_url = presign["publicUrl"]

        # Store result so the tool can poll for it
        _upload_results[token] = (public_url, time.monotonic())
        # Consume the token (one-time use)
        _upload_tokens.pop(token, None)

        return JSONResponse({"publicUrl": public_url})
