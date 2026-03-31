## ADDED Requirements

### Requirement: Create brand profile
The `profiles_create` tool SHALL create a new brand profile via `POST /v1/profiles`. ToolAnnotations(Write, not idempotent).

#### Scenario: Create profile
- **WHEN** `profiles_create` is called with name="CDIT Brand"
- **THEN** the profile is created and returns the profile ID

### Requirement: Get profile details
The `profiles_get` tool SHALL return a single profile by ID via `GET /v1/profiles/{profileId}`. ToolAnnotations(RO, idempotent).

#### Scenario: Get profile
- **WHEN** `profiles_get` is called with a valid profile_id
- **THEN** returns profile details including name and associated account IDs

### Requirement: Update profile
The `profiles_update` tool SHALL update a profile via `PUT /v1/profiles/{profileId}`. ToolAnnotations(Write, idempotent).

#### Scenario: Rename profile
- **WHEN** `profiles_update` is called with profile_id and name="New Name"
- **THEN** the profile is updated

### Requirement: Delete profile
The `profiles_delete` tool SHALL remove a profile via `DELETE /v1/profiles/{profileId}`. ToolAnnotations(Write, idempotent).

#### Scenario: Delete profile
- **WHEN** `profiles_delete` is called with a profile_id
- **THEN** the profile is deleted (accounts are not disconnected)
