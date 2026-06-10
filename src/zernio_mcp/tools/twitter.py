"""Twitter engagement tools: retweet, unretweet, bookmark, follow."""

from __future__ import annotations

from mcp.types import ToolAnnotations

from zernio_mcp.server import mcp
from zernio_mcp.client import ZernioAPIError
from zernio_mcp.tools._common import client, error


@mcp.tool(
    title="Twitter retweet",
    tags={"social", "twitter", "write"},
    annotations=ToolAnnotations(title="Twitter retweet", readOnlyHint=False, idempotentHint=False, openWorldHint=True),
)
async def twitter_retweet(account_id: str, tweet_id: str) -> dict:
    """[social] Retweet a tweet. This is publicly visible — confirm with user first.

    Args:
        account_id: Your Twitter account ID.
        tweet_id: The tweet to retweet.
    """
    try:
        return await client().post("/v1/twitter/retweet", {"accountId": account_id, "tweetId": tweet_id})
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Twitter unretweet",
    tags={"social", "twitter", "write"},
    annotations=ToolAnnotations(title="Twitter unretweet", readOnlyHint=False, idempotentHint=True, openWorldHint=True),
)
async def twitter_unretweet(account_id: str, tweet_id: str) -> dict:
    """[social] Undo a retweet.

    Args:
        account_id: Your Twitter account ID.
        tweet_id: The tweet to unretweet.
    """
    try:
        return await client().delete("/v1/twitter/retweet", accountId=account_id, tweetId=tweet_id)
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Twitter bookmark",
    tags={"social", "twitter", "write"},
    annotations=ToolAnnotations(title="Twitter bookmark", readOnlyHint=False, idempotentHint=False, openWorldHint=True),
)
async def twitter_bookmark(account_id: str, tweet_id: str) -> dict:
    """[social] Bookmark a tweet (private — only visible to you).

    Args:
        account_id: Your Twitter account ID.
        tweet_id: The tweet to bookmark.
    """
    try:
        return await client().post("/v1/twitter/bookmark", {"accountId": account_id, "tweetId": tweet_id})
    except ZernioAPIError as e:
        return error(e.message)


@mcp.tool(
    title="Twitter follow",
    tags={"social", "twitter", "write"},
    annotations=ToolAnnotations(title="Twitter follow", readOnlyHint=False, idempotentHint=False, openWorldHint=True),
)
async def twitter_follow(account_id: str, target_user_id: str) -> dict:
    """[social] Follow a Twitter user. This is publicly visible — confirm with user first.

    Args:
        account_id: Your Twitter account ID.
        target_user_id: The user to follow.
    """
    try:
        return await client().post("/v1/twitter/follow", {"accountId": account_id, "targetUserId": target_user_id})
    except ZernioAPIError as e:
        return error(e.message)
