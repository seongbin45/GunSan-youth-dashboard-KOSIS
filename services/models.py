from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Eligibility:
    age_min: int | None = None
    age_max: int | None = None
    employment_status: list[str] = field(default_factory=list)
    regions: list[str] = field(default_factory=list)
    housing_required: bool | None = None
    requires_no_house: bool | None = None
    median_income_percent_max: int | None = None
    annual_income_limit_million_krw: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Eligibility":
        return cls(
            age_min=data.get("age_min"),
            age_max=data.get("age_max"),
            employment_status=list(data.get("employment_status") or []),
            regions=list(data.get("regions") or []),
            housing_required=data.get("housing_required"),
            requires_no_house=data.get("requires_no_house"),
            median_income_percent_max=data.get("median_income_percent_max"),
            annual_income_limit_million_krw=data.get("annual_income_limit_million_krw"),
        )


@dataclass(frozen=True)
class Policy:
    schema_version: str
    id: str
    name: str
    category: str
    source: str
    benefit: str
    url: str
    updated_at: str
    keywords: list[str]
    eligibility: Eligibility

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Policy":
        return cls(
            schema_version=str(data["schema_version"]),
            id=str(data["id"]),
            name=str(data["name"]),
            category=str(data["category"]),
            source=str(data["source"]),
            benefit=str(data["benefit"]),
            url=str(data.get("url") or ""),
            updated_at=str(data["updated_at"]),
            keywords=list(data.get("keywords") or []),
            eligibility=Eligibility.from_dict(data["eligibility"]),
        )


@dataclass(frozen=True)
class UserProfile:
    age: int
    employment_status: str
    has_house: bool
    region: str = "전국"
    median_income_percent: int | None = None
    annual_income_million_krw: int | None = None
    keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PolicyMatch:
    policy: Policy
    score: int
    reasons: list[str]
