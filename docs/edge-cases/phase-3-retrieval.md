# Phase 3 Edge Cases: Retrieval Layer

Purpose: retrieve the right Groww evidence without inventing or over-broadly matching facts.

## Edge Cases

- User asks about one HDFC scheme but uses a partial or informal name.
  - Expected handling: match against configured scheme aliases only when confidence is high.
- Query mentions two schemes.
  - Expected handling: refuse comparison/advice if the intent is comparative; otherwise ask for one scheme.
- Query asks for a field not present in the fixed corpus.
  - Expected handling: return insufficient-information response with one relevant Groww source link.
- Retrieval returns chunks from the wrong scheme due to shared HDFC terms.
  - Expected handling: scheme match should outrank generic text matches.
- Query asks about "best", "better", "returns", or "should I".
  - Expected handling: compliance should catch before retrieval or prevent final answer after retrieval.
- Multiple chunks from the same page disagree because of stale or duplicated content.
  - Expected handling: prefer the most specific section and avoid merging conflicting values.
- Embedding search retrieves semantically similar but unsupported facts.
  - Expected handling: final answer must only use explicit evidence from retrieved text.

## Checks

- Retrieval result includes score, source URL, scheme ID, and chunk text.
- Top result for a scheme-specific query belongs to the requested scheme.
- Retrieval never returns evidence from outside `configs/corpus.yaml`.

