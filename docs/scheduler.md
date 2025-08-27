# Scheduler

The scheduler watches external sources for new content and enqueues ingest jobs.
It uses `watchlist` entries stored in the ingestion SQLite database and a
priority queue stored in the same database.

## Watchlists

A watchlist entry describes a source to poll. Minimal fields:

- `source_type` – e.g. `youtube` or `twitch`.
- `handle` – identifier or URL for the source.
- `tenant` / `workspace` – routing context.

## Connectors

Connectors implement a small interface that discovers new items for a watch. In
this repository the connectors are deliberately tiny and emit each handle once,
which keeps tests fast and deterministic.

## Running

```python
from scheduler import Scheduler, PriorityQueue
from ingest.sources.youtube import YouTubeConnector
from ingest import models

conn = models.connect("ingest.db")
queue = PriorityQueue(conn)
sched = Scheduler(conn, queue, {"youtube": YouTubeConnector()})

sched.add_watch(tenant="default", workspace="main", source_type="youtube", handle="vid1")
sched.tick()        # discover and enqueue jobs
sched.worker_run_once(store=None)  # process one job
```

The Discord ops helpers expose convenience wrappers: `/ops ingest watch add`,
`/ops ingest watch list`, and `/ops ingest queue status`.
