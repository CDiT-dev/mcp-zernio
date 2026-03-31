## ADDED Requirements

### Requirement: List all comments
The `comments_list` tool SHALL list comments across all posts via `GET /v1/inbox/comments`. Filterable by platform. ToolAnnotations(RO, idempotent).

#### Scenario: List comments
- **WHEN** `comments_list` is called
- **THEN** returns paginated comments with post context, author, content

### Requirement: List comments for a post
The `comments_list_post` tool SHALL list comments for a specific post via `GET /v1/inbox/comments/{postId}`. ToolAnnotations(RO, idempotent).

#### Scenario: List post comments
- **WHEN** `comments_list_post` is called with a post_id
- **THEN** returns all comments on that post

### Requirement: Reply to comment
The `comments_reply` tool SHALL reply to a comment via `POST /v1/inbox/comments/{postId}`. ToolAnnotations(Write, not idempotent).

#### Scenario: Reply
- **WHEN** `comments_reply` is called with post_id, comment_id, and content
- **THEN** the reply is posted

### Requirement: Delete comment
The `comments_delete` tool SHALL delete a comment via `DELETE /v1/inbox/comments/{postId}`. ToolAnnotations(Write, idempotent).

#### Scenario: Delete
- **WHEN** `comments_delete` is called with post_id and comment_id
- **THEN** the comment is deleted

### Requirement: Hide comment
The `comments_hide` tool SHALL hide a comment via `POST /v1/inbox/comments/{postId}/{commentId}/hide`. ToolAnnotations(Write, idempotent).

#### Scenario: Hide
- **WHEN** `comments_hide` is called with post_id and comment_id
- **THEN** the comment is hidden from public view

### Requirement: Like comment
The `comments_like` tool SHALL like a comment via `POST /v1/inbox/comments/{postId}/{commentId}/like`. ToolAnnotations(Write, not idempotent).

#### Scenario: Like
- **WHEN** `comments_like` is called with post_id and comment_id
- **THEN** the comment is liked

### Requirement: Private reply to comment
The `comments_private_reply` tool SHALL send a private reply via `POST /v1/inbox/comments/{postId}/{commentId}/private-reply`. ToolAnnotations(Write, not idempotent).

#### Scenario: Private reply
- **WHEN** `comments_private_reply` is called with post_id, comment_id, and content
- **THEN** a private message is sent to the commenter
