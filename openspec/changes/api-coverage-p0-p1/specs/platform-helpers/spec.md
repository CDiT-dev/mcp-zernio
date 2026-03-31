## ADDED Requirements

### Requirement: Reddit search
The `reddit_search` tool SHALL search Reddit posts via `GET /v1/reddit/search`. ToolAnnotations(RO, idempotent).

#### Scenario: Search Reddit
- **WHEN** `reddit_search` is called with a query string
- **THEN** returns matching Reddit posts with titles, subreddits, and scores

### Requirement: Reddit feed
The `reddit_feed` tool SHALL get a subreddit's feed via `GET /v1/reddit/feed`. ToolAnnotations(RO, idempotent).

#### Scenario: Get subreddit feed
- **WHEN** `reddit_feed` is called with a subreddit name
- **THEN** returns recent posts from that subreddit

### Requirement: Reddit subreddits
The `reddit_subreddits` tool SHALL list the user's joined subreddits via `GET /v1/accounts/{accountId}/reddit-subreddits`. ToolAnnotations(RO, idempotent).

#### Scenario: List subreddits
- **WHEN** `reddit_subreddits` is called with a Reddit account_id
- **THEN** returns list of joined subreddits

### Requirement: Reddit flairs
The `reddit_flairs` tool SHALL get available flairs for a subreddit via `GET /v1/accounts/{accountId}/reddit-flairs`. ToolAnnotations(RO, idempotent).

#### Scenario: Get flairs
- **WHEN** `reddit_flairs` is called with account_id and subreddit
- **THEN** returns available flair options

### Requirement: LinkedIn mentions
The `linkedin_mentions` tool SHALL get LinkedIn mentions via `GET /v1/accounts/{accountId}/linkedin-mentions`. ToolAnnotations(RO, idempotent).

#### Scenario: Get mentions
- **WHEN** `linkedin_mentions` is called with a LinkedIn account_id
- **THEN** returns recent mentions of the user/org

### Requirement: LinkedIn org analytics
The `linkedin_org_analytics` tool SHALL get organization analytics via `GET /v1/accounts/{accountId}/linkedin-aggregate-analytics`. ToolAnnotations(RO, idempotent).

#### Scenario: Get org analytics
- **WHEN** `linkedin_org_analytics` is called with a LinkedIn account_id
- **THEN** returns follower growth, impressions, and engagement metrics

### Requirement: Pinterest boards
The `pinterest_boards` tool SHALL list Pinterest boards via `GET /v1/accounts/{accountId}/pinterest-boards`. ToolAnnotations(RO, idempotent).

#### Scenario: List boards
- **WHEN** `pinterest_boards` is called with a Pinterest account_id
- **THEN** returns list of boards with names and pin counts

### Requirement: YouTube playlists
The `youtube_playlists` tool SHALL list YouTube playlists via `GET /v1/accounts/{accountId}/youtube-playlists`. ToolAnnotations(RO, idempotent).

#### Scenario: List playlists
- **WHEN** `youtube_playlists` is called with a YouTube account_id
- **THEN** returns list of playlists with titles and video counts
