"""Pydantic output models for high-traffic read tools.

These describe the *current* top-level shape of the responses so FastMCP can
advertise a stable ``output_schema`` to clients (the LLM gets a typed contract
instead of opaque Zernio JSON). The tools keep returning plain ``dict`` objects
that conform to these shapes — extra upstream fields are preserved verbatim in
the structured content, so nothing is lost and existing callers are unaffected.

Item models set ``extra="allow"`` because Zernio's payloads carry many optional
per-platform fields we deliberately do not enumerate; the contract documents the
fields the LLM can rely on without pretending the list is exhaustive.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Lenient(BaseModel):
    """Base for item models that pass through unmodelled upstream fields."""

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Accounts / profiles
# ---------------------------------------------------------------------------


class Account(_Lenient):
    """A connected social media account (PII fields are stripped upstream)."""

    id: str | None = Field(default=None, alias="_id", description="Account id.")
    platform: str | None = Field(default=None, description="Platform key, e.g. 'twitter'.")
    username: str | None = Field(default=None, description="Handle on the platform.")
    displayName: str | None = Field(default=None, description="Display name.")
    profileName: str | None = Field(default=None, description="Owning brand profile name.")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class AccountList(BaseModel):
    """Result of ``accounts_list`` / ``accounts_health``."""

    accounts: list[Account] = Field(
        default_factory=list, description="Connected accounts."
    )
    error: str | None = Field(default=None, description="Set when the call failed.")

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------


class Post(_Lenient):
    """A single post record as returned by Zernio (fields vary by status)."""

    id: str | None = Field(default=None, alias="_id", description="Post id.")
    status: str | None = Field(
        default=None,
        description="draft | scheduled | published | failed | unpublished.",
    )
    content: str | None = Field(default=None, description="Post text.")
    platformPostUrl: str | None = Field(default=None, description="Live URL once published.")
    failure_reason: str | None = Field(default=None, description="Reason a failed post failed.")
    scheduledFor: str | None = Field(default=None, description="ISO 8601 scheduled time.")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class PostResult(BaseModel):
    """Result of ``posts_get`` and the post-mutating tools.

    Zernio nests the record under ``post`` on most endpoints; this model keeps
    that envelope and also surfaces the workflow flags ``posts_schedule`` adds.
    """

    post: Post | None = Field(default=None, description="The post record.")
    previous_post_id: str | None = Field(
        default=None, description="Set by posts_schedule when the id changed."
    )
    orphaned_previous_post_id: str | None = Field(
        default=None, description="Original draft that could not be deleted after recreate."
    )
    warning: str | None = Field(default=None, description="Non-fatal advisory.")
    error: str | None = Field(default=None, description="Set when the call failed.")

    model_config = ConfigDict(extra="allow")


class PostList(BaseModel):
    """Result of ``posts_list``."""

    posts: list[Post] = Field(default_factory=list, description="Matching posts.")
    error: str | None = Field(default=None, description="Set when the call failed.")

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


class AnalyticsResult(BaseModel):
    """Result of the analytics read tools (``analytics_posts``,
    ``analytics_insights``, ``analytics_instagram``).

    Analytics endpoints are deliberately heterogeneous: ``analytics_posts``
    without a ``post_id`` carries a ``posts`` list sorted by engagement; with
    one it carries a timeline; ``analytics_insights`` returns whichever shape
    the requested insight produces (``bestHour``/``bestDay``, ``metrics``,
    ``decay``…); ``analytics_instagram`` returns ``reach``/``impressions`` plus
    an optional ``demographics`` block. Rather than enumerate every variant we
    keep a single permissive contract: ``posts`` is surfaced as the one field
    common enough to type, every other field passes through verbatim under
    ``extra``, and the error path stays representable.
    """

    posts: list[dict[str, Any]] | None = Field(
        default=None, description="Per-post engagement metrics (analytics_posts)."
    )
    error: str | None = Field(default=None, description="Set when the call failed.")

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Inbox (conversations / DMs)
# ---------------------------------------------------------------------------


class InboxMessage(_Lenient):
    """A single direct message within a conversation."""

    id: str | None = Field(default=None, alias="_id", description="Message id.")
    content: str | None = Field(default=None, description="Message text.")
    createdAt: str | None = Field(default=None, description="ISO 8601 send time.")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class InboxConversation(_Lenient):
    """Result of ``inbox_get_conversation``.

    Zernio returns the conversation record at the top level (``_id``,
    ``platform``, ``participant``, ``status`` …); the tool additionally attaches
    the recent ``messages`` list when ``include_messages`` is true. Both the
    conversation fields and ``messages`` are optional so the metadata-only and
    error paths validate.
    """

    id: str | None = Field(default=None, alias="_id", description="Conversation id.")
    platform: str | None = Field(default=None, description="Platform key.")
    status: str | None = Field(default=None, description="e.g. 'unread', 'archived'.")
    messages: list[InboxMessage] | None = Field(
        default=None, description="Recent messages (when include_messages=True)."
    )
    error: str | None = Field(default=None, description="Set when the call failed.")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class InboxConversationList(BaseModel):
    """Result of ``inbox_list``."""

    conversations: list[InboxConversation] = Field(
        default_factory=list, description="Matching conversations."
    )
    error: str | None = Field(default=None, description="Set when the call failed.")

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Comments
# ---------------------------------------------------------------------------


class CommentItem(_Lenient):
    """A single comment on a post."""

    id: str | None = Field(default=None, alias="_id", description="Comment id.")
    platform: str | None = Field(default=None, description="Platform key.")
    content: str | None = Field(default=None, description="Comment text.")
    createdAt: str | None = Field(default=None, description="ISO 8601 time.")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class CommentList(BaseModel):
    """Result of ``comments_list``."""

    comments: list[CommentItem] = Field(
        default_factory=list, description="Matching comments."
    )
    error: str | None = Field(default=None, description="Set when the call failed.")

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Activity logs
# ---------------------------------------------------------------------------


class LogList(BaseModel):
    """Result of ``logs_posts``.

    Zernio returns ``{"logs": [...]}``; each entry is a free-form event record,
    so the items stay untyped dicts and pass through verbatim.
    """

    logs: list[dict[str, Any]] = Field(
        default_factory=list, description="Activity log events."
    )
    error: str | None = Field(default=None, description="Set when the call failed.")

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Usage / billing
# ---------------------------------------------------------------------------


class UsageStats(BaseModel):
    """Result of ``usage_stats``.

    The billing/usage payload has no stable required field across plans, so the
    contract is intentionally open: every upstream field passes through under
    ``extra`` and only the shared error envelope is enumerated.
    """

    error: str | None = Field(default=None, description="Set when the call failed.")

    model_config = ConfigDict(extra="allow")


# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------


class QueueSlot(_Lenient):
    """A recurring queue slot / preview slot."""

    id: str | None = Field(default=None, alias="_id", description="Slot id.")
    platform: str | None = Field(default=None, description="Target platform.")
    datetime: str | None = Field(default=None, description="ISO 8601 fire time (preview).")
    occupied: bool | None = Field(default=None, description="Whether the slot is taken (preview).")
    isDefault: bool | None = Field(default=None, description="Whether this is the default schedule.")

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class QueueSlotList(BaseModel):
    """Result of ``queue_list_slots`` / ``queue_preview``."""

    slots: list[QueueSlot] = Field(default_factory=list, description="Queue slots.")
    error: str | None = Field(default=None, description="Set when the call failed.")

    model_config = ConfigDict(extra="allow")
