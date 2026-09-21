"""
FinFit agent bench cases (no live LLM).

Each case defines:
- profile: fields to set on UserState before the turn
- query: user message
- expect_tools: tools that MUST appear at least once
- forbid_tools: tools that must NOT appear
- expect_tool_args: [{tool, args_contains: {k: v}}] — at least one matching call
- forbid_tool_args: [{tool, args_contains: {k: v}}] — no call may match
- expect_assumption_fields: assumption field names that must be recorded
- forbid_assumption_fields: must not be assumed (profile already known)
"""

BENCH_CASES = [
    {
        "id": "benefit_only_empty_profile",
        "profile": {},
        "query": "받을 수 있는 청년 혜택 알려줘",
        "expect_tools": ["check_benefit_eligibility"],
        "forbid_tools": ["get_gunsan_youth_stats"],
        "expect_assumption_fields": ["age", "income_level"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
        "forbid_internal_kinds": ["structure_findings", "cross_verify"],
    },
    {
        "id": "benefit_only_full_profile",
        "profile": {
            "age": 26,
            "income_level": "100%이하",
            "employment_status": "미취업",
            "has_house": False,
            "first_goal": "비상금",
        },
        "query": "내 조건으로 혜택 자격 확인해줘",
        "expect_tools": ["check_benefit_eligibility"],
        "forbid_tools": ["get_gunsan_youth_stats"],
        "forbid_assumption_fields": ["age", "income_level", "employment_status", "has_house"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
        "forbid_internal_kinds": ["cross_verify"],
    },
    {
        "id": "benefit_with_income_no_auto_savings",
        "profile": {
            "age": 26,
            "income_level": "100%이하",
            "employment_status": "미취업",
            "has_house": False,
            "monthly_income": 2500000,
            "first_goal": None,
        },
        "query": "받을 수 있는 청년 혜택 알려줘",
        "expect_tools": ["check_benefit_eligibility"],
        "forbid_tools": ["calculate_savings_plan", "get_gunsan_youth_stats"],
        "forbid_assumption_fields": ["age", "monthly_income"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "savings_only_with_income",
        "profile": {"monthly_income": 2400000, "first_goal": None},
        "query": "월급 기준으로 저축 계획 세워줘",
        "expect_tools": ["calculate_savings_plan"],
        "forbid_tools": ["get_gunsan_youth_stats"],
        "forbid_assumption_fields": ["monthly_income"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
        "forbid_internal_kinds": ["structure_findings", "cross_verify"],
    },
    {
        "id": "savings_only_no_income",
        "profile": {"first_goal": None},
        "query": "생활비 아끼고 저축하려면 얼마가 적당해?",
        "expect_tools": ["calculate_savings_plan"],
        "forbid_tools": ["get_gunsan_youth_stats"],
        "expect_assumption_fields": ["monthly_income"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "gunsan_stats_only",
        "profile": {"first_goal": None},
        "query": "군산시 청년 인구 현황 어때?",
        "expect_tools": ["get_gunsan_youth_stats"],
        "forbid_tools": ["check_benefit_eligibility", "calculate_savings_plan"],
        "expect_tool_args": [
            {"tool": "get_gunsan_youth_stats", "args_contains": {"category": "population"}},
        ],
        "forbid_tool_args": [
            {"tool": "get_gunsan_youth_stats", "args_contains": {"category": "employment"}},
            {
                "tool": "get_gunsan_youth_stats",
                "args_contains": {"category": "employment_count"},
            },
        ],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
        "forbid_internal_kinds": ["structure_findings", "cross_verify", "assess_coverage"],
    },
    {
        "id": "employment_stats",
        "profile": {"first_goal": None},
        "query": "군산 청년 취업 상황 알려줘",
        "expect_tools": ["get_gunsan_youth_stats"],
        "forbid_tools": ["calculate_savings_plan"],
        # generic 취업 → 군산 어려움% (employment_difficulty), not raw employment_count
        "expect_tool_args": [
            {
                "tool": "get_gunsan_youth_stats",
                "args_contains": {"category": "employment_difficulty"},
            },
        ],
        "forbid_tool_args": [
            {
                "tool": "get_gunsan_youth_stats",
                "args_contains": {"category": "employment_count"},
            },
            {"tool": "get_gunsan_youth_stats", "args_contains": {"category": "population"}},
        ],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "employment_count_stats",
        "profile": {"first_goal": None},
        "query": "전북 청년 취업자 수 통계 알려줘",
        "expect_tools": ["get_gunsan_youth_stats"],
        "forbid_tools": ["calculate_savings_plan"],
        "expect_tool_args": [
            {
                "tool": "get_gunsan_youth_stats",
                "args_contains": {"category": "employment_count"},
            },
        ],
        "forbid_tool_args": [
            {
                "tool": "get_gunsan_youth_stats",
                "args_contains": {"category": "employment_difficulty"},
            },
            {"tool": "get_gunsan_youth_stats", "args_contains": {"category": "housing"}},
        ],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "employment_difficulty_stats",
        "profile": {"first_goal": None},
        "query": "군산 취업 어려움 원인이 뭐야?",
        "expect_tools": ["get_gunsan_youth_stats"],
        "expect_tool_args": [
            {
                "tool": "get_gunsan_youth_stats",
                "args_contains": {"category": "employment_difficulty"},
            },
        ],
        "forbid_tool_args": [
            {
                "tool": "get_gunsan_youth_stats",
                "args_contains": {"category": "employment_count"},
            },
        ],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "housing_stats",
        "profile": {"first_goal": None},
        "query": "군산 청년 주택 소유율 통계 있어?",
        "expect_tools": ["get_gunsan_youth_stats"],
        "forbid_tools": ["calculate_savings_plan"],
        "expect_tool_args": [
            {"tool": "get_gunsan_youth_stats", "args_contains": {"category": "housing"}},
        ],
        "forbid_tool_args": [
            {
                "tool": "get_gunsan_youth_stats",
                "args_contains": {"category": "employment_difficulty"},
            },
        ],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "income_stats",
        "profile": {"first_goal": None},
        "query": "군산 청년 임금 분포 통계 알려줘",
        "expect_tools": ["get_gunsan_youth_stats"],
        "forbid_tools": ["calculate_savings_plan", "check_benefit_eligibility"],
        "expect_tool_args": [
            {"tool": "get_gunsan_youth_stats", "args_contains": {"category": "income"}},
        ],
        "forbid_tool_args": [
            {"tool": "get_gunsan_youth_stats", "args_contains": {"category": "population"}},
            {
                "tool": "get_gunsan_youth_stats",
                "args_contains": {"category": "employment_count"},
            },
        ],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "benefit_and_savings",
        "profile": {
            "age": 27,
            "income_level": "140%이하",
            "employment_status": "취업자",
            "has_house": False,
            "monthly_income": 2500000,
            "first_goal": None,
        },
        "query": "혜택이랑 저축 계획 같이 알려줘",
        "expect_tools": ["check_benefit_eligibility", "calculate_savings_plan"],
        "forbid_tools": ["get_gunsan_youth_stats"],
        "forbid_assumption_fields": ["age", "monthly_income"],
        "expect_depth": "standard",
        "expect_max_internals": 2,
        "forbid_internal_kinds": ["cross_verify"],
    },
    {
        "id": "complex_three_pillars",
        "profile": {
            "age": 25,
            "income_level": "100%이하",
            "employment_status": "미취업",
            "has_house": False,
            "monthly_income": 2000000,
            "first_goal": None,
        },
        "query": "군산 거주 취준생인데 혜택, 저축, 지역 현황 다 알려줘",
        "expect_tools": [
            "check_benefit_eligibility",
            "calculate_savings_plan",
            "get_gunsan_youth_stats",
        ],
        # 취준생 → employment_difficulty (not bare population)
        "expect_tool_args": [
            {
                "tool": "get_gunsan_youth_stats",
                "args_contains": {"category": "employment_difficulty"},
            },
        ],
        "forbid_assumption_fields": ["age", "income_level", "monthly_income"],
        "expect_depth": "deep",
        "expect_max_internals": 4,
    },
    {
        "id": "doyak_keyword_benefit",
        "profile": {"first_goal": None},
        "query": "청년도약계좌 자격 되나?",
        "expect_tools": ["check_benefit_eligibility"],
        "forbid_tools": ["get_gunsan_youth_stats"],
        "expect_assumption_fields": ["age"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "jeonse_keyword",
        "profile": {"first_goal": None, "has_house": False, "monthly_income": None},
        "query": "전세 보증 관련 지원 있어?",
        "expect_tools": ["check_benefit_eligibility"],
        "forbid_tools": ["get_gunsan_youth_stats"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "wolse_benefit_no_stats",
        "profile": {"first_goal": None, "monthly_income": None},
        "query": "청년 월세 지원 혜택 알려줘",
        "expect_tools": ["check_benefit_eligibility"],
        "forbid_tools": ["get_gunsan_youth_stats"],
        "expect_assumption_fields": ["age"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "gunsan_benefit_no_bare_stats",
        "profile": {"first_goal": None, "monthly_income": None},
        "query": "군산 거주인데 받을 수 있는 혜택 뭐 있어?",
        "expect_tools": ["check_benefit_eligibility"],
        "forbid_tools": ["get_gunsan_youth_stats"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "jeonse_stats_not_benefit",
        "profile": {"first_goal": None, "monthly_income": None},
        "query": "전세 통계 있어?",
        "expect_tools": ["get_gunsan_youth_stats"],
        "forbid_tools": ["check_benefit_eligibility"],
        "expect_tool_args": [
            {"tool": "get_gunsan_youth_stats", "args_contains": {"category": "housing"}},
        ],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "first_goal_triggers_benefit",
        "profile": {
            "first_goal": "노트북",
            "age": 24,
            "income_level": "100%이하",
            "employment_status": "취업자",
            "has_house": False,
            "monthly_income": 2000000,
        },
        "query": "뭐부터 하면 좋을까?",
        "expect_tools": ["check_benefit_eligibility"],
        "forbid_tools": ["calculate_savings_plan", "get_gunsan_youth_stats"],
        "forbid_assumption_fields": ["age"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "first_goal_pure_savings_no_benefit",
        "profile": {
            "first_goal": "노트북",
            "age": 24,
            "monthly_income": 2000000,
            "income_level": "100%이하",
            "employment_status": "취업자",
            "has_house": False,
        },
        "query": "저축 계획만 간단히",
        "expect_tools": ["calculate_savings_plan"],
        "forbid_tools": ["check_benefit_eligibility", "get_gunsan_youth_stats"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "budget_keyword_savings",
        "profile": {"monthly_income": 2100000, "first_goal": None},
        "query": "예산 어떻게 나누면 돼?",
        "expect_tools": ["calculate_savings_plan"],
        "forbid_tools": ["get_gunsan_youth_stats"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "synthesize_always",
        "profile": {"age": 30, "income_level": "100%이하", "employment_status": "취업자",
                    "has_house": True, "monthly_income": 3000000, "first_goal": None},
        "query": "저축 계획만 간단히",
        "expect_tools": ["calculate_savings_plan"],
        "must_synthesize": True,
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
    {
        "id": "unclear_intent_no_tools",
        "profile": {"first_goal": None, "monthly_income": None},
        "query": "돈 관리 어떻게 해",
        "expect_tools": [],
        "forbid_tools": [
            "check_benefit_eligibility",
            "calculate_savings_plan",
            "get_gunsan_youth_stats",
        ],
        "must_synthesize": True,
        "expect_depth": "shallow",
        # clarify_intent then synthesize (prepare optional)
        "expect_max_internals": 2,
    },
    {
        "id": "bare_salary_clarifies_not_savings",
        "profile": {"first_goal": None, "monthly_income": None},
        "query": "월급 얼마야",
        "expect_tools": [],
        "forbid_tools": [
            "calculate_savings_plan",
            "get_gunsan_youth_stats",
            "check_benefit_eligibility",
        ],
        "must_synthesize": True,
        "expect_depth": "shallow",
        "expect_max_internals": 2,
    },
    {
        "id": "gunsan_job_benefit_no_stats",
        "profile": {"first_goal": None, "monthly_income": None},
        "query": "군산 취업 지원 혜택",
        "expect_tools": ["check_benefit_eligibility"],
        "forbid_tools": ["get_gunsan_youth_stats", "calculate_savings_plan"],
        "expect_depth": "shallow",
        "expect_max_internals": 1,
    },
]
