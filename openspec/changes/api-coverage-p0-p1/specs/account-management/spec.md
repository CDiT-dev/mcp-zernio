## ADDED Requirements

### Requirement: Update account settings
The `accounts_update` tool SHALL update account settings via `PUT /v1/accounts/{accountId}`. ToolAnnotations(Write, idempotent).

#### Scenario: Update account
- **WHEN** `accounts_update` is called with account_id and new settings
- **THEN** the account is updated

### Requirement: Disconnect account
The `accounts_delete` tool SHALL disconnect a social account via `DELETE /v1/accounts/{accountId}`. ToolAnnotations(Write, idempotent).

#### Scenario: Disconnect account
- **WHEN** `accounts_delete` is called with an account_id
- **THEN** the account is disconnected from Zernio

### Requirement: Follower statistics
The `accounts_follower_stats` tool SHALL return follower count trends over time via `GET /v1/accounts/follower-stats`. Results SHALL be cached for 60s (follower counts don't change mid-conversation). ToolAnnotations(RO, idempotent).

#### Scenario: Get follower trends
- **WHEN** `accounts_follower_stats` is called
- **THEN** returns per-account follower counts over time

### Requirement: Single account health
The `accounts_health_single` tool SHALL return health status for one account via `GET /v1/accounts/{accountId}/health`. ToolAnnotations(RO, idempotent).

#### Scenario: Check one account
- **WHEN** `accounts_health_single` is called with an account_id
- **THEN** returns token status and health details for that specific account
