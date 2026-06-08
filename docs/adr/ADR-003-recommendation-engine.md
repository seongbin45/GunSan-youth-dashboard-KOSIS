# ADR-003: Keep Recommendation Logic Outside UI

## Decision

Recommendation logic lives in `services/recommendation.py`. Streamlit pages create a `UserProfile` and render `PolicyMatch` results.

## Reason

- UI changes should not break policy matching.
- Recommendation behavior can be tested without running Streamlit.
- The same matching service can be reused by the AI page or future APIs.

## Consequence

UI pages should call `matches = match_policies(profile, policies)` and should not contain policy eligibility branches.
