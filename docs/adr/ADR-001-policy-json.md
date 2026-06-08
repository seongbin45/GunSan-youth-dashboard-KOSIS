# ADR-001: Manage Policy Conditions As JSON

## Decision

Policy conditions are stored in `data/policies.json` instead of being embedded in Streamlit UI files.

## Reason

- Policies change often.
- JSON is easier to update and test than scattered `if` statements.
- The same data can later move to SQLite, Supabase, or a public API without changing the UI contract.

## Consequence

All recommendation logic must load policies through `services.policy_loader`.
