"""Media tools: upload via presign, direct upload."""

from __future__ import annotations

import base64

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, SSRFError, ALLOWED_MEDIA_TYPES
from zernio_mcp.tools._common import client, error

MAX_BASE64_BYTES = 2 * 1024 * 1024  # 2 MB


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def media_upload(
    url: str | None = None,
    base64_data: str | None = None,
    mime_type: str | None = None,
    file_name: str = "upload",
) -> dict:
    """Upload media for use in posts. Returns publicUrl to pass to posts_create.

    Two input modes:
      - URL (preferred): provide a publicly accessible HTTPS URL.
      - Base64 (for mobile camera roll, images under 2MB only):
        provide base64_data and mime_type (e.g., "image/png").

    Supported formats: JPG, PNG, WebP, GIF, MP4, MOV, WebM.
    """
    c = client()
    try:
        if url:
            data, content_type = await c.fetch_url_bytes(url)
            ext = content_type.split("/")[-1].replace("quicktime", "mov")
            presign = await c.presign_media(f"{file_name}.{ext}", content_type)
            await c.upload_to_gcs(presign["uploadUrl"], data, content_type)
            return {"publicUrl": presign["publicUrl"]}

        elif base64_data and mime_type:
            if mime_type.lower() not in ALLOWED_MEDIA_TYPES:
                return error(f"Unsupported MIME type: {mime_type}")
            try:
                raw = base64.b64decode(base64_data)
            except Exception:
                return error("Invalid base64 data")
            if len(raw) > MAX_BASE64_BYTES:
                return error(f"Image exceeds 2MB base64 limit ({len(raw) / 1024 / 1024:.1f}MB). Provide a URL instead.")
            ext = mime_type.split("/")[-1].replace("quicktime", "mov")
            presign = await c.presign_media(f"{file_name}.{ext}", mime_type)
            await c.upload_to_gcs(presign["uploadUrl"], raw, mime_type)
            return {"publicUrl": presign["publicUrl"]}

        else:
            return error("Provide 'url' (HTTPS link) or 'base64_data' + 'mime_type'.")

    except SSRFError as e:
        return error(str(e))
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def media_upload_direct(
    base64_data: str,
    mime_type: str,
    file_name: str = "upload",
) -> dict:
    """Upload media directly (alternative to media_upload for smaller files).

    Uses Zernio's direct upload endpoint instead of the presigned GCS flow.
    Best for small images. For large files or videos, use media_upload with a URL.

    Args:
        base64_data: Base64-encoded file content.
        mime_type: MIME type (e.g., "image/png").
        file_name: Optional filename.
    """
    try:
        raw = base64.b64decode(base64_data)
    except Exception:
        return error("Invalid base64 data")

    try:
        return await client().post("/v1/media/upload-direct", {
            "file": base64_data,
            "fileName": file_name,
            "fileType": mime_type,
        })
    except ZernioAPIError as e:
        return error(e.message)
