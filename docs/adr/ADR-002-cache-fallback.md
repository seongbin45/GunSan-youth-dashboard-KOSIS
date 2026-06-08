# ADR-002: Show API Cache Fallback State

## Decision

The youth benefit update page shows API status, cache status, data freshness, and fallback usage.

## Reason

Public APIs can fail, slow down, or return incomplete data. The MVP should prove that FinFit can still show the latest cached snapshot when upstream data is unavailable.

## Consequence

`YouthDataService` records sync status and exposes source status for the Streamlit dashboard.
