# Changelog

## [0.3.0] - 2026-04-11

### Added
- Thread support for Twitter/X and Bluesky via `thread_items` parameter on `posts_create`
- Typed Pydantic models (`MediaItem`, `ThreadItem`) replacing raw dicts for better LLM ergonomics
- Thread splitting guidance in tool description (hook-first, sentence boundaries, no numbering)
- Validation: platform restriction (twitter/bluesky only), mutual exclusivity with content/media_items, min 2 / max 25 items

### Changed
- `content` parameter defaults to `None` instead of empty string for clearer mutual exclusivity
- `platforms` parameter defaults to `None` instead of mutable `[]`
- `posts_update` media_items also uses typed `MediaItem` model
- Improved `profile_id` documentation

## [0.2.2] - 2026-04-09

- fix: lowercase Docker image tags in release CI

## [0.2.0] - 2026-04-09

### Changed
- Bumped FastMCP dependency to >=3.2.2
- `posts_list` status parameter now uses Literal enum for type safety
- `queue_create_slot` day parameter now uses Literal enum
- Enhanced `posts_create` platforms parameter documentation with object schema

### Added
- Automated version bump and release CI via GitHub Actions
- CHANGELOG.md for tracking changes
