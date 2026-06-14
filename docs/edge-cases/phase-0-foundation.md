# Phase 0 Edge Cases: Project Foundation

Purpose: prevent unclear ownership, conflicting requirements, and accidental scope drift before implementation starts.

## Edge Cases

- Problem statement says official AMC/AMFI/SEBI sources, but current project rule says only five exact Groww URLs.
  - Expected handling: treat `docs/architecture.md`, `configs/corpus.yaml`, and `docs/handoff.md` as the active source boundary.
- Multiple copies of docs exist or paths change.
  - Expected handling: use files under `docs/` as canonical project docs.
- New contributors add sources without reading the fixed-corpus rule.
  - Expected handling: catalog validation must reject all URLs outside `configs/corpus.yaml`.
- README later contradicts architecture.
  - Expected handling: update README to match fixed Groww corpus before implementation is considered complete.
- Handoff becomes stale.
  - Expected handling: update `docs/handoff.md` after any meaningful architecture, source, or implementation change.

## Checks

- `docs/architecture.md` includes the fixed corpus table.
- `configs/corpus.yaml` contains exactly five sources.
- `docs/handoff.md` says no other URLs are allowed.

