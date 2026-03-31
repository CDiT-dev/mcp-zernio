## ADDED Requirements

### Requirement: Preview upcoming queue slots
The `queue_preview` tool SHALL return the next N upcoming queue slots for a given profile, with structured data: ISO 8601 timestamp, platform, and whether the slot is occupied or open. Default limit SHALL be 5 slots. The docstring MUST instruct Claude: "Present a maximum of 3 suggested open slots in natural language before asking the user to choose, not the entire queue."

#### Scenario: Open slots available
- **WHEN** `queue_preview` is called with a `profile_id`
- **THEN** returns up to 5 slots, each with `{ datetime: "2026-04-01T14:00:00Z", platform: "twitter", occupied: false }`

#### Scenario: All slots occupied
- **WHEN** all upcoming slots for the profile are occupied
- **THEN** returns the occupied slots with their scheduled post titles, and a message indicating no open slots

#### Scenario: No profile specified
- **WHEN** `queue_preview` is called without a `profile_id` and user has multiple profiles
- **THEN** returns an error instructing to specify a profile (or call `profiles_list` first)

#### Scenario: ToolAnnotations
- **WHEN** `queue_preview` is registered
- **THEN** it MUST have `ToolAnnotations(readOnlyHint=True, idempotentHint=True)`
