# Provenance Logging

Each ingested item records provenance metadata including source URL,
license information and a checksum. Provenance entries enable future audits
and consent tracking. The `provenance` table stores these fields:

- `content_id`
- `source_url`
- `source_type`
- `retrieved_at`
- `license`
- `terms_url`
- `consent_flags`
- `checksum_sha256`

Usage logs reference provenance IDs to provide traceable records of how
content was used in prompts or responses.
