## ADDED Requirements

### Requirement: Retweet
The `twitter_retweet` tool SHALL retweet a tweet via `POST /v1/twitter/retweet`. ToolAnnotations(Write, not idempotent).

#### Scenario: Retweet
- **WHEN** `twitter_retweet` is called with account_id and tweet_id
- **THEN** the tweet is retweeted

### Requirement: Unretweet
The `twitter_unretweet` tool SHALL undo a retweet via `DELETE /v1/twitter/retweet`. ToolAnnotations(Write, idempotent).

#### Scenario: Unretweet
- **WHEN** `twitter_unretweet` is called with account_id and tweet_id
- **THEN** the retweet is removed

### Requirement: Bookmark tweet
The `twitter_bookmark` tool SHALL bookmark a tweet via `POST /v1/twitter/bookmark`. ToolAnnotations(Write, not idempotent).

#### Scenario: Bookmark
- **WHEN** `twitter_bookmark` is called with account_id and tweet_id
- **THEN** the tweet is bookmarked

### Requirement: Follow user
The `twitter_follow` tool SHALL follow a Twitter user via `POST /v1/twitter/follow`. ToolAnnotations(Write, not idempotent).

#### Scenario: Follow
- **WHEN** `twitter_follow` is called with account_id and target_user_id
- **THEN** the user is followed
