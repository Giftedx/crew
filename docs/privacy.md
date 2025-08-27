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

## Extending
Rules can be adjusted by editing `policy.yaml` without changing code.
Additional detectors or redaction strategies can be added under
`core/privacy` as needed.
