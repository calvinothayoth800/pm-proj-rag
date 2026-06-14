# Phase 1 Edge Cases: Corpus Definition

Purpose: keep the project locked to the selected five Groww pages.

## Edge Cases

- A source URL differs by trailing slash, query string, UTM tag, casing, or redirect.
  - Expected handling: reject it unless the normalized URL exactly matches one of the five configured URLs.
- A Groww page links to factsheets, AMC pages, SEBI pages, AMFI pages, or related schemes.
  - Expected handling: do not crawl or ingest linked pages.
- A selected Groww page is unavailable, rate-limited, or returns a client-side shell.
  - Expected handling: record fetch failure and do not substitute another source.
- Groww updates page layout or field labels.
  - Expected handling: ingestion should fail loudly for missing expected fields instead of silently producing weak chunks.
- A scheme is renamed on Groww.
  - Expected handling: keep the configured URL as the source ID; update title only after manual review.
- The same factual value appears with different labels on the same page.
  - Expected handling: preserve section metadata so retrieval can disambiguate.

## Checks

- Exactly five schemes are configured.
- Exactly five sources are configured.
- Every source has `allowed: true`, `scheme_id`, `type`, and `last_checked`.
- No source URL outside `https://groww.in/mutual-funds/...` is present.

