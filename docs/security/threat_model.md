# Security Threat Model

> Version: 0.1 (bootstrap)
> Scope: Discord entrypoints, REST façade, Agents / LLM routing, Ingestion & Scheduler, Archiver, Memory (vector + KG + unified), Plugins & Marketplace (future), Grounding & Verification, Privacy/PII, Observability & Incidents.

This document captures an initial STRIDE‑style threat model for the platform. It will evolve as features (plugins, marketplace signing, advanced RL domains) are hardened. Each section lists: Assets, Trust Boundaries, Threats, Existing Controls, Gaps / Planned Mitigations (mapped to PR tasks).

---

## 1. Assets

- API / Discord bot token(s)
- Secrets (provider keys, webhook signing secrets, model keys)
- User generated content (Discord messages, attachments)
- Ingested media & transcripts (copyright / privacy sensitive)
- Vector embeddings & Knowledge Graph nodes/edges (derived intelligence)
- Archiver manifest (canonical asset references, message IDs)
- RL bandit state (routing / prompt selection data)
- Marketplace / Plugin manifests & signed artifacts (supply chain)
- AnswerContracts + provenance (grounding guarantees)
- Audit / security / incident logs

## 2. Trust Boundaries

1. Discord Gateway / Slash Commands → Internal command handler.
2. User provided URLs / media → Ingestion & Archiver.
3. External content fetch (yt-dlp / Twitch / web) → Downloader sandbox.
4. LLM Provider APIs (OpenRouter / models) → Router & Token Meter.
5. Plugin Sandbox (future) → Core service adapters.
6. REST façade (archive / retrieval) → Internal services.
7. Webhook / callback ingress (future) → Verification layer.
8. Scheduler pollers (network) → Internal queue.

## 3. STRIDE Analysis (Summary)

| Category | Representative Threat | Target | Existing Controls | Gap / Mitigation |
|----------|----------------------|--------|-------------------|------------------|
| Spoofing | Forged webhook / callback | Webhook endpoints | HMAC signing helpers (`security.signing`) | Enforce verification + clock skew + replay cache (PR18) |
| Tampering | Manipulate manifest / provenance rows | Storage (archiver, KG) | Dedup by sha256 | Integrity hash logging, optional signed manifests, DB row immutability policy |
| Repudiation | User denies issuing destructive command | Ops slash cmds | Structured security events | Add actor signatures & audit chain IDs |
| Information Disclosure | SSRF to internal metadata service | Network fetch | `net_guard.is_safe_url` (basic) | Add redirect revalidation, host allow/deny lists, size caps |
| Denial of Service | Command flood causing token spend | Router / LLM | Simple token bucket | Multi-scope rate limiter + escalating cooldowns |
| Elevation of Privilege | Unprivileged user runs ops command | Discord commands | Role→perm map | ABAC (tenant/workspace/risk tier), defense in depth |
| Supply Chain | Malicious plugin / model | Plugin runtime | (Not fully implemented) | Signed manifests, trust tiers, capability gating (PR8–10) |
| Data Poisoning | Adversarial ingestion altering RL policy | Ingestion / RL | Minimal validation | Provenance scoring, anomaly detection, quarantine |
| Privacy / PII Leak | Sensitive text flows to model unredacted | Prompt / retrieval | Privacy filter stub | Full PII detection + redaction metrics + retention sweeps |
| Hallucination | Ungrounded answer misleads users | RAG answer path | Grounding contract & verifier (basic) | Confidence scoring, abstain thresholds, unsupported claim alerts |

## 4. Detailed Threats & Planned Controls

### 4.1 Spoofed Webhooks / Callbacks

**Threat:** Attacker sends forged request to internal endpoint to enqueue jobs or inject data.
**Controls:** HMAC (timestamp + nonce) primitives exist.
**Mitigations:** Enforce signature check on *all* inbound webhook endpoints; replay cache (nonce LRU) already available; reject skew > tolerance; security event on failure.

### 4.2 SSRF & Unsafe Fetch

**Threat:** Crafted URL resolves to internal IP (169.254/ metadata, RFC1918) or redirects there.
**Controls:** Basic public-IP check.
**Mitigations:** Add redirect chain revalidation, host allowlist/denylist, max bytes, content-type allowlist, per-host rate limiting.

### 4.3 Excessive LLM Spend / Abuse

**Threat:** Flood of `/context` or tool invocations consumes budget.
**Controls:** Token bucket (global).
**Mitigations:** Per-user/guild/command/provider buckets, progressive backoff, cooldown unlock command, alerts on burst spend.

### 4.4 Privilege Escalation via Misconfigured Roles

**Threat:** User obtains `ops` capabilities accidentally or via stale config.
**Controls:** Role→permission YAML.
**Mitigations:** ABAC overlay (risk tier match, channel constraints), signed config optional, runtime diff detection + warning.

### 4.5 Data Exfiltration via Plugins (Future)

**Threat:** Plugin exfiltrates embeddings or secrets.
**Mitigations (planned):** Capability manifest, network egress allowlist, memory namespace scoping, cost & quota guards, PII redaction in adapters.

### 4.6 Hallucination / Unsupported Claims

**Threat:** Ungrounded answer presented as fact.
**Controls:** AnswerContract + simple verifier.
**Mitigations:** Evidence pack scoring, verifier escalate path (revise/fail), abstain fallback + user explanation, contradiction checks against KG.

### 4.7 PII Retention & Compliance Drift

**Threat:** Sensitive data retained beyond policy or exported unredacted.
**Controls:** Baseline privacy filter.
**Mitigations:** Provenance + retention sweeps, export tool with redaction, per-tenant retention policy enforcement & logs.

### 4.8 Supply Chain (Plugins / Marketplace)

**Threat:** Malicious or compromised plugin introduces backdoor.
**Mitigations:** Signing (ed25519 / Sigstore), trust tiers, staged rollout with health metrics, lockfile, advisory ingestion.

### 4.9 Scheduler / Ingestion Flood

**Threat:** High-frequency polling of noisy sources saturates resources.
**Mitigations:** RL-informed poll interval bounds, per-tenant source quotas, queue prioritization, dead-letter thresholds + alerts.

### 4.10 Incident Response Gaps

**Threat:** Slow detection of systemic failure or attack.
**Mitigations:** Synthetic probes, SLO burn rate detection, Discord incident workflow with timeline + postmortem template.

## 5. Risk Ranking (Current State)

| Risk | Likelihood | Impact | Priority |
|------|-----------|--------|----------|
| SSRF / Unsafe fetch | Med | High | High |
| Webhook forgery / replay | Med | High | High |
| Excessive spend | High | Med | High |
| Hallucination w/o grounding | Med | Med | High |
| Privilege misconfig | Low | High | High |
| Supply chain (future) | Med | High | High |
| PII retention gap | Med | Med | Med |
| Plugin exfiltration (future) | Low (pre-marketplace) | High | Med |
| Ingestion flood | Med | Med | Med |
| Incident blind spots | Med | Med | Med |

## 6. Roadmap Linkage

- **PR18**: ABAC, advanced rate limiting, net guard hardening, webhook enforcement (HMAC timestamp+nonce, skew & replay checks), secrets rotation, SBOM/SCA.
- **PR8–10**: Plugin sandbox, marketplace signing & test gates.
- **PR17 Enhancements**: Stronger grounding confidence & abstain logic.
- **PR5/Privacy Expansion**: Full PII detection + retention sweeps.
- **PR11/PR3**: Scheduler RL fairness & poll cadence optimization.
- **PR13**: Synthetics & SLO burn alerts to reduce MTTR.

## 7. Assumptions

- Discord bot token stored only in environment (not committed) and rotated manually now. Rotation automation planned.
- No untrusted arbitrary code execution outside (future) plugin sandbox.
- Single-process deployment; distributed rate limiting not yet required.

## 8. Open Questions

1. Required compliance regimes (GDPR/CCPA) scope? → influences retention/export detail.
2. Plugin distribution channel(s) trust root format? → impacts signing chain.
3. Model provider isolation levels? Separate keys per tenant? → cost attribution + compromise blast radius.

---

### Appendix A: Planned Webhook Verification Control

| Aspect | Design |
|--------|--------|
| Threats | Spoofed origin (Spoofing), replay (Repudiation/Tampering), payload manipulation (Tampering) |
| Secrets Source | `config/security.yaml` → `webhooks.secrets` mapping (supports multiple keys for rotation) |
| Signature Scheme | HMAC-SHA256 over `timestamp.nonce.payload` (implemented in `security.signing`) |
| Headers | `X-Signature`, `X-Timestamp`, `X-Nonce` (override capable) |
| Freshness | Reject if `abs(now - timestamp) > clock_skew_seconds` |
| Replay Protection | LRU nonce cache (bounded) via `signing._seen_nonces` + pruning |
| Rotation | Attempt verification with all active secrets (primary + next) before fail |
| Events | `action="webhook"` with `decision` allow/block; reasons: `missing_headers`, `skew`, `invalid_signature`, `replay` |
| Failure Mode | Raise `SecurityError`; caller returns 401/403 with generic message |
| Future Enhancements | Per-source key scoping, key ID header, optional body hash canonicalization |

This appendix will be merged into main control sections once implemented.

---
**Maintenance:** Update on any new external integration, capability expansion, or post-incident review. Version bump + changelog entry required.
