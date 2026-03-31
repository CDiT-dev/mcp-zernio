## ADDED Requirements

### Requirement: Per-post engagement metrics
The `analytics_posts` tool SHALL return per-post engagement metrics (likes, comments, shares, impressions, reach). Results SHALL be sortable and paginated (default 10, max 50). When a `post_id` parameter is provided, the tool SHALL return the engagement timeline for that specific post. Response MUST include human-readable platform names alongside metric values.

#### Scenario: Top performing posts
- **WHEN** `analytics_posts` is called without `post_id`
- **THEN** returns paginated list of posts with engagement metrics, sorted by total engagement descending

#### Scenario: Single post timeline
- **WHEN** `analytics_posts` is called with `post_id="abc123"`
- **THEN** returns engagement timeline for that post (equivalent to Zernio's post-timeline endpoint)

#### Scenario: Response includes platform context
- **WHEN** results are returned
- **THEN** each entry includes `platform` (e.g., "Instagram"), `post_text` (truncated), and `platformPostUrl` alongside numeric metrics

#### Scenario: ToolAnnotations
- **WHEN** `analytics_posts` is registered
- **THEN** it MUST have `ToolAnnotations(readOnlyHint=True, idempotentHint=True)`

### Requirement: Aggregated analytics insights
The `analytics_insights` tool SHALL accept a `type` parameter as `Literal["best_time", "content_decay", "daily_metrics", "posting_frequency"]` and return the corresponding aggregated analytics data. The docstring MUST include plain-language triggers:
- `best_time`: "Use when the user asks when to post or what time gets most engagement"
- `content_decay`: "Use when the user asks how long posts stay relevant or why reach drops off"
- `daily_metrics`: "Use for general performance overviews or 'how are my posts doing?'"
- `posting_frequency`: "Use when the user asks if they're posting enough or too much"

The `origin` parameter (mapped from Zernio API's `source`) SHALL use `Literal["all", "via_zernio", "imported"]` — never expose the API's confusing `"late"` value.

#### Scenario: Best posting time
- **WHEN** `analytics_insights` is called with `type="best_time"`
- **THEN** returns day-of-week and hour-of-day engagement data from Zernio's best-time endpoint

#### Scenario: Daily metrics overview
- **WHEN** `analytics_insights` is called with `type="daily_metrics"` and optional date range
- **THEN** returns day-by-day aggregated volume and engagement metrics

#### Scenario: Origin filter
- **WHEN** `analytics_insights` is called with `origin="via_zernio"`
- **THEN** server maps `"via_zernio"` to API's `source="late"` parameter transparently

#### Scenario: ToolAnnotations
- **WHEN** `analytics_insights` is registered
- **THEN** it MUST have `ToolAnnotations(readOnlyHint=True, idempotentHint=True)`
