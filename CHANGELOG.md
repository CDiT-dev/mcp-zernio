# Changelog

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
