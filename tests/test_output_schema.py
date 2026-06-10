"""Regression: declared output_schemas must accept the error path payload.

Tools that advertise ``output_schema=<Model>.model_json_schema()`` return a
plain ``{"error": ...}`` dict (via ``_common.error``) on any upstream failure.
If the model marks a collection field as required (no default), that error
payload violates the declared schema and clients surface a schema-validation
error instead of the actual upstream message. These tests pin both the error
path and a representative success path against the declared JSON Schema.

See: "make output_schema satisfiable on error paths" review fix.
"""

from __future__ import annotations

import jsonschema
import pytest

from zernio_mcp.models import (
    AccountList,
    AnalyticsResult,
    CommentList,
    InboxConversation,
    InboxConversationList,
    LogList,
    PostList,
    PostResult,
    QueueSlotList,
    UsageStats,
)
from zernio_mcp.tools._common import error

# Every model used as a strict ``output_schema=`` in the tool modules.
STRICT_OUTPUT_MODELS = [
    AccountList,
    AnalyticsResult,
    CommentList,
    InboxConversation,
    InboxConversationList,
    LogList,
    PostList,
    PostResult,
    QueueSlotList,
    UsageStats,
]


@pytest.mark.parametrize("model", STRICT_OUTPUT_MODELS, ids=lambda m: m.__name__)
def test_error_payload_validates_against_output_schema(model):
    """The ``{"error": ...}`` dict from the error path must satisfy the schema."""
    schema = model.model_json_schema()
    jsonschema.validate(error("upstream failed"), schema)


@pytest.mark.parametrize("model", STRICT_OUTPUT_MODELS, ids=lambda m: m.__name__)
def test_empty_payload_validates_against_output_schema(model):
    """An empty ``{}`` (no fields at all) must satisfy every output schema.

    Pins the rule 3 contract: collection fields default to empty lists and no
    field is required, so the most degenerate upstream response still validates.
    """
    jsonschema.validate({}, model.model_json_schema())


# ---------------------------------------------------------------------------
# Pass-3 success-path + field-preservation contracts (one per new model).
# Each asserts a representative *success* payload — including unmodelled
# upstream passthrough fields — still validates against the declared schema.
# ---------------------------------------------------------------------------


def test_comment_list_success_payload_validates():
    schema = CommentList.model_json_schema()
    payload = {
        "comments": [
            {"_id": "x1", "platform": "instagram", "content": "nice",
             "createdAt": "t", "likeCount": 3}  # likeCount is passthrough
        ]
    }
    jsonschema.validate(payload, schema)
    # Empty / omitted collection still validates.
    jsonschema.validate({"comments": []}, schema)


def test_inbox_conversation_list_success_payload_validates():
    schema = InboxConversationList.model_json_schema()
    payload = {
        "conversations": [
            {"_id": "c1", "platform": "twitter", "status": "unread",
             "participant": {"name": "Al"}}  # participant is passthrough
        ]
    }
    jsonschema.validate(payload, schema)


def test_inbox_conversation_metadata_and_messages_validate():
    """The metadata-only and messages-attached shapes both validate."""
    schema = InboxConversation.model_json_schema()
    # Metadata only (include_messages=False).
    jsonschema.validate(
        {"_id": "c1", "platform": "twitter", "participant": {"name": "Al"}}, schema
    )
    # With messages attached by the tool.
    jsonschema.validate(
        {
            "_id": "c1",
            "platform": "twitter",
            "messages": [
                {"_id": "m1", "content": "Hi", "createdAt": "t", "sender": "them"}
            ],
        },
        schema,
    )


def test_log_list_success_payload_validates():
    schema = LogList.model_json_schema()
    jsonschema.validate({"logs": [{"event": "published", "at": "t"}]}, schema)


def test_usage_stats_success_payload_validates():
    """usage_stats has no required fields — arbitrary billing payloads validate."""
    schema = UsageStats.model_json_schema()
    jsonschema.validate({"posts": 42, "billing": {"plan": "pro"}}, schema)


def test_analytics_result_insight_shapes_validate():
    """analytics_insights / analytics_instagram return heterogeneous shapes that
    all pass through AnalyticsResult's permissive contract."""
    schema = AnalyticsResult.model_json_schema()
    jsonschema.validate({"bestHour": 14, "bestDay": "Tuesday"}, schema)  # best_time
    jsonschema.validate({"metrics": []}, schema)  # daily_metrics
    jsonschema.validate(
        {"reach": 100, "impressions": 250, "demographics": {"ages": []}}, schema
    )  # instagram
    jsonschema.validate({"posts": [{"likes": 42}]}, schema)  # analytics_posts


def test_account_list_success_payload_validates():
    """A populated accounts payload (with passthrough fields) still validates."""
    schema = AccountList.model_json_schema()
    payload = {
        "accounts": [
            {"_id": "a1", "platform": "twitter", "username": "x", "followers": 42}
        ]
    }
    jsonschema.validate(payload, schema)


def test_account_list_empty_accounts_validates():
    """accounts is no longer required — an empty/omitted list must validate."""
    schema = AccountList.model_json_schema()
    jsonschema.validate({"accounts": []}, schema)
    jsonschema.validate({}, schema)
