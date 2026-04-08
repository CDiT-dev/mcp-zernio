"""Inbox tools: conversations and messages (DMs)."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def inbox_list(platform: str | None = None, status: str | None = None, limit: int = 20) -> dict:
    """[social] List conversations (DMs) across platforms.

    Args:
        platform: Optional. Filter by platform.
        status: Optional. Filter by status (e.g., "unread").
        limit: Max results (default 20).
    """
    try:
        return await client().get("/v1/inbox/conversations", platform=platform, status=status, limit=limit)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, idempotentHint=True))
async def inbox_get_conversation(
    conversation_id: str,
    include_messages: bool = True,
    message_limit: int = 20,
) -> dict:
    """[social] Get a conversation and its messages.

    Returns conversation metadata (platform, participant, status) plus
    the most recent messages. Set include_messages=False to get only
    conversation metadata.

    Args:
        conversation_id: The conversation to retrieve.
        include_messages: Include messages (default True).
        message_limit: Max messages to include (default 20).
    """
    try:
        conv = await client().get(f"/v1/inbox/conversations/{conversation_id}")
        if include_messages:
            msgs = await client().get(
                f"/v1/inbox/conversations/{conversation_id}/messages",
                limit=message_limit,
            )
            conv["messages"] = msgs.get("messages", msgs if isinstance(msgs, list) else [])
        return conv
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def inbox_update(conversation_id: str, status: str) -> dict:
    """[social] Update conversation metadata (e.g., mark as read, archive).

    Args:
        conversation_id: The conversation to update.
        status: New status (e.g., "read", "archived").
    """
    try:
        return await client().put(f"/v1/inbox/conversations/{conversation_id}", {"status": status})
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=False))
async def inbox_messages_send(conversation_id: str, content: str) -> dict:
    """[social] Send a reply in a conversation.

    IMPORTANT: Confirm message content with the user before sending.
    This sends a real message to another person.

    Args:
        conversation_id: The conversation to reply in.
        content: Message text.
    """
    try:
        return await client().post(f"/v1/inbox/conversations/{conversation_id}/messages", {"content": content})
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def inbox_message_edit(conversation_id: str, message_id: str, content: str) -> dict:
    """[social] Edit a sent message.

    Args:
        conversation_id: The conversation containing the message.
        message_id: The message to edit.
        content: New message text.
    """
    try:
        return await client().patch(
            f"/v1/inbox/conversations/{conversation_id}/messages/{message_id}",
            {"content": content},
        )
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, idempotentHint=True))
async def inbox_message_delete(conversation_id: str, message_id: str) -> dict:
    """[social] Delete a message from a conversation.

    Args:
        conversation_id: The conversation containing the message.
        message_id: The message to delete.
    """
    try:
        return await client().delete(f"/v1/inbox/conversations/{conversation_id}/messages/{message_id}")
    except ZernioAPIError as e:
        return error(e.message)
