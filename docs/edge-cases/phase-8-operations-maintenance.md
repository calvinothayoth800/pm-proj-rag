# Phase 8 Edge Cases: Operations And Maintenance

Purpose: keep the fixed corpus fresh without expanding scope accidentally.

## Edge Cases

- Groww changes URL slugs or redirects old URLs.
  - Expected handling: do not auto-follow into new corpus membership; require manual architecture/config update.
- A page disappears or returns persistent errors.
  - Expected handling: mark source unhealthy and keep the corpus size unchanged until manually reviewed.
- Someone updates `last_checked` without refreshing content.
  - Expected handling: refresh workflow should record fetch run metadata.
- Ingestion adds linked pages during maintenance.
  - Expected handling: fail allowlist validation.
- Handoff omits important recent changes.
  - Expected handling: maintenance checklist requires `docs/handoff.md` update.
- README drifts from architecture.
  - Expected handling: include README in release/readiness checks once created.
- Data files contain copyrighted full-page snapshots.
  - Expected handling: keep raw data local as needed; avoid publishing unnecessary full scraped content.
- Dependencies or external APIs change.
  - Expected handling: keep ingestion/retrieval tests runnable locally and document required setup.

## Checks

- `configs/corpus.yaml` still contains exactly five URLs.
- Every source has current `last_checked`.
- Index metadata matches the latest ingestion run.
- `docs/handoff.md` reflects current phase and known limitations.

