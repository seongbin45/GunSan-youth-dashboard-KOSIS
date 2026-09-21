"""
Single UserContext schema for FinFit pages + FinFitAgent.

Goals (accuracy first):
- One place maps session_state / onboarding / ledger / benefit form → structured profile
- Every filled field records *source* (never silent invention)
- Defaults used only by agent tool args stay outside this schema (assumptions)
- Legacy session keys kept working; canonical snapshot at session["user_context"]
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Mapping, MutableMapping, Optional


# Canonical income_level values (benefits_matcher / AI tool enum)
INCOME_LEVELS = (
    "60%이하",
    "100%이하",
    "140%이하",
    "150%이하",
    "180%이하",
    "소득기준초과",
)

# Session keys we read (legacy multipage contract)
SESSION_KEYS = {
    "user_level",
    "monthly_income_range",
    "first_goal",
    "income",
    "level",
    "expenses",
    "savings_goals",
    "benefit_profile",
    "matched",
    "matched_benefit_cards",
    "ai_shared_benefits",
    "user_context",
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _set_field(
    sources: dict[str, str],
    confidences: dict[str, float],
    name: str,
    value: Any,
    source: str,
    confidence: float,
    *,
    allow_overwrite: bool = True,
) -> Any:
    """Record provenance; return value for assignment."""
    if value is None or value == "" or value == []:
        return None
    prev = sources.get(name)
    if prev and not allow_overwrite:
        return None
    # Higher confidence wins if already set in this build pass
    if name in confidences and confidences[name] > confidence:
        return None
    sources[name] = source
    confidences[name] = confidence
    return value


def income_range_to_monthly_won(income_range: str | None) -> Optional[int]:
    """
    H5: map onboarding income *range id/label* → representative monthly won (band midpoint).

    Derived only — never treat as measured salary. Caller must use source
    ``onboarding_range_mid`` and conf below chat/ledger-touched (~0.55).
    Open-ended ``over200`` uses 2_500_000 as a youth-entry midpoint, not a ceiling.
    """
    if not income_range:
        return None
    raw = str(income_range).strip()
    ir = raw.lower().replace(" ", "").replace("만원", "만").replace("~", "-").replace("～", "-")

    id_mid = {
        "under50": 400_000,
        "50to100": 750_000,
        "100to150": 1_250_000,
        "150to200": 1_750_000,
        "over200": 2_500_000,
    }
    if ir in id_mid:
        return id_mid[ir]

    # Label forms from Onboarding.INCOMES
    if "미만" in ir and "50" in ir:
        return 400_000
    if "200" in ir and "이상" in ir:
        return 2_500_000
    if "150" in ir and "200" in ir:
        return 1_750_000
    if "100" in ir and "150" in ir:
        return 1_250_000
    if "50" in ir and "100" in ir:
        return 750_000
    return None


def income_range_to_income_level(income_range: str | None) -> Optional[str]:
    """
    Soft map onboarding *range labels/ids* → mid-income band enum.
    This is derived, not measured 중위소득 — caller must mark source as derived.
    """
    if not income_range:
        return None
    raw = str(income_range).strip()
    ir = raw.lower().replace(" ", "")

    # Onboarding INCOMES[].id (pages/Onboarding.py)
    id_map = {
        "under50": "60%이하",
        "50to100": "100%이하",
        "100to150": "100%이하",
        "150to200": "140%이하",
        "over200": "180%이하",
    }
    if ir in id_map:
        return id_map[ir]

    # Explicit 중위% style
    if "초과" in ir or "해당없음" in ir:
        return "소득기준초과"
    if "60%" in ir:
        return "60%이하"
    if "180%" in ir:
        return "180%이하"
    if "150%" in ir:
        return "150%이하"
    if "140%" in ir:
        return "140%이하"
    if "100%" in ir:
        return "100%이하"

    # Won range labels from onboarding (approximate — derived only)
    # e.g. "50만원 미만", "150~200만원", "200만원 이상"
    if "미만" in ir and "50" in ir:
        return "60%이하"
    if "200이상" in ir or ("200" in ir and "이상" in ir):
        return "180%이하"
    if "150" in ir and "200" in ir:
        return "140%이하"
    if "100" in ir and "150" in ir:
        return "100%이하"
    if "50" in ir and "100" in ir:
        return "100%이하"
    if "200" in ir or "250" in ir or "300" in ir:
        return "180%이하"
    if "150" in ir:
        return "140%이하"
    if "100" in ir or "120" in ir:
        return "100%이하"
    return "100%이하"


def monthly_income_to_income_level(monthly_income: int | None) -> Optional[str]:
    """
    Very rough band from monthly won → mid-income enum (derived, not 중위 실측).
    Used only when user stated monthly income but not 중위%.
    """
    if monthly_income is None:
        return None
    try:
        m = int(monthly_income)
    except Exception:
        return None
    if m <= 0:
        return None
    # Coarse brackets aligned with onboarding-ish youth ranges
    if m < 500_000:
        return "60%이하"
    if m < 1_500_000:
        return "100%이하"
    if m < 2_500_000:
        return "140%이하"
    if m < 4_000_000:
        return "180%이하"
    return "소득기준초과"


def sum_expenses(expenses: Any) -> Optional[int]:
    if not expenses or not isinstance(expenses, list):
        return None
    total = 0
    any_amt = False
    for e in expenses:
        if not isinstance(e, dict):
            continue
        amt = e.get("amount") or e.get("지출금액") or 0
        try:
            if isinstance(amt, str):
                amt = int(float(amt.replace(",", "").strip() or 0))
            else:
                amt = int(amt)
            if amt:
                any_amt = True
                total += amt
        except Exception:
            continue
    return total if any_amt else None


def collect_benefit_names(session: Mapping[str, Any]) -> list[str]:
    names: list[str] = []
    for key in ("matched_benefit_cards", "ai_shared_benefits"):
        cards = session.get(key) or []
        if not isinstance(cards, list):
            continue
        for b in cards[:20]:
            if not isinstance(b, dict):
                continue
            name = b.get("name") or b.get("title")
            if name and name not in names:
                names.append(str(name))
    for name in session.get("matched") or []:
        if isinstance(name, str) and name and name not in names:
            names.append(name)
    return names


@dataclass
class UserContext:
    """
    Canonical user profile snapshot.

    Rules:
    - None means unknown (not defaulted).
    - sources[field] explains where the value came from.
    - confidences[field] in 0..1 (user form ~1.0, derived ~0.5–0.7).
    """

    # Onboarding / path
    path_level: Optional[str] = None  # beginner | experienced
    income_range: Optional[str] = None
    first_goal: Optional[str] = None

    # Benefit eligibility (normalized)
    age: Optional[int] = None
    income_level: Optional[str] = None
    employment_status: Optional[str] = None
    has_house: Optional[bool] = None

    # Finance
    monthly_income: Optional[int] = None
    monthly_spend: Optional[int] = None
    savings_level: Optional[int] = None  # 1~10 ledger/main
    current_savings_rate: Optional[str] = None
    active_goals: list[str] = field(default_factory=list)
    known_benefits: list[str] = field(default_factory=list)

    # Provenance
    sources: dict[str, str] = field(default_factory=dict)
    confidences: dict[str, float] = field(default_factory=dict)
    built_at: str = field(default_factory=_now)

    def missing_for_benefits(self) -> list[str]:
        miss = []
        if self.age is None:
            miss.append("age")
        if not self.income_level:
            miss.append("income_level")
        if not self.employment_status:
            miss.append("employment_status")
        if self.has_house is None:
            miss.append("has_house")
        return miss

    def missing_for_savings(self) -> list[str]:
        return ["monthly_income"] if self.monthly_income is None else []

    def to_public_dict(self) -> dict[str, Any]:
        """JSON-safe snapshot for session_state['user_context']."""
        d = asdict(self)
        return d

    def to_context_string(self) -> str:
        parts = []
        if self.path_level:
            parts.append(f"경로: {self.path_level}")
        if self.income_range:
            parts.append(f"소득구간: {self.income_range}")
        if self.first_goal:
            parts.append(f"주요 목표: {self.first_goal}")
        if self.age is not None:
            parts.append(f"나이: {self.age}세")
        if self.income_level:
            parts.append(f"중위소득대: {self.income_level}")
        if self.employment_status:
            parts.append(f"고용: {self.employment_status}")
        if self.has_house is not None:
            parts.append(f"주택: {'유주택' if self.has_house else '무주택'}")
        if self.monthly_income is not None:
            parts.append(f"월소득: {self.monthly_income:,}원")
        if self.monthly_spend is not None:
            parts.append(f"월지출합: {self.monthly_spend:,}원")
        if self.current_savings_rate:
            parts.append(f"저축률추정: {self.current_savings_rate}")
        if self.active_goals:
            parts.append(f"목표: {', '.join(self.active_goals[:5])}")
        if self.known_benefits:
            parts.append(f"관심혜택: {', '.join(self.known_benefits[:5])}")
        if not parts:
            return "아직 충분한 사용자 정보가 없습니다."
        # Append short provenance for honesty
        if self.sources:
            src_bits = [f"{k}←{v}" for k, v in list(self.sources.items())[:8]]
            parts.append("출처[" + ", ".join(src_bits) + "]")
        return " | ".join(parts)

    def provenance_lines(self) -> list[str]:
        lines = []
        for k, src in sorted(self.sources.items()):
            conf = self.confidences.get(k)
            conf_s = f" · conf {conf:.2f}" if conf is not None else ""
            val = getattr(self, k, None)
            if isinstance(val, list):
                val_s = f"{len(val)}건"
            else:
                val_s = str(val)
            lines.append(f"- **{k}** = `{val_s}` ← {src}{conf_s}")
        return lines


def build_user_context(
    session: Optional[Mapping[str, Any]] = None,
    *,
    prior: Any = None,
) -> UserContext:
    """
    Build UserContext from Streamlit session_state-like mapping + optional prior UserState.

    Priority (high → low) per field — only *known* values, never tool defaults:
      age: benefit_profile > prior.age
      income_level: benefit_profile > onboarding range (derived) > prior
      employment/has_house: benefit_profile > prior
      monthly_income: session income (ledger) > prior
      goals: savings_goals > first_goal > prior
    """
    session = session or {}
    ctx = UserContext()
    sources: dict[str, str] = {}
    confidences: dict[str, float] = {}

    # --- prior agent state (persisted memory) ---
    if prior is not None:
        prior_map = {
            "path_level": getattr(prior, "level", None),
            "income_range": getattr(prior, "income_range", None),
            "first_goal": getattr(prior, "first_goal", None),
            "age": getattr(prior, "age", None),
            "income_level": getattr(prior, "income_level", None),
            "employment_status": getattr(prior, "employment_status", None),
            "has_house": getattr(prior, "has_house", None),
            "monthly_income": getattr(prior, "monthly_income", None),
            "monthly_spend": getattr(prior, "monthly_spend", None),
            "current_savings_rate": getattr(prior, "current_savings_rate", None),
        }
        for name, raw in prior_map.items():
            if raw is None or raw == "":
                continue
            conf = 0.65
            sources[name] = "agent"
            confidences[name] = conf
            setattr(ctx, name, raw)
        goals = list(getattr(prior, "active_goals", None) or [])
        if goals:
            ctx.active_goals = list(goals)
            sources["active_goals"] = "agent"
            confidences["active_goals"] = 0.6
        kb = list(getattr(prior, "known_benefits", None) or [])
        if kb:
            ctx.known_benefits = list(kb)
            sources["known_benefits"] = "agent"
            confidences["known_benefits"] = 0.6

    # --- onboarding ---
    ul = session.get("user_level")
    if ul:
        v = _set_field(sources, confidences, "path_level", str(ul), "onboarding", 0.95)
        if v:
            ctx.path_level = v

    ir = session.get("monthly_income_range")
    if ir:
        v = _set_field(sources, confidences, "income_range", str(ir), "onboarding", 0.95)
        if v:
            ctx.income_range = v
        # derived mid-income band only if not set higher later
        derived = income_range_to_income_level(str(ir))
        if derived:
            # H2: must beat agent prior (0.65) so onboarding range is not
            # stuck under a previous chat-estimated mid-income band.
            # Still below benefit_profile (1.0).
            v2 = _set_field(
                sources, confidences, "income_level", derived, "onboarding_derived", 0.72
            )
            if v2:
                ctx.income_level = v2
        # H5: range → representative won for savings tools (not silent default 230만).
        # conf 0.55: below agent/chat (0.65) and ledger-touched (0.95);
        # above ledger factory default 2M (0.45).
        mid_won = income_range_to_monthly_won(str(ir))
        if mid_won is not None:
            v3 = _set_field(
                sources,
                confidences,
                "monthly_income",
                mid_won,
                "onboarding_range_mid",
                0.55,
            )
            if v3 is not None:
                ctx.monthly_income = v3

    fg = session.get("first_goal")
    if fg:
        v = _set_field(sources, confidences, "first_goal", str(fg), "onboarding", 0.95)
        if v:
            ctx.first_goal = v
        if v and v not in ctx.active_goals:
            # soft add goal label
            if "active_goals" not in sources or confidences.get("active_goals", 0) < 0.95:
                if v not in ctx.active_goals:
                    ctx.active_goals = [v] + [g for g in ctx.active_goals if g != v]
                sources["active_goals"] = "onboarding"
                confidences["active_goals"] = 0.9

    # --- ledger / main screen ---
    # H1: pages default income=2_000_000 without user edit must NOT beat
    # agent prior or chat-parsed income (conf 0.65). Only "touched" ledger wins.
    if session.get("income") not in (None, "", 0, "0"):
        try:
            mi = int(session["income"])
            touched = bool(
                session.get("income_touched")
                or session.get("income_user_set")
            )
            # Untouched factory default used by Ledger/Savings/Main
            if (not touched) and mi == 2_000_000:
                ledger_conf = 0.45  # below agent prior 0.65
                ledger_src = "ledger_default"
            else:
                ledger_conf = 0.95
                ledger_src = "ledger"
            v = _set_field(
                sources, confidences, "monthly_income", mi, ledger_src, ledger_conf
            )
            if v is not None:
                ctx.monthly_income = v
        except Exception:
            pass

    if session.get("level") not in (None, ""):
        try:
            lv = int(session["level"])
            if 1 <= lv <= 10:
                v = _set_field(sources, confidences, "savings_level", lv, "ledger", 0.9)
                if v is not None:
                    ctx.savings_level = v
        except Exception:
            pass

    spend = sum_expenses(session.get("expenses"))
    if spend is not None:
        v = _set_field(sources, confidences, "monthly_spend", spend, "ledger_derived", 0.85)
        if v is not None:
            ctx.monthly_spend = v
        inc = ctx.monthly_income
        if inc and inc > 0:
            rate = max(0.0, min(1.0, (inc - spend) / inc))
            rs = f"{int(rate * 100)}%"
            v2 = _set_field(
                sources, confidences, "current_savings_rate", rs, "ledger_derived", 0.8
            )
            if v2:
                ctx.current_savings_rate = v2

    goals = session.get("savings_goals")
    if isinstance(goals, list) and goals:
        titles = [g.get("title", str(g)) for g in goals if g]
        titles = [t for t in titles if t]
        if titles:
            ctx.active_goals = titles
            sources["active_goals"] = "savings"
            confidences["active_goals"] = 0.95

    # --- benefit form (highest for eligibility fields) ---
    bp = session.get("benefit_profile") or {}
    if isinstance(bp, dict) and bp:
        from .benefits_matcher import (
            normalize_employment,
            normalize_has_house,
            normalize_income_level,
        )

        if bp.get("age") not in (None, ""):
            try:
                age = int(bp["age"])
                v = _set_field(sources, confidences, "age", age, "benefit_profile", 1.0)
                if v is not None:
                    ctx.age = v
            except Exception:
                pass

        if bp.get("income_ui") or bp.get("income_level"):
            raw_inc = bp.get("income_ui") or bp.get("income_level")
            inc = normalize_income_level(str(raw_inc))
            v = _set_field(sources, confidences, "income_level", inc, "benefit_profile", 1.0)
            if v:
                ctx.income_level = v

        emp_ui = bp.get("employment_ui") or bp.get("employment")
        kws = bp.get("keywords") if isinstance(bp.get("keywords"), list) else None
        if emp_ui or kws:
            emp = normalize_employment(emp_ui, kws)
            v = _set_field(
                sources, confidences, "employment_status", emp, "benefit_profile", 1.0
            )
            if v:
                ctx.employment_status = v

        if bp.get("housing_ui") is not None or bp.get("has_house") is not None:
            house_raw = bp.get("housing_ui") if "housing_ui" in bp else bp.get("has_house")
            house = normalize_has_house(house_raw)
            sources["has_house"] = "benefit_profile"
            confidences["has_house"] = 1.0
            ctx.has_house = house

    # --- matched benefits names ---
    names = collect_benefit_names(session)
    if names:
        # merge unique, prefer session list
        merged = list(names)
        for n in ctx.known_benefits:
            if n not in merged:
                merged.append(n)
        ctx.known_benefits = merged[:30]
        sources["known_benefits"] = "benefit_match"
        confidences["known_benefits"] = 0.9

    ctx.sources = sources
    ctx.confidences = confidences
    ctx.built_at = _now()
    return ctx


def apply_context_to_user_state(state: Any, ctx: UserContext) -> None:
    """
    Copy known UserContext fields into FinFitAgent.UserState.
    Does not invent defaults; leaves state field unchanged if ctx is None for that field.
    """
    if ctx.path_level:
        state.level = ctx.path_level
    if ctx.income_range:
        state.income_range = ctx.income_range
    if ctx.first_goal:
        state.first_goal = ctx.first_goal
    if ctx.age is not None:
        state.age = ctx.age
    if ctx.income_level:
        state.income_level = ctx.income_level
    if ctx.employment_status:
        state.employment_status = ctx.employment_status
    if ctx.has_house is not None:
        state.has_house = ctx.has_house
    if ctx.monthly_income is not None:
        state.monthly_income = ctx.monthly_income
    if ctx.monthly_spend is not None:
        state.monthly_spend = ctx.monthly_spend
    if ctx.current_savings_rate:
        state.current_savings_rate = ctx.current_savings_rate
    if getattr(ctx, "savings_level", None) is not None:
        try:
            sl = int(ctx.savings_level)
            if 1 <= sl <= 10:
                state.savings_level = sl
        except Exception:
            pass
    if ctx.active_goals:
        state.active_goals = list(ctx.active_goals)
    if ctx.known_benefits:
        state.known_benefits = list(ctx.known_benefits)
    state.last_updated = _now()


def write_context_to_session(session: MutableMapping[str, Any], ctx: UserContext) -> None:
    """Store canonical snapshot; does not delete legacy keys."""
    session["user_context"] = ctx.to_public_dict()


def sync_session_and_state(
    session: MutableMapping[str, Any],
    state: Any,
) -> UserContext:
    """
    One-shot: build context from session+prior state, apply to agent state, write session snapshot.
    """
    ctx = build_user_context(session, prior=state)
    apply_context_to_user_state(state, ctx)
    write_context_to_session(session, ctx)
    return ctx


def load_context_from_session(session: Mapping[str, Any]) -> Optional[UserContext]:
    """Rehydrate snapshot if present; else None (caller should build)."""
    raw = session.get("user_context")
    if not isinstance(raw, dict):
        return None
    try:
        known = {f.name for f in UserContext.__dataclass_fields__.values()}  # type: ignore
        kwargs = {k: v for k, v in raw.items() if k in known}
        return UserContext(**kwargs)
    except Exception:
        return None
