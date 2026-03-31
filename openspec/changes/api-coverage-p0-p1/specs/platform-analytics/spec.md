## ADDED Requirements

### Requirement: YouTube daily views
The `analytics_youtube_daily` tool SHALL return daily view stats via `GET /v1/analytics/youtube/daily-views`. ToolAnnotations(RO, idempotent).

#### Scenario: Get daily views
- **WHEN** `analytics_youtube_daily` is called with optional date range
- **THEN** returns day-by-day view counts for the YouTube account

### Requirement: Instagram account insights
The `analytics_instagram_insights` tool SHALL return Instagram account metrics via `GET /v1/analytics/instagram/account-insights`. ToolAnnotations(RO, idempotent).

#### Scenario: Get Instagram insights
- **WHEN** `analytics_instagram_insights` is called
- **THEN** returns reach, impressions, profile views, and follower growth

### Requirement: Instagram demographics
The `analytics_instagram_demographics` tool SHALL return audience demographic data via `GET /v1/analytics/instagram/demographics`. ToolAnnotations(RO, idempotent).

#### Scenario: Get demographics
- **WHEN** `analytics_instagram_demographics` is called
- **THEN** returns age ranges, gender distribution, and top locations

### Requirement: Post engagement timeline
The `analytics_post_timeline` tool SHALL return per-post engagement over time via `GET /v1/analytics/post-timeline`. ToolAnnotations(RO, idempotent).

#### Scenario: Get post timeline
- **WHEN** `analytics_post_timeline` is called with a post_id
- **THEN** returns time-series engagement data (likes, comments, shares over time)
