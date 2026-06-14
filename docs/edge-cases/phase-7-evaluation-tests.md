# Phase 7 Edge Cases: Evaluation And Tests

Purpose: verify factuality, source discipline, and refusal behavior.

## Edge Cases

- Tests accidentally use URLs outside the five-source corpus.
  - Expected handling: fail the test fixture or catalog validation.
- Snapshot tests become brittle when answer wording changes.
  - Expected handling: assert contract-level behavior: source, footer, refusal class, and factual value.
- Retrieval tests pass because of hardcoded answers.
  - Expected handling: verify retrieved chunk metadata and source URL.
- Compliance tests miss paraphrased advice requests.
  - Expected handling: include varied phrasings for investment advice, comparisons, returns, and projections.
- Sentence counting fails on abbreviations or decimals.
  - Expected handling: use a conservative sentence validator and include decimal-heavy examples.
- Tests log sensitive sample values.
  - Expected handling: use fake placeholders and ensure redaction in logs.
- Stale indexes make tests pass against old corpus data.
  - Expected handling: tests should rebuild or verify index build metadata.

## Checks

- Factual queries pass with exactly one Groww URL.
- Advisory/comparison queries refuse.
- Out-of-corpus queries refuse or return not-found.
- Sensitive-data queries refuse without echoing sensitive strings.
- Footer date matches source metadata.

