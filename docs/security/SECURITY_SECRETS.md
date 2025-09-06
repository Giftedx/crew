---
title: Secrets & Security Operations
origin: SECURITY_SECRETS.md (root)
status: migrated
last_moved: 2025-09-02
---

## Overview

This document describes how to manage and rotate secrets for the Ultimate Discord Intelligence Bot. It was migrated from the repository root during the September 2025 documentation consolidation.

## Table of Contents

1. Secret Inventory
2. Storage & Injection Best Practices
3. Rotation Playbooks
4. Webhook Secret Zero‑Downtime Rotation
5. Automated Scanning (gitleaks)
6. Responding to Exposure
7. Git History Purge Procedure
8. Local Developer Hygiene

## 1. Secret Inventory

| Category | Examples | Notes |
|----------|----------|-------|
| LLM API Keys | `OPENAI_API_KEY`, `OPENROUTER_API_KEY` | Long-lived by default; prefer project-scoped keys. |
| Discord | `DISCORD_BOT_TOKEN`, webhook URLs | Webhook URLs are effectively secrets. |
| Vector DB | `QDRANT_API_KEY` | JWT-like; rotate in Qdrant console. |
| Archive Service | `ARCHIVE_API_TOKEN` | Only if archive feature enabled. |
| Webhook Shared Secrets | `WEBHOOK_SECRET_DEFAULT`, `WEBHOOK_SECRET_BACKUP` | Dual-secret rotation pattern. |
| Redis / Postgres | Credentials / URLs | Use least privilege roles. |
| Plugin Secrets | (plugin-specific) | Keep out of code; inject at runtime. |

## 2. Storage & Injection Best Practices

* Use a cloud secrets manager (AWS Secrets Manager, GCP Secret Manager, Vault, Doppler, 1Password Connect) for production.
* Application process receives secrets as environment variables at startup (12‑factor principle).
* Never bake real secrets into container images or commit `.env` files.
* Apply least privilege: separate keys per environment (dev/staging/prod) and avoid sharing.
* Restrict network egress to only required domains (OpenAI, Qdrant, Discord, etc.).

## 3. Rotation Playbooks

Recommended rotation cadence: every 90 days or immediately on suspicion of compromise.

### LLM / External API Keys

1. Create new key in provider dashboard.
2. Update secret manager entry (do not delete old key yet if provider lacks immediate invalidation).
3. Redeploy services picking up new env.
4. After validation, revoke old key.

### Discord Bot Token

1. Regenerate in Discord Developer portal (Bot tab).
2. Update secret manager / `.env`.
3. Restart bot (old token invalidated instantly).

### Qdrant API Key

1. Generate new API key in Qdrant Cloud.
2. Deploy with both if dual-key supported; otherwise swap & redeploy quickly.
3. Delete old key.

## 4. Webhook Secret Zero‑Downtime Rotation

The project supports a dual-secret pattern: `WEBHOOK_SECRET_DEFAULT` + `WEBHOOK_SECRET_BACKUP`.

Procedure:

1. Ensure `WEBHOOK_SECRET_BACKUP` is empty or a previous retired secret.
2. Run: `python scripts/rotate_webhook_secret.py --write` (dry-run by default without `--write`).
3. Commit *only* if you are rotating placeholders; for real deployments update secrets manager instead of committing.
4. Redeploy services so both new default and promoted backup are accepted.
5. After traffic stabilizes, clear (or replace) the backup secret for next cycle.

## 5. Automated Scanning (gitleaks)

* Pre-commit hook runs `gitleaks` with custom rules (`.gitleaks.toml`).
* CI should also execute: `gitleaks detect --config=.gitleaks.toml` (add to workflow).
* Redaction enabled to avoid leaking secret values in logs.

## 6. Responding to Exposure

1. Identify scope: which secrets displayed/committed? (`git log -p` / PR diff).
2. Immediate revoke/rotate exposed secrets.
3. Purge leaked artifacts from issue trackers / logs.
4. If tokens allowed privileged actions, audit recent usage (Discord audit logs, OpenAI usage, Qdrant logs).
5. Perform git history purge (section 7) for public repos to reduce future accidental reintroduction.
6. Document incident & improvements (add to `incidents.md` or create one if missing).

## 7. Git History Purge Procedure

If a real secret was committed:

```bash
git checkout main
git pull --ff-only
git filter-repo --invert-paths --path .env --path secrets.txt   # example
git push --force origin main
```

Then invalidate all previously cloned credentials (force developers to reclone) and rotate the secret.
If `git filter-repo` not installed: `pip install git-filter-repo`.

Alternative (BFG):

```bash
bfg --delete-files .env
bfg --replace-text replacements.txt
```

## 8. Local Developer Hygiene

* Use `.env.example` & `.env.production.example`; never add `.env`.
* Add an editor setting to mark `.env` as sensitive (VS Code: `"files.watcherExclude"`).
* Run `pre-commit run --all-files` before pushing.
* Keep your personal OpenAI / Discord keys separate from organization production keys.

---
Questions / improvements: open an issue or add proposals to `FUTURE_WORK.md` under a **Security** section.
