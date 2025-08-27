# Grounding Guarantees

The grounding layer ensures every user answer is backed by verifiable
evidence. Answers reference sources via citations and a lightweight verifier
checks that minimum citation counts are satisfied.

Configuration lives in `config/grounding.yaml` and may be overridden per
tenant. The default `/context` command requires at least three citations.

The `grounding` package provides helpers to gather evidence from memory,
build validated answer contracts and verify them. Ops helpers expose a
`/ops grounding audit` command for quick inspection.
