from __future__ import annotations

from .models import Policy, PolicyMatch, UserProfile
from .policy_loader import load_policies


def _region_matches(user_region: str, policy_regions: list[str]) -> bool:
    if not policy_regions or "전국" in policy_regions:
        return True
    return user_region in policy_regions or any(region in user_region for region in policy_regions)


def _income_matches(profile: UserProfile, policy: Policy) -> bool:
    eligibility = policy.eligibility

    if eligibility.median_income_percent_max is not None and profile.median_income_percent is not None:
        if profile.median_income_percent > eligibility.median_income_percent_max:
            return False

    if (
        eligibility.annual_income_limit_million_krw is not None
        and profile.annual_income_million_krw is not None
    ):
        if profile.annual_income_million_krw > eligibility.annual_income_limit_million_krw:
            return False

    return True


def _match_policy(profile: UserProfile, policy: Policy) -> PolicyMatch | None:
    eligibility = policy.eligibility
    reasons: list[str] = []
    score = 0

    if eligibility.age_min is not None and profile.age < eligibility.age_min:
        return None
    if eligibility.age_max is not None and profile.age > eligibility.age_max:
        return None
    if eligibility.age_min is not None or eligibility.age_max is not None:
        reasons.append("연령 조건 충족")
        score += 30

    if eligibility.employment_status and profile.employment_status not in eligibility.employment_status:
        return None
    if eligibility.employment_status:
        reasons.append("고용/상태 조건 충족")
        score += 20

    if eligibility.requires_no_house is True and profile.has_house:
        return None
    if eligibility.requires_no_house is True:
        reasons.append("무주택 조건 충족")
        score += 20

    if eligibility.housing_required is True and not profile.has_house:
        return None

    if not _region_matches(profile.region, eligibility.regions):
        return None
    if eligibility.regions:
        reasons.append("지역 조건 충족")
        score += 10

    if not _income_matches(profile, policy):
        return None
    if eligibility.median_income_percent_max or eligibility.annual_income_limit_million_krw:
        reasons.append("소득 조건 충족 또는 확인 필요")
        score += 20

    keyword_hits = sorted(set(profile.keywords) & set(policy.keywords))
    if keyword_hits:
        reasons.append(f"관심 키워드 일치: {', '.join(keyword_hits)}")
        score += 5 * len(keyword_hits)

    if not reasons:
        reasons.append("기본 조건 확인 필요")

    return PolicyMatch(policy=policy, score=score, reasons=reasons)


def match_policies(profile: UserProfile, policies: list[Policy] | None = None) -> list[PolicyMatch]:
    source_policies = policies if policies is not None else load_policies()
    matches = [match for policy in source_policies if (match := _match_policy(profile, policy))]
    return sorted(matches, key=lambda match: (-match.score, match.policy.category, match.policy.name))
