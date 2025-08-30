# Runtime Data Artifacts

To keep the repository root clean, mutable runtime state is stored (by default) under the `data/` directory. These files are **generated / mutated at runtime** and generally should not be hand‑edited.

## Current Artifacts

| File | Purpose | Default Resolution Order | Env Override |
|------|---------|--------------------------|--------------|
| `data/archive_manifest.db` | SQLite manifest for archived Discord attachments (content hash -> metadata) | 1. `ARCHIVE_DB_PATH` env var 2. existing legacy `archive_manifest.db` in root 3. create `data/archive_manifest.db` | `ARCHIVE_DB_PATH` |
| `data/trustworthiness.json` | JSON store of per-person truth/lie counts + score used by TrustworthinessTrackerTool | 1. explicit ctor arg 2. `TRUST_TRACKER_PATH` env var 3. existing legacy `trustworthiness.json` in root 4. create `data/trustworthiness.json` | `TRUST_TRACKER_PATH` |

## Migration / Backward Compatibility

If legacy root-level files (`archive_manifest.db`, `trustworthiness.json`) are present they will continue to be used until a `data/` version is created, avoiding accidental divergence. New deployments will create the `data/` directory automatically.

Deprecated (2025): The root `trustworthiness.json` path is deprecated in favor of `data/trustworthiness.json` (or an explicit
`TRUST_TRACKER_PATH`). It will be removed from documentation examples after 2025-12-31; environments should migrate now by
moving the file into `data/` (the tracker will not auto-delete the legacy file to avoid data loss).

## Custom Locations

Set the environment variables or pass an explicit path to the respective constructors / modules to place these artifacts elsewhere (e.g., a mounted volume in production).

Examples:

```bash
export ARCHIVE_DB_PATH=/var/lib/udi/archive_manifest.db
export TRUST_TRACKER_PATH=/var/lib/udi/trustworthiness.json
```

## Version Control Guidance

These files are runtime state and normally should be **ignored** in VCS. Add the following to `.gitignore` if not already present:

```
data/*.db
data/*.json
```


(We intentionally allow pattern-based ignore so future runtime JSON/DB artifacts land under the same rule.)

## Rationale

Consolidating mutable state under `data/`:

- Keeps root uncluttered
- Clarifies what is safe to delete/regenerate
- Simplifies container volume mounts / backups
- Avoids accidental commits of evolving local state

