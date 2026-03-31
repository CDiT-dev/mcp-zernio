## ADDED Requirements

### Requirement: Post activity logs
The `logs_posts` tool SHALL return post activity logs via `GET /v1/posts/logs`. ToolAnnotations(RO, idempotent).

#### Scenario: Get post logs
- **WHEN** `logs_posts` is called
- **THEN** returns recent post activity (created, published, failed, deleted events)

### Requirement: Per-post logs
The `logs_post_detail` tool SHALL return logs for a specific post via `GET /v1/posts/{postId}/logs`. ToolAnnotations(RO, idempotent).

#### Scenario: Get post detail logs
- **WHEN** `logs_post_detail` is called with a post_id
- **THEN** returns the full event history for that post

### Requirement: Connection logs
The `logs_connections` tool SHALL return connection event logs via `GET /v1/connections/logs`. ToolAnnotations(RO, idempotent).

#### Scenario: Get connection logs
- **WHEN** `logs_connections` is called
- **THEN** returns account connection/disconnection events
