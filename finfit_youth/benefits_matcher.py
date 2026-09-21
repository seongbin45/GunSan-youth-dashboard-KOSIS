"""
Match user profile against 온통청년(policy) snapshot cached by YouthDataService.

Primary source: youth_cache.db snapshot:policy (filled by pages/7_청년혜택업데이트.py sync).
Fallback: small curated static list only when cache is empty or yields nothing.
"""
from __future__ import annotations

import re
from typing import Any, Optional

from .cache_store import CacheStore
from .config import CACHE_DB_PATH

# 전북 지역 zip 코드 접두 (온통청년 zipCd 샘플: 52111 등)
_JEONBUK_ZIP_PREFIXES = ("52",)
_GUNSAN_HINTS = ("군산", "Gunsan", "GUNSAN")
_JEONBUK_HINTS = ("전북", "전라북", "전북특별", "전북자치")

# earnCndSeCd — observed codes; exact 중위% mapping is not documented, use soft ranks
# 0043001 appears most common (often unrestricted / broad)
# Prefer not hard-failing on unknown codes.
_INCOME_RANK = {
    "60%이하": 1,
    "100%이하": 2,
    "140%이하": 3,
    "150%이하": 4,
    "180%이하": 5,
    "소득기준초과": 9,
}


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(str(v).strip() or default)
    except Exception:
        return default


def _text_blob(item: dict[str, Any]) -> str:
    raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
    parts = [
        item.get("title") or "",
        item.get("summary") or "",
        item.get("region") or "",
        raw.get("plcyNm") or "",
        raw.get("plcyExplnCn") or "",
        raw.get("plcySprtCn") or "",
        raw.get("plcyKywdNm") or "",
        raw.get("lclsfNm") or "",
        raw.get("mclsfNm") or "",
        raw.get("sprvsnInstCdNm") or "",
        raw.get("operInstCdNm") or "",
        raw.get("ptcpPrpTrgtCn") or "",
        raw.get("addAplyQlfcCndCn") or "",
        raw.get("earnEtcCn") or "",
    ]
    return " ".join(str(p) for p in parts if p)


def _region_score(item: dict[str, Any]) -> tuple[int, str]:
    """Higher is better for Gunsan/Jeonbuk youth users."""
    raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
    blob = _text_blob(item)
    zip_cd = str(raw.get("zipCd") or item.get("region") or "")
    inst = str(raw.get("sprvsnInstCdNm") or "") + str(raw.get("rgtrInstCdNm") or "")

    if any(h in blob for h in _GUNSAN_HINTS) or "군산" in inst:
        return 50, "군산/지역 명시"
    if any(h in blob or h in inst for h in _JEONBUK_HINTS):
        return 35, "전북 권역"
    # zip list may be comma-separated codes
    codes = re.findall(r"\d{5}", zip_cd)
    if codes and any(c.startswith(_JEONBUK_ZIP_PREFIXES) for c in codes):
        return 30, "전북 zipCd"
    if not codes and not zip_cd.strip():
        return 15, "전국/지역 미지정"
    # other regions still usable but lower
    return 5, "타지역·전국"


def _age_ok(age: int, raw: dict[str, Any]) -> tuple[bool, str]:
    lim = str(raw.get("sprtTrgtAgeLmtYn") or "N").upper()
    mn = _safe_int(raw.get("sprtTrgtMinAge"), 0)
    mx = _safe_int(raw.get("sprtTrgtMaxAge"), 0)
    if lim == "Y" and (mn or mx):
        if mn and age < mn:
            return False, f"최소연령 {mn}"
        if mx and mx < 99 and age > mx:
            return False, f"최대연령 {mx}"
        return True, f"연령 {mn or '?'}~{mx or '?'}"
    # no hard limit → soft pass for typical youth ages
    if 15 <= age <= 45:
        return True, "연령 제한 없음/완화"
    return True, "연령 정보 없음"


def _employment_score(employment_status: str, blob: str) -> int:
    s = 0
    if employment_status == "미취업":
        if any(k in blob for k in ("미취업", "구직", "취업지원", "실업", "취준")):
            s += 12
        if any(k in blob for k in ("재직", "근로자", "재직자")) and "미취업" not in blob:
            s -= 8
    elif employment_status == "취업자":
        if any(k in blob for k in ("재직", "근로", "취업자", "직장")):
            s += 10
        if "미취업" in blob and "취업" not in blob:
            s -= 4
    elif employment_status == "창업자":
        if any(k in blob for k in ("창업", "스타트업", "사업자")):
            s += 12
    return s


def _housing_score(has_house: bool, blob: str) -> int:
    if not has_house:
        if any(k in blob for k in ("무주택", "월세", "전세", "주거", "임대")):
            return 10
    else:
        if any(k in blob for k in ("무주택", "월세")):
            return -6
    return 0


def _query_score(query: str, blob: str, title: str) -> int:
    if not query:
        return 0
    q = query.lower().strip()
    score = 0
    for token in re.split(r"\s+", q):
        if len(token) < 2:
            continue
        if token in title.lower():
            score += 15
        elif token in blob.lower():
            score += 8
    return score


def _life_stage_score_delta(
    *,
    title: str,
    blob: str,
    query: str,
    employment_status: str,
) -> int:
    """
    Demote policies that require a life-stage the user did not signal.

    Not geography-first (군산 가점과 무관). Only avoids e.g. 신혼 정책을
    미혼·취준 질문 상단에 올리는 정확도 문제.
    """
    q = f"{query or ''} {employment_status or ''}"
    text = f"{title} {blob}"
    delta = 0

    user_married = any(k in q for k in ("신혼", "기혼", "부부", "배우자", "결혼"))
    policy_married = any(k in text for k in ("신혼부부", "신혼 ", "신혼을", "부부 ")) or (
        "신혼" in title
    )
    if policy_married and not user_married:
        delta -= 45

    user_startup = any(k in q for k in ("창업", "기업", "사업자", "자영업", "스타트업"))
    policy_startup = any(
        k in text for k in ("창업", "청년기업", "스타트업", "예비창업", "사업장 대여")
    )
    if (
        employment_status in ("미취업", "")
        and policy_startup
        and not user_startup
    ):
        delta -= 28

    user_farm = any(k in q for k in ("귀농", "귀촌", "농업", "농민", "스마트팜", "영농"))
    policy_farm = any(
        k in text for k in ("귀농", "귀촌", "농업인", "스마트팜", "영농", "농생명")
    )
    if policy_farm and not user_farm:
        delta -= 35

    # mild boost: job-seeker + job support wording
    if employment_status == "미취업" or any(
        k in q for k in ("취준", "구직", "미취업")
    ):
        if any(k in text for k in ("취업", "구직", "일자리", "채용", "직업훈련", "교육")):
            if not policy_startup:
                delta += 8

    return delta


def _category_from_raw(raw: dict[str, Any], blob: str) -> str:
    l1 = str(raw.get("lclsfNm") or "")
    l2 = str(raw.get("mclsfNm") or "")
    if l1:
        return f"{l1}" + (f"/{l2}" if l2 else "")
    for cat, keys in (
        ("자산형성", ("적금", "저축", "자산", "금융")),
        ("주거", ("월세", "전세", "주거", "주택")),
        ("구직", ("취업", "구직", "일자리", "채용")),
        ("창업", ("창업",)),
        ("생활복지", ("복지", "상담", "문화", "패스")),
    ):
        if any(k in blob for k in keys):
            return cat
    return "청년정책"


def _to_benefit_card(item: dict[str, Any], score: int, why: str) -> dict[str, Any]:
    raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
    blob = _text_blob(item)
    title = item.get("title") or raw.get("plcyNm") or "제목 없음"
    support = str(raw.get("plcySprtCn") or item.get("summary") or "")[:200]
    condition_bits = []
    mn = _safe_int(raw.get("sprtTrgtMinAge"), 0)
    mx = _safe_int(raw.get("sprtTrgtMaxAge"), 0)
    if mn or mx:
        condition_bits.append(f"연령 {mn or '?'}~{mx or '?'}")
    inst = raw.get("sprvsnInstCdNm") or ""
    if inst:
        condition_bits.append(str(inst))
    region_note = why
    url = raw.get("aplyUrlAddr") or raw.get("refUrlAddr1") or ""
    return {
        "category": _category_from_raw(raw, blob),
        "name": title,
        "benefit": support or (item.get("summary") or "")[:160] or "지원 내용 본문 참고",
        "condition": " · ".join(condition_bits) or "요건은 상세 공고 확인",
        "region_match": region_note,
        "policy_id": item.get("id") or raw.get("plcyNo") or "",
        "url": url,
        "source": "온통청년 정책 캐시",
        "score": score,
    }


def _static_fallback(age, income_level, employment_status, has_house) -> list[dict]:
    """Minimal offline list used only when cache has no usable matches."""
    matched = []
    is_over = income_level == "소득기준초과"
    is_u60 = not is_over and income_level == "60%이하"
    is_u100 = is_u60 or (not is_over and income_level == "100%이하")
    is_u140 = is_u100 or (not is_over and income_level == "140%이하")
    is_u150 = is_u140 or (not is_over and income_level == "150%이하")
    is_u180 = is_u150 or (not is_over and income_level == "180%이하")
    is_un = employment_status == "미취업"
    is_wo = employment_status == "취업자"
    is_fo = employment_status == "창업자"
    if 19 <= age <= 34 and not is_over:
        matched.append({
            "category": "자산형성", "name": "청년미래적금(2026신설)",
            "benefit": "월 최대 50만원x3년, 최대 2,200만원",
            "condition": "만 19~34세, 소득 6천만원 이하",
            "source": "로컬 폴백", "score": 1,
        })
    if 19 <= age <= 34 and is_u180:
        matched.append({
            "category": "자산형성", "name": "청년도약계좌",
            "benefit": "5년 월 최대 70만원, 최대 5,000만원+비과세",
            "condition": "만 19~34세, 중위 관련 요건 확인",
            "source": "로컬 폴백", "score": 1,
        })
    if 18 <= age <= 39 and is_u140 and (is_wo or is_fo):
        matched.append({
            "category": "자산형성", "name": "전북청년 함께두배적금",
            "benefit": "월 10만원 1:1 매칭, 2년 후 두 배",
            "condition": "전북 거주 근로·창업 청년",
            "source": "로컬 폴백", "score": 1,
        })
    if not has_house and 19 <= age <= 34 and is_u60:
        matched.append({
            "category": "주거", "name": "청년월세 한시 특별지원",
            "benefit": "월 최대 20만원x24개월",
            "condition": "무주택, 중위 60% 이하",
            "source": "로컬 폴백", "score": 1,
        })
    if is_un and 18 <= age <= 34 and is_u100:
        matched.append({
            "category": "구직", "name": "국민취업지원제도 1유형",
            "benefit": "구직촉진수당 월 60만원x6개월",
            "condition": "미취업·소득 요건 확인",
            "source": "로컬 폴백", "score": 1,
        })
    if 18 <= age <= 39:
        matched.append({
            "category": "생활복지", "name": "K-패스 등 생활 지원(예시)",
            "benefit": "교통·생활 지원 상품 검토",
            "condition": "연령 요건 확인",
            "source": "로컬 폴백", "score": 1,
        })
    return matched


def load_policy_snapshot(store: Optional[CacheStore] = None) -> list[dict[str, Any]]:
    store = store or CacheStore(CACHE_DB_PATH)
    snap = store.get("snapshot:policy", max_age_seconds=None)
    return snap if isinstance(snap, list) else []


def normalize_income_level(income_level: str) -> str:
    """Map UI labels (page 4 / onboarding) → agent tool income_level enum."""
    s = str(income_level or "").replace(" ", "")
    if "초과" in s or "해당없음" in s:
        return "소득기준초과"
    if "60" in s:
        return "60%이하"
    if "100" in s:
        return "100%이하"
    if "140" in s:
        return "140%이하"
    if "150" in s:
        return "150%이하"
    if "180" in s:
        return "180%이하"
    # short forms from page 4 expander: "60%", "100%", ...
    return "100%이하"


def normalize_has_house(has_house) -> bool:
    if isinstance(has_house, bool):
        return has_house
    s = str(has_house or "")
    if "무주택" in s:
        return False
    if "유주택" in s or "있음" in s:
        return True
    return False


def normalize_employment(
    employment: str | None = None,
    selected_keywords: list | None = None,
) -> str:
    joined = " ".join(selected_keywords or [])
    emp = str(employment or "")
    blob = f"{joined} {emp}"
    if "창업" in blob:
        return "창업자"
    if "미취업" in blob or "구직" in blob:
        return "미취업"
    if "농업" in blob:
        return "농업종사자"
    if "취업" in blob or "근로" in blob:
        return "취업자"
    return "미취업"


def keywords_to_query(selected_keywords: list | None, extra: str = "") -> str:
    parts = list(selected_keywords or [])
    if extra:
        parts.append(extra)
    # shorten long UI labels to search tokens
    tokens = []
    for p in parts:
        if "미취업" in p or "구직" in p:
            tokens.append("취업")
        elif "취업" in p:
            tokens.append("취업")
        elif "창업" in p:
            tokens.append("창업")
        elif "농업" in p:
            tokens.append("농업")
        elif "신혼" in p:
            tokens.append("신혼")
        elif "다자녀" in p:
            tokens.append("다자녀")
        else:
            tokens.append(str(p)[:20])
    return " ".join(tokens)


def match_benefits_for_ui(
    age: int,
    income_level: str,
    has_house,
    selected_keywords: list | None = None,
    employment: str | None = None,
    query: str = "",
    limit: int = 15,
    store: Optional[CacheStore] = None,
) -> dict[str, Any]:
    """
    Single entry for Pages (esp. page 4) + backward-compatible shape.

    Returns:
      - matched_policies: list[str]  (legacy page 4 / config API)
      - benefits: list[dict]         (full cards, same as AI tool)
      - data_source, cache_size, summary, profile_used, ...
    """
    inc = normalize_income_level(income_level)
    house = normalize_has_house(has_house)
    emp = normalize_employment(employment, selected_keywords)
    q = (query or "").strip() or keywords_to_query(selected_keywords)

    core = match_benefits(
        age=int(age),
        income_level=inc,
        employment_status=emp,
        has_house=house,
        query=q,
        limit=limit,
        store=store,
    )
    names = [b.get("name") for b in core.get("benefits") or [] if b.get("name")]
    return {
        **core,
        "matched_policies": names,
        "is_over_limit": inc == "소득기준초과",
        "is_youth_18_34": 18 <= int(age) <= 34,
        "normalized": {
            "income_level": inc,
            "employment_status": emp,
            "has_house": house,
            "query": q,
        },
    }


def match_benefits(
    age: int,
    income_level: str,
    employment_status: str,
    has_house: bool,
    query: str = "",
    limit: int = 12,
    store: Optional[CacheStore] = None,
) -> dict[str, Any]:
    """
    Rank 온통청년 policy snapshot for a user profile.
    Returns same shape as previous tool: matched_count, benefits, summary + meta.
    """
    snapshot = load_policy_snapshot(store)
    ranked: list[tuple[int, dict]] = []

    for item in snapshot:
        if not isinstance(item, dict):
            continue
        raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
        blob = _text_blob(item)
        title = str(item.get("title") or raw.get("plcyNm") or "")

        ok_age, age_why = _age_ok(int(age), raw)
        if not ok_age:
            continue

        r_score, r_why = _region_score(item)
        score = r_score
        score += _employment_score(employment_status, blob)
        score += _housing_score(bool(has_house), blob)
        score += _query_score(query, blob, title)
        score += _life_stage_score_delta(
            title=title,
            blob=blob,
            query=query or "",
            employment_status=str(employment_status or ""),
        )

        # Prefer finance/job/housing for FinFit chat default ranking when no query
        if not query:
            if any(k in blob for k in ("금융", "적금", "저축", "월세", "전세", "취업", "구직", "주거", "자산")):
                score += 6

        # Mild income text soft boost
        if income_level and income_level != "소득기준초과":
            if "소득" in blob or "중위" in blob:
                score += 2

        if score < 12:
            # drop weak/irrelevant (esp. other-region seminars)
            continue

        why = f"{r_why}; {age_why}"
        ranked.append((score, _to_benefit_card(item, score, why)))

    ranked.sort(key=lambda x: (-x[0], x[1].get("name") or ""))
    benefits = [b for _, b in ranked[:limit]]

    data_source = "온통청년 정책 캐시"
    if not benefits:
        benefits = _static_fallback(age, income_level, employment_status, has_house)
        data_source = "로컬 폴백 (캐시 매칭 없음 — 7_청년혜택업데이트에서 정책 동기화 권장)"

    jeonbuk = sum(
        1
        for b in benefits
        if "전북" in (b.get("region_match") or "") or "군산" in (b.get("region_match") or "")
    )
    result = {
        "matched_count": len(benefits),
        "benefits": benefits,
        "summary": (
            f"총 {len(benefits)}건 추천 (출처: {data_source}, "
            f"전북·군산 관련 점수 상위 {jeonbuk}건 포함). "
            "신청 가능 확정 아님 — 공식 공고 확인 필요."
        ),
        "data_source": data_source,
        "cache_size": len(snapshot),
        "query": query or "",
        "profile_used": {
            "age": age,
            "income_level": income_level,
            "employment_status": employment_status,
            "has_house": has_house,
        },
    }
    from .trust_copy import enrich_benefits_result

    return enrich_benefits_result(result, store=store or CacheStore(CACHE_DB_PATH))
