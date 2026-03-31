## ADDED Requirements

### Requirement: Update draft or scheduled posts
The `posts_update` tool SHALL edit a draft or scheduled post via `PUT /v1/posts/{postId}`. Accepts content, platforms, media_urls, scheduled_for. ToolAnnotations(Write, idempotent).

#### Scenario: Edit draft content
- **WHEN** `posts_update` is called with post_id and new content
- **THEN** the post content is updated and the response confirms the change

#### Scenario: Reschedule a post
- **WHEN** `posts_update` is called with post_id and new scheduled_for datetime
- **THEN** the scheduled time is updated

### Requirement: Bulk upload posts from CSV
The `posts_bulk_upload` tool SHALL import posts from CSV data via `POST /v1/posts/bulk-upload`. Accepts CSV content as a string. Docstring MUST note practical size limits. ToolAnnotations(Write, not idempotent).

#### Scenario: Import 5 posts from CSV
- **WHEN** `posts_bulk_upload` is called with CSV content containing 5 rows
- **THEN** returns a summary with created count, failed count, and any errors per row
