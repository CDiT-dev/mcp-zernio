## ADDED Requirements

### Requirement: Create queue time slots
The `queue_create_slot` tool SHALL create a recurring time slot via `POST /v1/queue/slots`. Accepts profile_id, day_of_week, time, and platform. ToolAnnotations(Write, not idempotent).

#### Scenario: Create a Monday 9am Twitter slot
- **WHEN** `queue_create_slot` is called with profile_id, day="monday", time="09:00", platform="twitter"
- **THEN** the slot is created and the response includes the slot ID and confirmation

### Requirement: List queue slots
The `queue_list_slots` tool SHALL list all configured queue slots via `GET /v1/queue/slots`. Filterable by profile_id. ToolAnnotations(RO, idempotent).

#### Scenario: List all slots for a profile
- **WHEN** `queue_list_slots` is called with a profile_id
- **THEN** returns all configured recurring slots with day, time, platform, and occupied status

### Requirement: Update queue slot
The `queue_update_slot` tool SHALL update an existing slot via `PUT /v1/queue/slots`. ToolAnnotations(Write, idempotent).

#### Scenario: Change slot time
- **WHEN** `queue_update_slot` is called with slot_id and new time="14:00"
- **THEN** the slot is updated and confirmation is returned

### Requirement: Delete queue slot
The `queue_delete_slot` tool SHALL remove a slot via `DELETE /v1/queue/slots`. ToolAnnotations(Write, idempotent).

#### Scenario: Remove a slot
- **WHEN** `queue_delete_slot` is called with a slot_id
- **THEN** the slot is deleted

### Requirement: Get next available slot
The `queue_next_slot` tool SHALL return the next available open queue slot via `GET /v1/queue/next-slot`. ToolAnnotations(RO, idempotent).

#### Scenario: Find next open slot
- **WHEN** `queue_next_slot` is called with a profile_id
- **THEN** returns the next unoccupied slot with datetime, platform, and slot_id
