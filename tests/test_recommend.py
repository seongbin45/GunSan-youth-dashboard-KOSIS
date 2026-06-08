from services.models import UserProfile
from services.policy_loader import load_policies
from services.recommendation import match_policies


def test_job_seeker_gets_employment_support():
    profile = UserProfile(
        age=25,
        employment_status="job_seeker",
        has_house=False,
        region="군산시",
        median_income_percent=100,
        keywords=["취업"],
    )

    names = {match.policy.name for match in match_policies(profile, load_policies())}

    assert "국민취업지원제도 1유형" in names
    assert "전북형 청년활력수당" in names


def test_home_owner_does_not_get_no_house_policy():
    profile = UserProfile(
        age=25,
        employment_status="student",
        has_house=True,
        region="전국",
        median_income_percent=60,
        keywords=["주거"],
    )

    names = {match.policy.name for match in match_policies(profile, load_policies())}

    assert "청년월세 한시 특별지원" not in names


def test_worker_in_gunsan_gets_regional_savings_policy():
    profile = UserProfile(
        age=28,
        employment_status="worker",
        has_house=False,
        region="군산시",
        median_income_percent=100,
        keywords=["저축"],
    )

    names = {match.policy.name for match in match_policies(profile, load_policies())}

    assert "전북청년 함께 두배적금" in names
