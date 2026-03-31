## ADDED Requirements

### Requirement: List contacts
The `contacts_list` tool SHALL list contacts via `GET /v1/contacts`. Filterable by search query. ToolAnnotations(RO, idempotent).

#### Scenario: List contacts
- **WHEN** `contacts_list` is called
- **THEN** returns paginated list of contacts

### Requirement: Create contact
The `contacts_create` tool SHALL create a contact via `POST /v1/contacts`. ToolAnnotations(Write, not idempotent).

#### Scenario: Create contact
- **WHEN** `contacts_create` is called with name and platform details
- **THEN** the contact is created

### Requirement: Get contact
The `contacts_get` tool SHALL get a single contact via `GET /v1/contacts/{id}`. ToolAnnotations(RO, idempotent).

#### Scenario: Get contact
- **WHEN** `contacts_get` is called with a contact_id
- **THEN** returns contact details

### Requirement: Update contact
The `contacts_update` tool SHALL update a contact via `PUT /v1/contacts/{id}`. ToolAnnotations(Write, idempotent).

#### Scenario: Update contact
- **WHEN** `contacts_update` is called with contact_id and updates
- **THEN** the contact is updated

### Requirement: Delete contact
The `contacts_delete` tool SHALL delete a contact via `DELETE /v1/contacts/{id}`. ToolAnnotations(Write, idempotent).

#### Scenario: Delete contact
- **WHEN** `contacts_delete` is called with a contact_id
- **THEN** the contact is deleted
