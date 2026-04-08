"""Comment tools: list, reply, delete, hide, like, private reply."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def comments_list(
    post_id: str | None = None,
    platform: str | None = None,
    limit: int = 20,
) -> dict:
    """[social] List comments. Without post_id: all comments. With post_id: comments for that post.

    Args:
        post_id: Optional. Filter to a specific post's comments.
        platform: Optional. Filter by platform.
        limit: Max results (default 20).
    """
    try:
        if post_id:
            return await client().get(f"/v1/inbox/comments/{post_id}", platform=platform, limit=limit)
        return await client().get("/v1/inbox/comments", platform=platform, limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def comments_reply(post_id: str, comment_id: str, content: str) -> dict:
    """[social] Reply to a comment. Confirm reply content with the user before sending.

    Args:
        post_id: The post containing the comment.
        comment_id: The comment to reply to.
        content: Reply text.
    """
    try:
        return await client().post(f"/v1/inbox/comments/{post_id}", {
            "commentId": comment_id, "content": content,
        })
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def comments_delete(post_id: str, comment_id: str) -> dict:
    """[social] Delete a comment.

    Args:
        post_id: The post containing the comment.
        comment_id: The comment to delete.
    """
    try:
        return await client().delete(f"/v1/inbox/comments/{post_id}", commentId=comment_id)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def comments_hide(post_id: str, comment_id: str) -> dict:
    """[social] Hide a comment from public view.

    Args:
        post_id: The post containing the comment.
        comment_id: The comment to hide.
    """
    try:
        return await client().post(f"/v1/inbox/comments/{post_id}/{comment_id}/hide")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def comments_like(post_id: str, comment_id: str) -> dict:
    """[social] Like a comment.

    Args:
        post_id: The post containing the comment.
        comment_id: The comment to like.
    """
    try:
        return await client().post(f"/v1/inbox/comments/{post_id}/{comment_id}/like")
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def comments_private_reply(post_id: str, comment_id: str, content: str) -> dict:
    """[social] Send a private reply to a commenter. Confirm with user before sending.

    Args:
        post_id: The post containing the comment.
        comment_id: The comment to privately reply to.
        content: Private message text.
    """
    try:
        return await client().post(f"/v1/inbox/comments/{post_id}/{comment_id}/private-reply", {"content": content})
    except ZernioAPIError as e:
        return error(e.message)
