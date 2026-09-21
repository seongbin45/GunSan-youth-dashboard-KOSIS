"""
Rule-based intent routing for FinFitAgent.plan / demo / critique.

Single module so agent.py stays orchestration-only.
Behavior must stay locked by tests/intent_golden.jsonl — change routing here,
then update golden with an explicit product decision.
"""
from __future__ import annotations

from typing import Optional


def wants_stats_query(user_message: str) -> bool:
    """
    Whether the user message asks for Gunsan/KOSIS-style stats tools.

    Precision rules (benefit vs stats):
    - bare 월급/계산 → not savings, not stats (clarify or wait for clearer words)
    - 전세/월세/주택 + 지원/혜택/자격 → benefit, NOT stats (unless 통계/비율/소유율)
    - bare 군산 + 혜택 → benefit only
    - 군산 + 취업/일자리 + 지원/혜택 (no 통계·현황·상황) → benefit only, NOT stats
    """
    q = (user_message or "").lower()
    benefitish = any(k in q for k in ("혜택", "지원", "자격", "지원금"))
    stats_explicit = any(
        k in q for k in ("통계", "현황", "비율", "분포", "비중", "데이터", "상황", "어때", "원인")
    )

    # Explicit stats / survey wording
    if any(k in q for k in ("통계", "현황", "비율", "분포", "비중", "데이터")):
        return True

    # Population / ownership always data-like
    if any(k in q for k in ("인구", "소유율", "소유 비율")):
        return True

    # Employment volume
    if any(k in q for k in ("취업자 수", "취업자수", "일자리 수", "고용 규모")):
        return True

    # Job difficulty / situation (not pure 혜택/지원)
    if any(k in q for k in ("취업 어려움", "구직난", "미스매치", "취업 상황", "취업현황", "일자리 상황")):
        return True
    if ("취업" in q or "일자리" in q) and any(k in q for k in ("어때", "알려", "상황", "원인")):
        if not benefitish:
            return True

    # Housing as data (not 월세/전세 지원 혜택)
    if any(k in q for k in ("주택", "월세", "전세")) and any(
        k in q for k in ("통계", "현황", "비율", "소유", "분포")
    ):
        return True

    # Wage bands
    if any(k in q for k in ("임금", "소득 분포", "임금 분포", "월평균 임금")):
        return True
    if "소득" in q and any(k in q for k in ("통계", "현황", "분포", "구간")):
        return True

    # 군산 + topic: benefit phrasing without stats wording must not pull KOSIS
    if "군산" in q:
        pure_geo = any(k in q for k in ("통계", "현황", "인구", "데이터", "임금"))
        house_topic = "주택" in q or "월세" in q or "전세" in q
        job_topic = any(k in q for k in ("취업", "일자리"))
        if pure_geo:
            return True
        if house_topic:
            # "군산 주택 지원 혜택" → benefit only; "군산 주택 현황/소유율" → stats
            if benefitish and not stats_explicit and "소유" not in q:
                return False
            return True
        if job_topic:
            if benefitish and not stats_explicit:
                return False
            return True

    return False


def stats_category_for_query(user_message: str) -> str:
    """
    Map question → get_gunsan_youth_stats category.
    Single source for plan / critique refine / insufficient fallback.
    """
    q = (user_message or "").lower()
    if any(x in q for x in ["주택", "월세", "전세", "소유율", "소유 비율"]):
        return "housing"
    if any(x in q for x in ["임금", "소득 분포", "임금 분포", "월평균 임금"]) or (
        "소득" in q and any(k in q for k in ["통계", "현황", "분포", "구간"])
    ):
        return "income"
    if any(x in q for x in ["어려움", "구직난", "미스매치", "취업 원인"]):
        return "employment_difficulty"
    if any(x in q for x in ["취업자 수", "취업자수", "일자리 수", "고용 규모"]):
        return "employment_count"
    if "취업" in q or "일자리" in q or "취준" in q:
        return "employment_difficulty"
    if "인구" in q:
        return "population"
    return "population"


def wants_savings_query(user_message: str) -> bool:
    """
    Explicit savings/budget intent only (not implied by monthly_income).

    Precision: bare 「월급」「계산」 alone is too broad
    (e.g. '월급 얼마야', '계산 좀' must NOT open savings tool).
    """
    q = (user_message or "").lower()
    if any(k in q for k in ("저축", "예산", "생활비", "절약", "가계부")):
        return True
    # 모으기 / 적립 의도 (e.g. "돈 어떻게 모아야할까", "모을까")
    if any(k in q for k in ("모아", "모으", "모을", "적립", "비상금")):
        return True
    # 월급 only with budget/plan companion words
    if "월급" in q and any(
        k in q for k in ("저축", "예산", "계획", "나누", "관리", "아끼", "생활비", "모아", "모으")
    ):
        return True
    # 계산 only with financial plan context
    if "계산" in q and any(
        k in q for k in ("저축", "예산", "생활비", "월급", "절약", "가계부", "계획")
    ):
        return True
    return False


def wants_benefit_query(user_message: str, first_goal: Optional[str] = None) -> bool:
    """
    Benefit/eligibility intent.

    - Explicit keywords → True
    - first_goal alone → True only for open-ended turns (no competing savings/stats intent)
      so "뭐부터 하면 좋을까?" still triggers benefits, but pure 저축/통계 does not.
    """
    q = (user_message or "").lower()
    if any(k in q for k in ("혜택", "지원", "자격", "도약", "적금", "대출")):
        return True
    if first_goal and not wants_savings_query(user_message) and not wants_stats_query(user_message):
        return True
    return False


# Shown when no pillar tools are planned (avoid empty silent synthesis)
CLARIFY_INTENT_TEXT = (
    "질문이 여러 방향으로 해석될 수 있어요. 원하시는 항목을 골라 주세요.\n"
    "1) **청년 혜택·지원 자격** (예: 받을 수 있는 혜택, 월세 지원)\n"
    "2) **저축·예산 계획** (예: 월급 저축 계획, 예산 나누기)\n"
    "3) **군산 청년 통계** (예: 인구 현황, 취업 상황, 주택 소유율, 임금 분포)\n"
    "한 줄로 다시 말씀해 주시면 맞춰 도구로 조회해 드릴게요."
)


def is_unclear_intent(user_message: str, first_goal: Optional[str] = None) -> bool:
    """True when no benefit/savings/stats pillar is detected (and not empty-only noise optional)."""
    msg = (user_message or "").strip()
    if not msg:
        return True
    if wants_benefit_query(msg, first_goal):
        return False
    if wants_savings_query(msg):
        return False
    if wants_stats_query(msg):
        return False
    return True
