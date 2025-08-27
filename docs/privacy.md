# Privacy and Policy Controls

This project includes a privacy layer used by ingestion, retrieval, prompting
and archiving services. The policy file defines allowed sources, forbidden
media types, and redaction masks. Content is passed through the privacy filter
before storage so that email addresses, phone numbers, IP addresses and other
personal data are masked.

## Modules
- `policy_engine` loads `policy.yaml` and offers simple allow/block checks.
- `pii_detector` finds email, phone, IP, credit-like numbers and more.
- `redactor` replaces detected spans with masks.
- `privacy_filter` ties the components together and returns a `PrivacyReport`.

## Ops Commands

The `discord.commands` module exposes a few helpers for operational tasks:

- `ops_privacy_status(events, policy_version)` summarises recent privacy events.
- `ops_privacy_show(report)` displays a previously captured `PrivacyReport`.
- `ops_privacy_sweep(conn, tenant=None)` triggers a retention sweep and returns
  the number of deleted provenance rows.

## Extending
Rules can be adjusted by editing `policy.yaml` without changing code.
Additional detectors or redaction strategies can be added under
`core/privacy` as needed.
