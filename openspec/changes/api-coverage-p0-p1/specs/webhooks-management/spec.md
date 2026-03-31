## ADDED Requirements

### Requirement: Get webhook config
The `webhooks_get` tool SHALL get webhook settings via `GET /v1/webhooks/settings`. ToolAnnotations(RO, idempotent).

#### Scenario: Get config
- **WHEN** `webhooks_get` is called
- **THEN** returns current webhook URL, events, and status

### Requirement: Create webhook
The `webhooks_create` tool SHALL create webhook config via `POST /v1/webhooks/settings`. ToolAnnotations(Write, not idempotent).

#### Scenario: Create webhook
- **WHEN** `webhooks_create` is called with url and event types
- **THEN** the webhook is configured

### Requirement: Update webhook
The `webhooks_update` tool SHALL update webhook config via `PUT /v1/webhooks/settings`. ToolAnnotations(Write, idempotent).

#### Scenario: Update webhook
- **WHEN** `webhooks_update` is called with new url or events
- **THEN** the webhook config is updated

### Requirement: Delete webhook
The `webhooks_delete` tool SHALL remove webhook config via `DELETE /v1/webhooks/settings`. ToolAnnotations(Write, idempotent).

#### Scenario: Delete webhook
- **WHEN** `webhooks_delete` is called
- **THEN** the webhook is removed

### Requirement: Test webhook
The `webhooks_test` tool SHALL send a test event via `POST /v1/webhooks/test`. ToolAnnotations(Write, not idempotent).

#### Scenario: Send test
- **WHEN** `webhooks_test` is called
- **THEN** a test event is sent to the configured webhook URL

### Requirement: Webhook logs
The `webhooks_logs` tool SHALL return delivery logs via `GET /v1/webhooks/logs`. ToolAnnotations(RO, idempotent).

#### Scenario: Get logs
- **WHEN** `webhooks_logs` is called
- **THEN** returns recent webhook delivery attempts with status codes and timestamps
