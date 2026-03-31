## ADDED Requirements

### Requirement: List reviews
The `reviews_list` tool SHALL list Google Business reviews via `GET /v1/inbox/reviews`. ToolAnnotations(RO, idempotent).

#### Scenario: List reviews
- **WHEN** `reviews_list` is called
- **THEN** returns paginated reviews with rating, content, author, and reply status

### Requirement: Reply to review
The `reviews_reply` tool SHALL reply to a review via `POST /v1/inbox/reviews/{id}/reply`. ToolAnnotations(Write, not idempotent).

#### Scenario: Reply to review
- **WHEN** `reviews_reply` is called with review_id and content
- **THEN** the reply is posted
