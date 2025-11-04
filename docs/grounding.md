# Grounding Guarantees

**Current Implementation** (verified November 3, 2025):

- **Configuration**: `config/grounding.yaml` (tenant-aware citation requirements)
- **Grounding Package**: `src/grounding/` (evidence gathering and verification)
- **Citation Utils**: Automated numeric bracketed citation formatting
- **Verification Tools**: 10 tools in Verification category (9% of 111 total tools)

The grounding layer ensures every user answer is backed by verifiable
evidence. Answers reference sources via citations and a lightweight verifier
checks that minimum citation counts are satisfied.

Configuration lives in `config/grounding.yaml` and may be overridden per
tenant. The default `/context` command requires at least three citations.

The `grounding` package provides helpers to gather evidence from memory,
build validated answer contracts and verify them. Ops helpers expose a
`/ops grounding audit` command for quick inspection.

## Citation Formatting Enforcement

Grounded answers MUST end with ordered numeric bracketed citations appended
exactly once, for each piece of evidence in the contract, e.g.:

```text
The moon has no substantial atmosphere. [1][2][3]
```

Rules:

- Order reflects the order of the `Evidence` sequence passed into the contract.
- Citation indices are 1-indexed and contiguous (no gaps, no repeats).
- Empty evidence list -> no citation tail appended.
- Formatting is applied centrally by `grounding.citation_utils.append_numeric_citations`.
- The helper is idempotent; supplying an answer already suffixed with the
  correct tail will not duplicate it.

Deviation from this format will cause governance tests to fail; construct or
modify grounded answers only before citation formatting to avoid duplicate
tails.
