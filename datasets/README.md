# Datasets

This directory contains small, reproducible corpora used for offline evaluation.

## Layout
- `golden/` – versioned suites of task records used as golden tests.
- `fixtures/` – auxiliary files (transcripts, metadata) referenced by records.
- `schemas/` – JSON schemas for validating records.

All records are JSON Lines (`.jsonl`) and must conform to
`schemas/task_record.schema.json`.
