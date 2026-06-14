# Phase 2 Edge Cases: Ingestion Pipeline

Purpose: fetch and process only the fixed Groww pages without silently corrupting evidence.

## Edge Cases

- Fetcher receives an unapproved URL.
  - Expected handling: block before network access and return a clear allowlist error.
- Groww blocks automated requests or returns CAPTCHA-like content.
  - Expected handling: mark source as failed; do not ingest the blocked response as factual content.
- Page content is rendered by JavaScript and static HTML lacks facts.
  - Expected handling: parser should detect low-content extraction and fail with diagnostics.
- Duplicate chunks are produced from repeated page sections.
  - Expected handling: deduplicate by normalized text plus source URL.
- Numeric values are extracted without their labels or units.
  - Expected handling: keep nearby label/context in the same chunk.
- Dates on the page are missing or ambiguous.
  - Expected handling: use `last_checked` from `configs/corpus.yaml` for the response footer.
- Parser accidentally captures nav, ads, unrelated links, or legal boilerplate.
  - Expected handling: filter obvious non-answer sections while preserving source traceability.
- Ingestion output from an old run remains after a failed new run.
  - Expected handling: write run metadata and avoid mixing stale and fresh chunks.

## Checks

- Each chunk has `source_url`, `source_title`, `scheme_id`, `category`, and `last_checked`.
- Failed sources are visible in logs or run reports.
- No chunk references a URL outside the five-source catalog.

