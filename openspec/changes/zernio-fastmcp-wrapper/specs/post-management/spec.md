## ADDED Requirements

### Requirement: Create posts with self-describing modes
The `posts_create` tool SHALL support three publish modes, documented inline with examples in the docstring:
- `publish_now=True` → publish immediately
- `scheduled_for="2026-04-01T09:00:00Z"` → schedule for later (ISO 8601)
- Neither → save as draft

The tool SHALL accept an optional `profile_id` parameter for account disambiguation. The docstring MUST instruct: "If the user has not specified an account and has multiple accounts for the target platform, call profiles_list first to identify the correct brand context, then confirm before posting."

The tool SHALL default to draft mode (no `publish_now`, no `scheduled_for`) to prevent accidental publishing.

#### Scenario: Immediate publish
- **WHEN** `posts_create` is called with `publish_now=True`, text content, and a valid account_id
- **THEN** the post is published immediately and the response includes `platformPostUrl`

#### Scenario: Schedule post
- **WHEN** `posts_create` is called with `scheduled_for="2026-04-01T09:00:00Z"`
- **THEN** the post is saved with scheduled status and the response confirms the scheduled time

#### Scenario: Draft by default
- **WHEN** `posts_create` is called without `publish_now` or `scheduled_for`
- **THEN** the post is saved as a draft

#### Scenario: Cross-post to multiple platforms
- **WHEN** `posts_create` is called with multiple entries in the `platforms` array
- **THEN** the post is created for each platform and the response includes per-platform status and post IDs

#### Scenario: ToolAnnotations
- **WHEN** `posts_create` is registered
- **THEN** it MUST have `ToolAnnotations(readOnlyHint=False, idempotentHint=False)`

### Requirement: Get single post with failure context
The `posts_get` tool SHALL return a single post by ID including its current status. When `status` is `"failed"`, the response MUST include a `failure_reason` or `error_message` field from the Zernio API.

#### Scenario: Published post lookup
- **WHEN** `posts_get` is called with a valid published post ID
- **THEN** response includes status, platformPostUrl, platform, content, and publish timestamp

#### Scenario: Failed post with reason
- **WHEN** `posts_get` is called for a post with `status: "failed"`
- **THEN** response includes `failure_reason` (e.g., "Image aspect ratio rejected", "Caption exceeds 2200 characters")

### Requirement: List posts with filters
The `posts_list` tool SHALL support filtering by `status` (draft, scheduled, published, failed), `platform`, and date range (`from_date`, `to_date` in ISO 8601 format). Default limit SHALL be 20, maximum 50. The docstring MUST specify ISO 8601 date format with example.

#### Scenario: List failed posts
- **WHEN** `posts_list` is called with `status="failed"`
- **THEN** only posts with failed status are returned, each including `failure_reason`

#### Scenario: List scheduled for tomorrow
- **WHEN** `posts_list` is called with `status="scheduled"` and `from_date`/`to_date` spanning tomorrow
- **THEN** only posts scheduled within that date range are returned

#### Scenario: Default pagination
- **WHEN** `posts_list` is called without a `limit` parameter
- **THEN** at most 20 posts are returned

### Requirement: Delete draft or scheduled posts
The `posts_delete` tool SHALL delete posts that are in draft or scheduled status. The docstring MUST state: "Use for draft or scheduled posts only. For published posts, use posts_unpublish instead. If you don't know the post's status, call posts_get first."

#### Scenario: Delete a draft
- **WHEN** `posts_delete` is called with a draft post ID
- **THEN** the post is deleted and confirmation is returned

#### Scenario: Attempt to delete published post (server-side guard)
- **WHEN** `posts_delete` is called with a published post ID
- **THEN** the server MUST validate the post status and return an error explaining to use `posts_unpublish` instead (do not rely on Claude picking the right tool)

### Requirement: Unpublish posted content
The `posts_unpublish` tool SHALL remove a published post from the social media platform while keeping the Zernio record. The docstring MUST state: "Removes the post from the platform (e.g., deletes the tweet). The Zernio record is preserved. For drafts or scheduled posts, use posts_delete instead."

#### Scenario: Unpublish a tweet
- **WHEN** `posts_unpublish` is called with a published Twitter post ID
- **THEN** the tweet is deleted from Twitter, Zernio record status changes to "unpublished"

### Requirement: Retry failed posts
The `posts_retry` tool SHALL retry a post that has `status: "failed"`. The docstring MUST state: "Before retrying, call posts_get to check failure_reason and confirm with the user that the underlying issue has been resolved."

#### Scenario: Retry after transient failure
- **WHEN** `posts_retry` is called for a post that failed due to a network timeout
- **THEN** the post is resubmitted and returns new status (published or failed with updated reason)

#### Scenario: Retry with unresolved issue
- **WHEN** `posts_retry` is called for a post that failed because the image was too large
- **THEN** the retry fails again with the same `failure_reason` (no silent data loss)
