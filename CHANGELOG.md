# Changelog

## [0.3.21] - 2026-04-13

- fix: use {conv_id:path} to handle Bluesky IDs with slashes


## [0.3.20] - 2026-04-13

- feat: comment thread detail view with commenter names


## [0.3.19] - 2026-04-13

- fix: Open in App links — extract URL from platformData


## [0.3.18] - 2026-04-13

- fix: cache-bust JS via startup timestamp in script src


## [0.3.17] - 2026-04-13

- fix: cache-bust JS loading with Date.now() query param


## [0.3.16] - 2026-04-13

- feat: inline video preview for reel/video attachments


## [0.3.15] - 2026-04-13

- feat: render message attachments (reels, videos, images)


## [0.3.14] - 2026-04-13

- fix: comment + review normalizers for Zernio field names


## [0.3.13] - 2026-04-13

- fix: commit updated uv.lock with resend dependency


## [0.3.12] - 2026-04-12

- fix: expose core state/render to interactions JS, fix dark mode toggle


## [0.3.11] - 2026-04-12

- fix: normalize conversation + message data in proxy


## [0.3.10] - 2026-04-12

- fix: pass accountId to conversation API + fix endpoint URL path


## [0.3.9] - 2026-04-12

- fix: conversation normalizer field mapping + desktop layout CSS


## [0.3.8] - 2026-04-12

- fix: add SPA catch-all routes for /inbox/conv/*, /archived, /sent


## [0.3.7] - 2026-04-12

- fix: add missing settings import to inbox.py


## [0.3.6] - 2026-04-12

- chore: pass inbox auth env vars through compose.yaml


## [0.3.5] - 2026-04-12

- feat: inbox login page with passphrase + Resend magic links


## [0.3.4] - 2026-04-12

- feat: universal inbox UI — server proxy + SPA frontend


## [0.3.3] - 2026-04-12

- docs: clarify that Threads (Meta) does not support thread_items


## [0.3.2] - 2026-04-11

- fix: pre-check post status in delete/unpublish to avoid Zernio API 500s


## [0.3.1] - 2026-04-11

- feat: add thread_items support for Twitter/X and Bluesky (CDI-968)


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
