# Source Connectors

Connectors encapsulate discovery logic for a platform. They implement the
`SourceConnector` protocol defined in `ingest.sources.base` and return new
`DiscoveryItem` objects when the scheduler polls them.

This repository ships minimal `YouTubeConnector` and `TwitchConnector` classes.
They treat the watch handle as both the external ID and the URL to ingest and
emit each handle once. Real deployments would replace these with implementations
that call external APIs or scrape feeds while respecting rate limits and
policies.
