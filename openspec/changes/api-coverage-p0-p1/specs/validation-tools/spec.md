## ADDED Requirements

### Requirement: Validate post length against platform limits
The `validate_post_length` tool SHALL check content length against platform-specific character limits via `POST /v1/tools/validate/post-length`. ToolAnnotations(RO, idempotent).

#### Scenario: Content within limits
- **WHEN** `validate_post_length` is called with content and platform="twitter"
- **THEN** returns valid=true with remaining character count

#### Scenario: Content exceeds limit
- **WHEN** `validate_post_length` is called with 500-char content for Twitter
- **THEN** returns valid=false with the limit and overage count

### Requirement: Full post validation
The `validate_post` tool SHALL validate a complete post (content + media + platform config) via `POST /v1/tools/validate/post`. ToolAnnotations(RO, idempotent).

#### Scenario: Valid post
- **WHEN** `validate_post` is called with content, platforms, and media
- **THEN** returns per-platform validation results

### Requirement: Validate media
The `validate_media` tool SHALL validate media dimensions, format, and size against platform requirements via `POST /v1/tools/validate/media`. ToolAnnotations(RO, idempotent).

#### Scenario: Image valid for Instagram
- **WHEN** `validate_media` is called with media URL and platform="instagram"
- **THEN** returns valid=true with accepted dimensions
