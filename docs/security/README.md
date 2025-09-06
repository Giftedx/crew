---
title: Security Documentation Overview
origin: root_cleanup_phase
status: canonical
last_moved: 2025-09-02
---

This index summarizes the security-related documents and their intent.

## Contents

| File | Purpose |
|------|---------|
| `SECURITY_SECRETS.md` | Secrets management, rotation guidance, and environment hygiene |
| `config.md` | Secure configuration loading, precedence, and validation flows |
| `moderation.md` | Content moderation pipeline and enforcement stages |
| `ops.md` | Operational security procedures (on-call, incident handling) |
| `secrets.md` | Additional notes and references for secret scoping and storage |
| `signing.md` | Request signing, signature verification, and trust boundaries |
| `threat_model.md` | High-level threat model, assets, actors, mitigations |
| `validation.md` | Input validation primitives, URL/HTTP guards, schema linting |

## Conventions

All security docs follow the repository-wide conventions in `../conventions.md`.
Use `status: canonical` only after peer review. Deprecated guidance should be
moved to `docs/history/` with an explanatory stub.

## Related References

* Operational runbooks: `docs/operations/`
* Configuration reference: `docs/configuration.md`
* Privacy & retention: `docs/privacy.md`, `docs/retention.md`

---
Update this overview when adding or renaming security documents.
