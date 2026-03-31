## ADDED Requirements

### Requirement: List conversations
The `inbox_list` tool SHALL list conversations via `GET /v1/inbox/conversations`. Filterable by platform, status. ToolAnnotations(RO, idempotent).

#### Scenario: List all conversations
- **WHEN** `inbox_list` is called
- **THEN** returns paginated list of conversations with platform, participant, last message preview

### Requirement: Get conversation
The `inbox_get` tool SHALL get a single conversation via `GET /v1/inbox/conversations/{id}`. ToolAnnotations(RO, idempotent).

#### Scenario: Get conversation
- **WHEN** `inbox_get` is called with a conversation_id
- **THEN** returns conversation details with participant info and status

### Requirement: Update conversation
The `inbox_update` tool SHALL update conversation metadata via `PUT /v1/inbox/conversations/{id}` (mark read, archive, etc.). ToolAnnotations(Write, idempotent).

#### Scenario: Mark as read
- **WHEN** `inbox_update` is called with conversation_id and status="read"
- **THEN** the conversation is marked as read

### Requirement: List messages in conversation
The `inbox_messages_list` tool SHALL list messages via `GET /v1/inbox/conversations/{id}/messages`. ToolAnnotations(RO, idempotent).

#### Scenario: List messages
- **WHEN** `inbox_messages_list` is called with a conversation_id
- **THEN** returns paginated messages with content, sender, timestamp

### Requirement: Send message
The `inbox_messages_send` tool SHALL send a reply via `POST /v1/inbox/conversations/{id}/messages`. ToolAnnotations(Write, not idempotent).

#### Scenario: Send reply
- **WHEN** `inbox_messages_send` is called with conversation_id and content
- **THEN** the message is sent and confirmation returned

### Requirement: Edit message
The `inbox_message_edit` tool SHALL edit a message via `PATCH /v1/inbox/conversations/{id}/messages/{mid}`. ToolAnnotations(Write, idempotent).

#### Scenario: Edit message
- **WHEN** `inbox_message_edit` is called with message_id and new content
- **THEN** the message is updated

### Requirement: Delete message
The `inbox_message_delete` tool SHALL delete a message via `DELETE /v1/inbox/conversations/{id}/messages/{mid}`. ToolAnnotations(Write, idempotent).

#### Scenario: Delete message
- **WHEN** `inbox_message_delete` is called with message_id
- **THEN** the message is deleted

### Requirement: Typing indicator
The `inbox_typing` tool SHALL send a typing indicator via `POST /v1/inbox/conversations/{id}/typing`. ToolAnnotations(Write, not idempotent).

#### Scenario: Send typing
- **WHEN** `inbox_typing` is called with a conversation_id
- **THEN** a typing indicator is sent to the recipient

### Requirement: React to message
The `inbox_react` tool SHALL add a reaction via `POST /v1/inbox/conversations/{id}/messages/{mid}/reactions`. ToolAnnotations(Write, not idempotent).

#### Scenario: React to message
- **WHEN** `inbox_react` is called with message_id and reaction emoji
- **THEN** the reaction is added
