# Privacy and Policy Controls

**Current Implementation** (verified November 3, 2025):

- **Privacy Module**: `src/core/privacy/` (PII detection and redaction)
- **Policy Engine**: `config/policy.yaml` (source allow/block rules)
- **Security Layer**: `src/platform/security/` (rate limiting, privacy controls)
- **Feature Flags**: `enable_pii_detection`, `enable_pii_redaction`
- **RL Override**: `strict` arm forces maximum privacy enforcement

This project includes a privacy layer used by ingestion, retrieval, prompting
and archiving services. The policy file defines allowed sources, forbidden
media types, and redaction masks. Content is passed through the privacy filter
before storage so that email addresses, phone numbers, IP addresses and other
personal data are masked.

## Modules

- `policy_engine` loads `config/policy.yaml` and offers simple allow/block checks.
- `pii_detector` finds email, phone, IP, credit-like numbers and more.
- `redactor` replaces detected spans with masks.
- `privacy_filter` ties the components together and returns a `PrivacyReport`.

## Feature Flags

Two runtime flags gate detection and masking phases (managed via the generic
flag service so they appear in lower‑case form):

| Flag | Default | Effect |
|------|---------|--------|
| `enable_pii_detection` | on | When disabled, the detector is skipped entirely and no spans are produced. |
| `enable_pii_redaction` | on | When disabled (while detection is on) spans are reported but the original text is returned unchanged. |

Both can be overridden per call by passing `context={'enable_detection': bool, 'enable_redaction': bool}` to `privacy_filter.filter_text`.

The reinforcement learning (RL) routing layer may return the arm `strict`; if
so, both detection and redaction are force‑enabled regardless of flags or
context overrides. This guarantees maximal privacy enforcement for high‑risk
evaluation domains.

## Test Coverage

The matrix of flag combinations plus the RL `strict` override path is covered
in `tests/test_privacy_flags.py` to prevent regressions (e.g. accidental
redaction when detection off, or failure to redact under strict arm).

## Ops Commands

The `discord.commands` module exposes a few helpers for operational tasks:

- `ops_privacy_status(events, policy_version)` summarises recent privacy events.
- `ops_privacy_show(report)` displays a previously captured `PrivacyReport`.
- `ops_privacy_sweep(conn, tenant=None)` triggers a retention sweep and returns
  the number of deleted provenance rows.

## Extending

Rules can be adjusted by editing `config/policy.yaml` without changing code.
Additional detectors or redaction strategies can be added under
`core/privacy` as needed.
