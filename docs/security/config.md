# Security Configuration

The file `config/security.yaml` defines role permissions, basic rate limits, and
simple moderation rules.

Example:

```yaml
role_permissions:
  viewer: []
  ops:
    - ingest.backfill
  admin:
    - '*'
rate_limits:
  default_per_minute: 60
moderation:
  banned_terms:
    - banned
  action: redact
```
