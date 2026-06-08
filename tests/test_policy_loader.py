from services.policy_loader import load_policies, load_policy_records


def test_load_policies_has_schema_version():
    policies = load_policies()
    assert policies
    assert {policy.schema_version for policy in policies} == {"1.0"}


def test_policy_records_include_required_eligibility_fields():
    records = load_policy_records()
    for record in records:
        eligibility = record["eligibility"]
        assert "age_min" in eligibility
        assert "age_max" in eligibility
        assert "employment_status" in eligibility
        assert "regions" in eligibility
        assert "housing_required" in eligibility
        assert "median_income_percent_max" in eligibility
        assert "annual_income_limit_million_krw" in eligibility
