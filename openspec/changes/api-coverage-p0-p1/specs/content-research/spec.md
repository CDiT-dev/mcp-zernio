## ADDED Requirements

### Requirement: Download post info from platforms
The following tools SHALL download post metadata from their respective platforms via Zernio's server-side fetching. Each accepts a `url` parameter and returns content, media URLs, engagement metrics, and author info. All ToolAnnotations(RO, idempotent).

- `tool_youtube_download` — `GET /v1/tools/youtube/download`
- `tool_instagram_download` — `GET /v1/tools/instagram/download`
- `tool_tiktok_download` — `GET /v1/tools/tiktok/download`
- `tool_twitter_download` — `GET /v1/tools/twitter/download`
- `tool_facebook_download` — `GET /v1/tools/facebook/download`
- `tool_linkedin_download` — `GET /v1/tools/linkedin/download`
- `tool_bluesky_download` — `GET /v1/tools/bluesky/download`

#### Scenario: Download YouTube video info
- **WHEN** `tool_youtube_download` is called with a YouTube URL
- **THEN** returns video title, description, view count, like count, channel info, and thumbnail URL

#### Scenario: Download Instagram post
- **WHEN** `tool_instagram_download` is called with an Instagram post URL
- **THEN** returns caption, media URLs, like count, comment count, and author info

#### Scenario: Invalid URL
- **WHEN** any download tool is called with a non-matching platform URL
- **THEN** returns a clear error from the Zernio API

### Requirement: YouTube transcript
The `tool_youtube_transcript` tool SHALL get a YouTube video's transcript via `GET /v1/tools/youtube/transcript`. ToolAnnotations(RO, idempotent).

#### Scenario: Get transcript
- **WHEN** `tool_youtube_transcript` is called with a YouTube URL
- **THEN** returns the video transcript text

### Requirement: Instagram hashtag checker
The `tool_instagram_hashtag` tool SHALL check hashtag performance via `POST /v1/tools/instagram/hashtag-checker`. ToolAnnotations(RO, idempotent).

#### Scenario: Check hashtag
- **WHEN** `tool_instagram_hashtag` is called with a hashtag
- **THEN** returns usage count, related hashtags, and competition level

### Requirement: Subreddit validation
The `validate_subreddit` tool SHALL check subreddit posting rules via `GET /v1/tools/validate/subreddit`. ToolAnnotations(RO, idempotent).

#### Scenario: Check subreddit rules
- **WHEN** `validate_subreddit` is called with a subreddit name
- **THEN** returns posting rules, allowed content types, and flair requirements
