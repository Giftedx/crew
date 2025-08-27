# Progress Tracker

## PR1 – Core Services
- [x] prompt_engine
- [x] token_meter
- [x] router
- [x] learning_engine
- [x] eval_harness
- [x] logging schema

## PR2 – Ingestion → Memory → RAG foundation
- [x] adapters for YouTube/Twitch/VOD/social
- [x] vector DB namespaces per tenant/workspace/creator
- [x] transcription, diarization, topic tagging tasks
- [x] Discord commands: /creator, /latest, /context, /collabs, /verify_profiles

## PR3 – RL Everywhere
- [x] routing domain wiring
- [x] prompt domain wiring
- [x] retrieval domain wiring
- [ ] tool planning domain
- [ ] cache/compression domain
- [ ] safety/redaction domain
- [ ] scheduler domain
- [ ] plugin runtime domain

## PR4 – Cost Guards, Budgets, Caching, Cold-Start & Reliability
- [x] token_meter cost guards and budgets
- [x] multi-tier caching layer
- [ ] cold-start priors and shadow bakeoffs
- [x] reliability primitives (retries, breakers)
- [ ] shadow/canary rollout controller

## PR5 – Privacy, PII, Policy & Provenance
- [x] policy engine and config
- [x] PII detection & redaction
- [x] provenance & usage logging
- [x] retention sweeper & export tool
- [ ] Discord ops privacy commands

| Phase | Item | Status | Notes |
|------:|------|:------:|-------|
| PR2 | Adapters (YT/Twitch + fixtures) | ✅ | |
| PR2 | Transcription + chunking + tags | ✅ | |
| PR2 | Qdrant namespaces + retriever | ✅ | |
| PR2 | Discord cmds (/latest, /context, /collabs) | ✅ | |
| PR2 | Tests + docs | ✅ | |
| PR3 | Learning domains registered | ✅ | |
| PR3 | learn_helper wired (routing/prompt/retrieval) | ✅ | |
| PR3 | Shadow/canary flags + ops cmds | ☐ | flags added; ops cmds pending |
| PR3 | Tests + docs | ✅ | |
| PR4 | Budgets + cost guard wired to token_meter/router | ✅ | |
| PR4 | LLM/retrieval caches with TTLs | ✅ | |
| PR4 | Cold-start priors + bakeoff in shadow | ☐ | |
| PR4 | Reliability primitives and circuit breakers | ✅ | |
| PR4 | `/ops status` + alerts | ☐ | command present; alerts pending |
| PR5 | policy_engine + config/policy.yaml | ✅ | |
| PR5 | pii_detector + redactor + privacy_filter | ✅ | |
| PR5 | provenance + usage_log schema and writes | ✅ | |
| PR5 | retention sweeper + export tool | ✅ | |
| PR5 | ops commands + alerts | ☐ | alerts pending |
