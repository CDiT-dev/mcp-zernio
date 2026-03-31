## ADDED Requirements

### Requirement: List connected social accounts
The `accounts_list` tool SHALL return all connected social media accounts with human-readable context: `id`, `platform`, `username`, `displayName`, `profileName`, and connection status. The response MUST include enough information for Claude to confirm the correct account without a follow-up call.

#### Scenario: Single account per platform
- **WHEN** user has one Twitter account connected
- **THEN** `accounts_list` returns that account with platform="twitter", username, displayName, and the profile it belongs to

#### Scenario: Multiple accounts for same platform
- **WHEN** user has 3 Twitter accounts connected across 2 brand profiles
- **THEN** `accounts_list` returns all 3 with distinct profileName fields so Claude can disambiguate

### Requirement: Check account token health
The `accounts_health` tool SHALL return the health/expiry status of each connected account's OAuth token. When a token is expired or revoked, the response MUST include a `reauth_url` or fallback instruction directing the user to `app.zernio.com/accounts` to reconnect.

#### Scenario: All tokens healthy
- **WHEN** all connected accounts have valid tokens
- **THEN** `accounts_health` returns each account with `status: "healthy"` and `expires_at` (if available)

#### Scenario: Expired token detected
- **WHEN** an Instagram account has an expired token
- **THEN** `accounts_health` returns that account with `status: "expired"` and a `reauth_url` or `reauth_instructions` field

#### Scenario: ToolAnnotations
- **WHEN** either tool is registered with FastMCP
- **THEN** both `accounts_list` and `accounts_health` MUST have `ToolAnnotations(readOnlyHint=True, idempotentHint=True)`

### Requirement: List brand profiles
The `profiles_list` tool SHALL return all brand profile groupings with their associated account IDs. The docstring MUST explain the relationship: "A profile is a brand grouping containing one or more connected accounts. Use profiles_list to identify which accounts belong to a brand, then pass account_ids to posts_create."

#### Scenario: Profile with multiple accounts
- **WHEN** a profile "CDIT Brand" has Twitter, LinkedIn, and Instagram accounts
- **THEN** `profiles_list` returns the profile with all 3 account IDs and their platform names

#### Scenario: No profiles configured
- **WHEN** user has accounts but no profiles set up in Zernio
- **THEN** `profiles_list` returns an empty list with a message explaining how to create profiles
