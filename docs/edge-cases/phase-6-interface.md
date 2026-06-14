# Phase 6 Edge Cases: Minimal Interface

Purpose: keep the UI simple, clear, and compliant.

## Edge Cases

- User pastes sensitive data into the question box.
  - Expected handling: client should avoid persisting it; server compliance must still reject it.
- User submits an empty or whitespace-only question.
  - Expected handling: show a short validation message.
- User submits an extremely long question.
  - Expected handling: enforce a reasonable character limit and ask for a shorter factual question.
- User clicks example questions before corpus/index is built.
  - Expected handling: show a clear unavailable or setup-needed state.
- Disclaimer is hidden on mobile.
  - Expected handling: keep `Facts-only. No investment advice.` visible in all supported layouts.
- Answer contains a long URL that breaks layout.
  - Expected handling: render as a link with wrapping or compact display text.
- Loading, error, and refusal states look the same.
  - Expected handling: separate states visually and textually without adding extra policy explanation clutter.

## Checks

- Welcome message exists.
- Three example questions exist.
- Disclaimer is always visible.
- No UI field asks for PAN, Aadhaar, account number, OTP, email, or phone number.

