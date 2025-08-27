# Privacy and Policy Controls

This project includes a lightweight privacy layer used by ingestion and memory
services. The policy file defines allowed sources, forbidden data types, and
redaction masks. Content is passed through the privacy filter before storage so
that email addresses, phone numbers, and other personal data are masked.

## Modules
- `policy_engine` loads `policy.yaml` and offers simple allow/block checks.
- `pii_detector` finds email and phone patterns.
- `redactor` replaces detected spans with masks.
- `privacy_filter` ties the components together and returns a `PrivacyReport`.

## Extending
Rules can be adjusted by editing `policy.yaml` without changing code.
Additional detectors or redaction strategies can be added under
`ultimate_discord_intelligence_bot/privacy` as needed.
