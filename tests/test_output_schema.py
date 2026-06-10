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
    PostList,
    PostResult,
    QueueSlotList,
)
from zernio_mcp.tools._common import error

# Every model used as a strict ``output_schema=`` in the tool modules.
STRICT_OUTPUT_MODELS = [
    AccountList,
    AnalyticsResult,
    PostList,
    PostResult,
    QueueSlotList,
]


@pytest.mark.parametrize("model", STRICT_OUTPUT_MODELS, ids=lambda m: m.__name__)
def test_error_payload_validates_against_output_schema(model):
    """The ``{"error": ...}`` dict from the error path must satisfy the schema."""
    schema = model.model_json_schema()
    jsonschema.validate(error("upstream failed"), schema)


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
