"""Media tools: URL-based upload + browser upload for Claude.ai."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError, SSRFError
from zernio_mcp.config import settings
from zernio_mcp.tools._common import client, error
from zernio_mcp.upload import create_upload_token, get_upload_result


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def media_upload(
    url: str,
    file_name: str = "upload",
) -> dict:
    """[social] Upload media from a URL for use in posts. Returns publicUrl.

    Provide a publicly accessible HTTPS URL pointing to an image or video.
    Supported formats: JPG, PNG, WebP, GIF, MP4, MOV, WebM.

    If the user has a local image (e.g. pasted inline), call media_get_upload_link
    first to get a browser upload page, then use the returned publicUrl here or
    in posts_create directly.
    """
    c = client()
    try:
        data, content_type = await c.fetch_url_bytes(url)
        ext = content_type.split("/")[-1].replace("quicktime", "mov")
        presign = await c.presign_media(f"{file_name}.{ext}", content_type)
        await c.upload_to_gcs(presign["uploadUrl"], data, content_type)
        return {"publicUrl": presign["publicUrl"]}
    except SSRFError as e:
        return error(str(e))
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def media_get_upload_link() -> dict:
    """[social] Get a browser upload link for images/videos.

    Use this when the user wants to upload a local file (e.g. pasted an image
    in Claude.ai). Returns a one-time upload URL that the user opens in their
    browser to drag-and-drop a file. After uploading, call media_check_upload
    with the returned token to get the publicUrl.

    Returns: {uploadPageUrl, token}
    """
    token = create_upload_token()
    base = settings.public_url.rstrip("/")
    return {
        "uploadPageUrl": f"{base}/upload?token={token}",
        "token": token,
        "instructions": "Give this link to the user. After they upload, call media_check_upload with the token to get the publicUrl.",
    }


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def media_check_upload(token: str) -> dict:
    """[social] Check if a browser upload has completed and get the publicUrl.

    Call this after giving the user an upload link from media_get_upload_link.
    If the upload is done, returns {publicUrl}. If still pending, returns
    {status: "pending"}.
    """
    url = get_upload_result(token)
    if url:
        return {"publicUrl": url}
    return {"status": "pending", "message": "Upload not yet completed. Ask the user if they've finished uploading."}
