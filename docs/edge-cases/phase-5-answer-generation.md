# Phase 5 Edge Cases: Answer Generation

Purpose: produce short, grounded, source-backed answers without leaking unsupported claims.

## Edge Cases

- Retrieved evidence is weak or missing.
  - Expected handling: say the information was not found in the fixed Groww corpus.
- Retrieved evidence has a value but no clear scheme name.
  - Expected handling: do not answer unless the source metadata identifies the scheme.
- Answer would need more than 3 sentences.
  - Expected handling: prioritize the direct fact, one source link, and footer.
- Generator tries to include two links.
  - Expected handling: formatter/validator rejects and rewrites to exactly one source link.
- Generator uses advisory language such as "suitable", "recommended", or "better".
  - Expected handling: post-answer validator rejects.
- Source freshness date is missing.
  - Expected handling: use `last_checked` from source metadata; if missing, validation fails.
- User asks for performance.
  - Expected handling: do not calculate or summarize; point to the relevant Groww page only.
- User asks for "why" behind a value.
  - Expected handling: answer only if the Groww text explicitly explains it.

## Checks

- Response has no more than 3 answer sentences.
- Response includes exactly one of the five Groww URLs.
- Response ends with `Last updated from sources: <YYYY-MM-DD>`.
- Response text contains no recommendation or advice terms.

