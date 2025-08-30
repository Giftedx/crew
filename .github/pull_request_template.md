# Pull Request

## Summary

Explain the change: what problem does it solve or improvement does it bring?

## Type of Change

- [ ] feat: New feature
- [ ] fix: Bug fix
- [ ] refactor: Code refactor (no functional change)
- [ ] docs: Documentation update
- [ ] test: Adding or correcting tests
- [ ] chore: Tooling/infra/housekeeping
- [ ] perf: Performance improvement
- [ ] style: Formatting (no logic)

## Checklist

- [ ] Tests added/updated (unit + any integration impacted)
- [ ] All tests pass locally (`pytest`)
- [ ] Typing passes (`make type` or mypy reports 0 new errors)
- [ ] Lint & format pass (`make lint` / `make format`)
- [ ] CHANGELOG updated (Unreleased section)
- [ ] README/docs updated if configuration, flags, or tool contracts changed
- [ ] Tenancy respected (explicit tenant/workspace context where required)
- [ ] Feature flags added for new subsystems (`ENABLE_<AREA>_<FEATURE>`)
- [ ] No leaking `Any` / added precise signatures
- [ ] UTC timestamps used (no `utcnow()` / naive `datetime.now()`)
- [ ] External calls routed through existing helpers (http utils, token meter, etc.)
- [ ] No unguarded direct model/provider SDK calls (use routing + caching layers)

## Testing Notes

Describe key test scenarios manually executed (if any) and links/log excerpts for complex flows.

## Deployment / Rollout Considerations

- Backwards compatibility notes
- Data migrations required?
- Feature flag default state

## Screenshots / Logs (optional)

## Follow-Ups (optional)

List any deferred tasks or future hardening ideas.
