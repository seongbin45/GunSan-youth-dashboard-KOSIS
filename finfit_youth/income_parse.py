"""
Parse profile facts stated in Korean user messages.

- Income: so savings tool prefers 「월급 230만원」 over stale profile.
- Age: so benefits tool prefers 「25세」 over default/stale profile age.
"""
from __future__ import annotations

import re
from typing import Optional


def parse_age_years(text: str | None) -> Optional[int]:
    """
    Extract age in full years from free text, or None.

    Supported: 25세, 25살, 만 25세, 나이 25세
    Range: 15–45 (youth product scope; avoids random two-digit matches).
    """
    if not text:
        return None
    s = str(text)
    patterns = (
        r"만\s*(\d{1,2})\s*세",
        r"나이\s*(\d{1,2})\s*세",
        r"(\d{1,2})\s*세",
        r"(\d{1,2})\s*살",
    )
    for pat in patterns:
        m = re.search(pat, s)
        if not m:
            continue
        age = int(m.group(1))
        if 15 <= age <= 45:
            return age
    return None


def parse_employment_status(text: str | None) -> Optional[str]:
    """
    Map free-text employment to tool enum values, or None.

    Enum: 미취업 | 취업자 | 창업자 | 농업종사자
    """
    if not text:
        return None
    q = str(text)
    # more specific first
    if any(k in q for k in ("창업", "사업자", "자영업")):
        return "창업자"
    if any(k in q for k in ("농업", "농민", "귀농")):
        return "농업종사자"
    if any(
        k in q
        for k in (
            "취준",
            "미취업",
            "구직",
            "실업",
            "백수",
            "취업준비",
            "구직자",
        )
    ):
        return "미취업"
    if any(k in q for k in ("재직", "직장", "취업자", "근로자", "회사원", "직장인")):
        # bare "취업" alone is ambiguous (취업 지원); require stronger tokens
        return "취업자"
    if "취업" in q and any(k in q for k in ("중", "했", "완료", "함", "상태")):
        return "취업자"
    return None


def parse_has_house(text: str | None) -> Optional[bool]:
    """True=유주택, False=무주택, None=unknown."""
    if not text:
        return None
    q = str(text)
    if any(k in q for k in ("무주택", "주택 없음", "집 없음", "자가 없음", "전세만", "월세만")):
        return False
    if any(k in q for k in ("유주택", "자가 보유", "주택 소유", "집 있음", "주택 있음")):
        return True
    # "무주택" already covered; bare "주택" is not enough
    return None


def parse_monthly_income_won(text: str | None) -> Optional[int]:
    """
    Extract a monthly income in KRW from free text, or None.

    Supported (examples):
      - 230만원 / 230 만원 / 230만
      - 2,300,000원 / 2300000원
      - 250만 원
    Prefers the first plausible match. Ignores tiny numbers (< 10만) unless explicit 원.
    """
    if not text:
        return None
    s = str(text).replace(" ", "")
    s = s.replace(",", "")

    # 1) N만원 / N만
    m = re.search(r"(\d+(?:\.\d+)?)\s*만\s*원?", s)
    if m:
        man = float(m.group(1))
        won = int(round(man * 10_000))
        if 100_000 <= won <= 50_000_000:  # 10만~5천만 월소득 합리적 범위
            return won

    # 2) plain 원 amount (e.g. 2300000원)
    m2 = re.search(r"(\d{6,9})\s*원", s)
    if m2:
        won = int(m2.group(1))
        if 100_000 <= won <= 50_000_000:
            return won

    # 3) 월급/소득 근처 숫자만 (만원 단위 추정: 100~999 → *10000)
    m3 = re.search(r"(?:월급|월소득|소득|연봉)?\D*?(\d{2,3})(?!\d)", s)
    if m3 and any(k in s for k in ("월급", "월소득", "소득", "만원", "저축")):
        n = int(m3.group(1))
        if 50 <= n <= 999:  # 50만~999만 표현
            # only if "만" appeared somewhere or 월급+세자리
            if "만" in s or "월급" in s:
                won = n * 10_000
                if 100_000 <= won <= 50_000_000:
                    return won

    return None
