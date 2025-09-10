---
title: Documentation Conventions
origin: root_cleanup_phase
status: canonical
last_moved: 2025-09-02
---

This document defines the authoritative rules for creating, placing, naming, and
maintaining documentation in this repository. It exists to prevent regression
after the 2025 root directory cleanup and to keep the `docs/` tree coherent.

## 1. Directory Taxonomy

All markdown documentation MUST live under `docs/` in one of the approved
category subdirectories:

| Category | Path | Purpose |
|----------|------|---------|
| Strategy | `docs/strategy/` | Vision, roadmaps, long‑term planning |
| Architecture | `docs/architecture/` | System design, diagrams, component evolution |
| Operations | `docs/operations/` | Processes, runbooks, change logs, audits |
| Testing | `docs/testing/` | Test conventions, harness usage, test-specific guides |
| Security | `docs/security/` | Secrets handling, threat models, rotation, RBAC |
| Agents | `docs/agents/` | Agent behaviors, orchestration, profiles |
| History (optional) | `docs/history/` | Archived / superseded docs (write‑protected) |

If a document does not clearly fit one of the above, select the closest
existing category and add a rationale line to its front‑matter. Avoid creating
new top-level categories without consensus.

## 2. Front‑Matter Schema

Every markdown file (except README indices) MUST include YAML front‑matter
conforming to this minimal schema:

```yaml
---
title: Human Title Case
origin: <source_reference_or_reason>
status: draft|migrated|canonical|deprecated|archived
last_moved: YYYY-MM-DD
---
```

Additional optional keys:

```yaml
replaces: <old_path_or_slug>
supersedes: <doc_id>
related: [list, of, slugs]
```

Rules:

* `title` MUST be Title Case and match the first visible H1 (if present).
* `origin` captures provenance (e.g. `legacy_root_file`, `analysis_output`, or
  a ticket/issue reference like `issue-123`).
* `status` transitions: `draft → canonical → (deprecated|archived)`.
* `last_moved` updates only when the file changes location, not for content edits.
* If a document supersedes another, keep a tombstone entry in
  `docs/ROOT_DOCS_INDEX.md` mapping old path → new path.

## 3. Naming & Headings

* Filenames use UPPER_SNAKE_CASE for conceptual / spec documents (e.g.
  `docs/strategy/IMPLEMENTATION_ROADMAP.md`), and lower-kebab-case for procedural guides.
  See `docs/operations/` for examples and indexes of runbooks.
* Exactly one H1 (`#`) per file and it MUST match the `title` front‑matter.
* Use sentence case for lower-level headings (H2+), unless they are proper nouns.

## 4. Linting & Style

Enforced (via markdown lint + CI) rules:

* One H1 per file (MD025)
* Blank line after front‑matter and before each heading (MD022/MD031)
* No trailing spaces; tabs prohibited (MD010)
* Lists: consistent ordered numbering (MD029) — use `1.` form in source
* No bare emphasis as heading substitute (MD036)
* Fenced code blocks specify language (MD040) unless plaintext intentionally
* Final newline at EOF (MD047)

Line width: soft 120 char recommendation; do not hard-wrap mid-sentence
purely for width.

## 5. Relocation & Index Policy

Any move / rename must update:

1. Front‑matter `last_moved`
2. `docs/ROOT_DOCS_INDEX.md` mapping (append if new, amend if renamed)
3. All inbound references (grep repo for old path) — update or add redirect note
4. (If superseded) Add `status: deprecated` to the old file and relocate to
  `docs/history/` OR replace with a stub pointing to the new canonical file.

## 6. Deprecated / Historical Content

* Move deprecated but still-referenced documents to `docs/history/` and set
  `status: deprecated`.
* Archived (frozen) documents use `status: archived` and MUST NOT be mutated;
  create a new document instead if changes are required.

## 7. Prohibited Patterns

The following are NOT allowed in the repository root:

* Standalone markdown files in the repository root (all belong under `docs/`)
* Backup variants (avoid committing temporary backup files)
* Redundant copies of migrated documents

## 8. Contribution Workflow (Docs)

1. Draft document under correct category with `status: draft`.
2. Run local markdown validation (`make docs-validate` once target exists).
3. Open PR; reviewer confirms taxonomy & front‑matter compliance.
4. Upon acceptance, set `status: canonical`.
5. If document replaces prior material, update index & add tombstone mapping.

## 9. Tooling & Automation (Planned)

Planned automation tasks (tracked in cleanup roadmap):

* Add markdown lint config (e.g. `.markdownlint.jsonc`) mirroring rules above.
* CI job: run lint + link reference validation script (`scripts/validate_docs.py`).
* Pre-commit hook template ensuring front‑matter presence.

## 10. Quick Compliance Checklist

Before merging a new / updated doc:

* [ ] Correct category & path
* [ ] Valid front‑matter keys
* [ ] Single H1 matching `title`
* [ ] Fenced code blocks labeled
* [ ] Index updated (if moved / replaced)
* [ ] No root-level stray copies introduced

---

Violations should block CI once automation is in place. Until then, reviewers
must manually enforce this specification.
