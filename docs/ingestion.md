# Ingestion Guide

This document describes the lightweight ingestion pipeline used in tests.
It supports fetching metadata and transcripts from YouTube and Twitch,
transcribing audio when transcripts are missing, and pushing chunks into
a Qdrant vector store for later retrieval.

## Running a one-shot ingest

```bash
python -m ingest.pipeline <url>
```

The pipeline reads configuration from `config/ingest.yaml` and expects
environment variables for external services when needed.
