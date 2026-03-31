## ADDED Requirements

### Requirement: List broadcasts
The `broadcasts_list` tool SHALL list broadcast campaigns via `GET /v1/broadcasts`. ToolAnnotations(RO, idempotent).

#### Scenario: List broadcasts
- **WHEN** `broadcasts_list` is called
- **THEN** returns paginated list of broadcast campaigns with status

### Requirement: Create broadcast
The `broadcasts_create` tool SHALL create a broadcast campaign via `POST /v1/broadcasts`. ToolAnnotations(Write, not idempotent).

#### Scenario: Create broadcast
- **WHEN** `broadcasts_create` is called with name, content, and target accounts
- **THEN** the broadcast is created

### Requirement: Get broadcast
The `broadcasts_get` tool SHALL get a single broadcast via `GET /v1/broadcasts/{id}`. ToolAnnotations(RO, idempotent).

#### Scenario: Get broadcast
- **WHEN** `broadcasts_get` is called with a broadcast_id
- **THEN** returns broadcast details including status and metrics

### Requirement: Update broadcast
The `broadcasts_update` tool SHALL update a broadcast via `PUT /v1/broadcasts/{id}`. ToolAnnotations(Write, idempotent).

#### Scenario: Update broadcast
- **WHEN** `broadcasts_update` is called with broadcast_id and updates
- **THEN** the broadcast is updated

### Requirement: Delete broadcast
The `broadcasts_delete` tool SHALL delete a broadcast via `DELETE /v1/broadcasts/{id}`. ToolAnnotations(Write, idempotent).

#### Scenario: Delete broadcast
- **WHEN** `broadcasts_delete` is called with a broadcast_id
- **THEN** the broadcast is deleted
