## ADDED Requirements

### Requirement: Usage statistics
The `usage_stats` tool SHALL return usage/billing stats via `GET /v1/usage-stats`. ToolAnnotations(RO, idempotent).

#### Scenario: Get usage stats
- **WHEN** `usage_stats` is called
- **THEN** returns API usage counts, post counts, and billing information

### Requirement: Direct media upload
The `media_upload_direct` tool SHALL upload media directly via `POST /v1/media/upload-direct` as an alternative to the presign flow. Accepts multipart form data. ToolAnnotations(Write, not idempotent).

#### Scenario: Direct upload
- **WHEN** `media_upload_direct` is called with file data and content type
- **THEN** the file is uploaded and publicUrl returned

### Requirement: List account groups
The `account_groups_list` tool SHALL list account groups via `GET /v1/account-groups`. ToolAnnotations(RO, idempotent).

#### Scenario: List groups
- **WHEN** `account_groups_list` is called
- **THEN** returns list of account groups with member accounts

### Requirement: Create account group
The `account_groups_create` tool SHALL create a group via `POST /v1/account-groups`. ToolAnnotations(Write, not idempotent).

#### Scenario: Create group
- **WHEN** `account_groups_create` is called with name and account_ids
- **THEN** the group is created

### Requirement: Delete account group
The `account_groups_delete` tool SHALL delete a group via `DELETE /v1/account-groups/{id}`. ToolAnnotations(Write, idempotent).

#### Scenario: Delete group
- **WHEN** `account_groups_delete` is called with a group_id
- **THEN** the group is deleted
