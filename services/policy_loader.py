from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Policy


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = ROOT / "data" / "policies.json"

REQUIRED_FIELDS = {
    "schema_version",
    "id",
    "name",
    "category",
    "source",
    "benefit",
    "updated_at",
    "keywords",
    "eligibility",
}

REQUIRED_ELIGIBILITY_FIELDS = {
    "age_min",
    "age_max",
    "employment_status",
    "regions",
    "housing_required",
    "median_income_percent_max",
    "annual_income_limit_million_krw",
}


def validate_policy_record(record: dict[str, Any]) -> None:
    missing = REQUIRED_FIELDS - set(record)
    if missing:
        raise ValueError(f"policy {record.get('id', '<unknown>')} is missing fields: {sorted(missing)}")

    eligibility = record.get("eligibility")
    if not isinstance(eligibility, dict):
        raise ValueError(f"policy {record['id']} eligibility must be an object")

    missing_eligibility = REQUIRED_ELIGIBILITY_FIELDS - set(eligibility)
    if missing_eligibility:
        raise ValueError(
            f"policy {record['id']} eligibility is missing fields: {sorted(missing_eligibility)}"
        )

    if record["schema_version"] != "1.0":
        raise ValueError(f"unsupported policy schema version: {record['schema_version']}")


def load_policy_records(path: str | Path | None = None) -> list[dict[str, Any]]:
    policy_path = Path(path) if path is not None else DEFAULT_POLICY_PATH
    with policy_path.open("r", encoding="utf-8") as f:
        records = json.load(f)

    if not isinstance(records, list):
        raise ValueError("policies.json must contain a list of policy records")

    for record in records:
        validate_policy_record(record)
    return records


def load_policies(path: str | Path | None = None) -> list[Policy]:
    return [Policy.from_dict(record) for record in load_policy_records(path)]
