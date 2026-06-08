# Target Architecture

The cleanup turns FinFit into an operating MVP with clear boundaries.

## Target Structure

```text
app.py
pages/
services/
    models.py
    policy_loader.py
    recommendation.py
data/
    policies.json
tests/
assets/
docs/
    CURRENT_ARCHITECTURE.md
    TARGET_ARCHITECTURE.md
    FEATURE_FREEZE_v1.md
    adr/
.github/workflows/test.yml
```

## Data Flow

```text
User input
  -> UserProfile
  -> match_policies(profile, policies)
  -> PolicyMatch results
  -> Streamlit rendering
```

## Operating Evidence

The youth update page shows:

- Last sync time
- Data freshness
- Item count
- API status
- Cache status
- Fallback usage

## Design Principle

Policy conditions are data. UI pages render forms and results, but do not own eligibility rules.
