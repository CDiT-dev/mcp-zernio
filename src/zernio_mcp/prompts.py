"""MCP prompts: guided multi-step workflows over the Zernio tool surface.

These turn the large (90+) tool surface into directed workflows so the client
does far less ad-hoc planning per request. Each prompt returns a single user
message with step-by-step instructions referencing the concrete tools and the
``zernio://`` resources.
"""

from __future__ import annotations

from zernio_mcp.server import mcp


@mcp.prompt(
    name="draft_cross_platform_campaign",
    title="Draft a cross-platform campaign",
    tags={"social", "workflow", "posts"},
)
def draft_cross_platform_campaign(
    topic: str,
    platforms: str = "twitter, linkedin, instagram",
    when: str = "draft",
) -> str:
    """Validate and schedule one message across several platforms.

    Args:
        topic: What the campaign is about.
        platforms: Comma-separated target platforms.
        when: "draft", "now", or an ISO 8601 datetime to schedule for.
    """
    return (
        f"Help me publish a cross-platform campaign about: {topic}\n"
        f"Target platforms: {platforms}\n"
        f"Timing: {when}\n\n"
        "Follow this workflow:\n"
        "1. Read the resource zernio://platforms for character limits and "
        "per-platform quirks (media-required, video-only, native threads).\n"
        "2. Read zernio://accounts to resolve the accountId for each target "
        "platform (call accounts_list only if the resource is unavailable). If "
        "more than one account matches a platform, read zernio://profiles and "
        "ask me which brand profile to use.\n"
        "3. Draft platform-appropriate copy: tighten for short-limit platforms "
        "(twitter/bluesky), expand for long-form (linkedin). For twitter or "
        "bluesky consider thread_items if the idea needs more than one post.\n"
        "4. For each platform call validate_post (or validate_post_length) and "
        "fix any failures BEFORE posting.\n"
        "5. Create the post with posts_create. For 'draft' omit timing; for "
        "'now' set publish_now=True; for a datetime pass scheduled_for. To "
        "promote an existing draft to scheduled, use posts_schedule (note: the "
        "post id changes).\n"
        "6. Report each platform's status from the response — partial failures "
        "are possible. Offer posts_retry for any that failed.\n"
        "Confirm the final copy with me before anything publishes."
    )


@mcp.prompt(
    name="triage_inbox",
    title="Triage the inbox",
    tags={"social", "workflow", "inbox"},
)
def triage_inbox(platform: str = "all", only_unread: bool = True) -> str:
    """List, summarize, and draft replies for incoming DMs and comments.

    Args:
        platform: Limit to one platform, or "all".
        only_unread: Focus on unread conversations only.
    """
    platform_clause = "" if platform == "all" else f" on {platform}"
    status_clause = ' with status="unread"' if only_unread else ""
    return (
        f"Triage my social inbox{platform_clause}.\n\n"
        "Workflow:\n"
        f"1. Call inbox_list{(' platform=' + platform) if platform != 'all' else ''}"
        f"{status_clause} to get open conversations.\n"
        "2. For each conversation that needs attention, call "
        "inbox_get_conversation (pass the accountId from the list entry) to "
        "read the recent messages.\n"
        "3. Group them by urgency and summarize who is waiting on what.\n"
        "4. For the ones worth answering, DRAFT a reply each and show them to "
        "me. Do NOT send anything until I approve the exact wording — "
        "inbox_messages_send delivers a real message to a real person.\n"
        "5. After I approve, send approved replies with inbox_messages_send, "
        "then optionally mark handled conversations with inbox_update.\n"
        "6. Also surface public comments worth a reply via comments_list, and "
        "draft comments_reply / comments_private_reply the same way (approval "
        "first)."
    )


@mcp.prompt(
    name="weekly_analytics_review",
    title="Weekly analytics review",
    tags={"social", "workflow", "analytics"},
)
def weekly_analytics_review(platform: str = "all") -> str:
    """Pull growth, engagement, and best-time signals into one summary.

    Args:
        platform: Limit the review to one platform, or "all".
    """
    platform_arg = "" if platform == "all" else f' platform="{platform}"'
    return (
        f"Give me a weekly analytics review{'' if platform == 'all' else ' for ' + platform}.\n\n"
        "Workflow:\n"
        "1. Call accounts_follower_stats for follower-growth trends (am I "
        "growing?).\n"
        f"2. Call analytics_insights(type='daily_metrics'{platform_arg}) for "
        "the overall engagement picture, and analytics_insights("
        f"type='posting_frequency'{platform_arg}) to check cadence.\n"
        f"3. Call analytics_insights(type='best_time'{platform_arg}) to find "
        "optimal posting windows.\n"
        f"4. Call analytics_posts({platform_arg.strip() or 'limit=10'}) for the "
        "top posts by engagement; note what worked.\n"
        "5. For Instagram, add analytics_instagram for reach + demographics; "
        "for YouTube, add analytics_youtube_daily.\n"
        "6. Synthesize: what grew, what landed, and 2-3 concrete "
        "recommendations (topics, formats, and the best time slots to queue "
        "next week via queue_preview / queue_set_schedule)."
    )
