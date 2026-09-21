"""
FinFit Agent Core — multi-step tool orchestration with user state + memory.

Honest scope (prototype):
- Explicit UserState + simple typed/episodic memory
- Rule-based plan + staged research_step (tools + light internal checks)
- Session grounding (onboarding / ledger / savings when present)
- Tracked assumptions when defaults fill missing profile fields
- Final LLM synthesis only; prefers complete answers over "need more info"
- Not a full paper-faithful ReAct/Reflexion/CoALA implementation
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

# Intent routing lives in intent_routing.py (golden-locked). Re-export for back-compat.
from .intent_routing import (  # noqa: F401
    wants_stats_query,
    wants_savings_query,
    wants_benefit_query,
    stats_category_for_query,
    is_unclear_intent,
    CLARIFY_INTENT_TEXT,
)

# Project root (finfit_youth/..)
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Canonical agent JSON store (keeps project root clean)
AGENT_STATE_DIR = _PROJECT_ROOT / "data" / "agent_state"


def _safe_user_id(user_id: str) -> str:
    """Prevent path traversal; keep filenames stable and short."""
    s = re.sub(r"[^A-Za-z0-9._-]", "_", str(user_id or "default")).strip("._")
    return (s[:80] if s else "default")


# --- 1. Structured User State (the "world model" the AI maintains) ---
@dataclass
class UserState:
    # From Onboarding
    level: Optional[str] = None                    # beginner / experienced
    income_range: Optional[str] = None             # "50만원 미만", "150~200만원" etc.
    first_goal: Optional[str] = None               # "노트북·전자기기", "비상금 마련"...

    # Inferred / learned over time
    age: Optional[int] = None
    income_level: Optional[str] = None             # "60%이하", "100%이하"...
    employment_status: Optional[str] = None        # "미취업", "취업자"...
    has_house: Optional[bool] = None

    # Financial state (should be synced from Household_Ledger + Savings)
    monthly_income: Optional[int] = None
    monthly_spend: Optional[int] = None
    current_savings_rate: Optional[str] = None
    savings_level: Optional[int] = None  # 1–10 from Savings/Main session "level"
    active_goals: List[str] = field(default_factory=list)
    known_benefits: List[str] = field(default_factory=list)  # names of benefits user is eligible for or interested in

    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_context_string(self) -> str:
        parts = []
        if self.level: parts.append(f"경로: {self.level}")
        if self.income_range: parts.append(f"소득: {self.income_range}")
        if self.first_goal: parts.append(f"주요 목표: {self.first_goal}")
        if self.age: parts.append(f"나이: {self.age}세")
        if self.monthly_income: parts.append(f"월 소득: {self.monthly_income:,}원")
        if self.monthly_spend: parts.append(f"추정 월 지출: {self.monthly_spend:,}원")
        if self.current_savings_rate: parts.append(f"저축률: {self.current_savings_rate}")
        if self.savings_level is not None: parts.append(f"저축강도: {self.savings_level}단계")
        if self.active_goals: parts.append(f"활성 목표: {', '.join(self.active_goals)}")
        if self.known_benefits: parts.append(f"알고 있는/자격 혜택: {', '.join(self.known_benefits[:5])}")
        return " | ".join(parts) if parts else "아직 충분한 사용자 정보가 없습니다."

    def update_from_facts(self, facts: List[Dict[str, Any]]):
        """Deeper state update from typed facts."""
        for f in facts:
            value = f.get("value", "").lower()
            if "세" in value and any(str(i) in value for i in range(19, 40)):
                import re
                m = re.search(r'(\d{2})', value)
                if m:
                    self.age = int(m.group(1))
            if "목표" in value or "저축" in value or "적금" in value:
                clean = f.get("value")
                if clean and clean not in self.active_goals:
                    self.active_goals.append(clean)
        self.last_updated = datetime.now().isoformat()


# --- 2. Memory System ---
@dataclass
class MemoryStore:
    """Structured memory for deeper reasoning.
    Facts are now typed for better state management and retrieval.
    This is fundamental for an agent that actually 'learns' the user over time.
    """
    facts: List[Dict[str, Any]] = field(default_factory=list)  # e.g. {"type": "goal", "value": "...", "confidence": 0.8, "ts": "..."}
    episodes: List[Dict[str, str]] = field(default_factory=list)

    def add_fact(self, fact_text: str, fact_type: str = "general"):
        fact = {
            "type": fact_type,
            "value": fact_text,
            "ts": datetime.now().isoformat(),
            "confidence": 0.7
        }
        # Avoid exact duplicates
        if not any(f["value"] == fact_text for f in self.facts):
            self.facts.append(fact)
            if len(self.facts) > 40:
                self.facts = self.facts[-30:]

    def add_episode(self, user_msg: str, assistant_msg: str, tools_used: List[str]):
        self.episodes.append({
            "ts": datetime.now().isoformat(),
            "user": user_msg[:250],
            "assistant": assistant_msg[:400],
            "tools": tools_used
        })
        if len(self.episodes) > 25:
            self.episodes = self.episodes[-15:]

    def get_relevant_context(self, query: str = "") -> str:
        """Query-aware retrieval for deeper relevance.
        Simple keyword + recency for now (can upgrade to embeddings later).
        This allows the agent to pull specific memories based on the current question.
        """
        ctx_parts = []

        if self.facts:
            relevant_facts = self.facts[-12:]
            if query:
                q_lower = query.lower()
                relevant_facts = [f for f in self.facts if q_lower in f.get("value", "").lower()] or self.facts[-8:]

            by_type = {}
            for f in relevant_facts[-10:]:
                t = f.get("type", "general")
                by_type.setdefault(t, []).append(f["value"])

            facts_str = []
            for t, vals in by_type.items():
                facts_str.append(f"[{t}]: " + "; ".join(vals))
            ctx_parts.append("관련 기억된 사실:\n" + "\n".join(f"- {s}" for s in facts_str))

        if self.episodes:
            recent = self.episodes[-3:]
            ctx_parts.append("최근 상호작용:\n" + "\n".join(
                f"사용자: {e['user']}\nAI: {e['assistant'][:150]}..." for e in recent))

        return "\n\n".join(ctx_parts) if ctx_parts else "아직 충분한 기억이 없습니다."


# --- 3. Core Agent ---
class FinFitAgent:
    """
    Multi-step research orchestrator for FinFit chat.
    Owns plan → tool/internal steps → synthesis context; page executes tools.
    """

    # Explicit defaults used only when profile fields are missing (always tracked)
    DEFAULTS = {
        "age": 25,
        "income_level": "100%이하",
        "employment_status": "미취업",
        "has_house": False,
        "monthly_income": 2300000,
        "savings_level": 5,
    }

    def __init__(self, user_id: str = "default"):
        self.user_id = user_id
        self.state = UserState()
        self.memory = MemoryStore()
        self.research_trajectory = []  # List of {plan, actions, observations, reflection}
        self.research_findings = []
        self._last_plan = None
        # Per-turn assumptions: [{field, value, reason, source}] — honesty for financial UX
        self.assumptions: List[Dict[str, Any]] = []
        # Last UserContext from sync_from_session (sourced profile; may be None)
        self.last_user_context = None
        self._load()

    def clear_turn_scratch(self):
        """
        Reset per-question research scratch (not long-term memory/state).

        research_trajectory is cleared so tools are NOT treated as 'already covered'
        across different user messages (bug: 2nd stats question planned 0 steps).
        Within one turn, multi-round still rebuilds trajectory via reflect_and_learn.
        """
        self.research_findings = []
        self.assumptions = []
        self._last_plan = None
        self.research_trajectory = []
        # Do not carry "insufficient" flag into a new user question
        if hasattr(self.state, "last_research_was_insufficient"):
            self.state.last_research_was_insufficient = False

    def record_assumption(self, field: str, value: Any, reason: str, source: str = "default"):
        """Record a filled-in default so users/LLM never treat it as verified fact."""
        for a in self.assumptions:
            if a.get("field") == field:
                a["value"] = value
                a["reason"] = reason
                a["source"] = source
                return
        self.assumptions.append({
            "field": field,
            "value": value,
            "reason": reason,
            "source": source,
            "ts": datetime.now().isoformat(),
        })

    def get_assumptions_text(self, for_user: bool = True) -> str:
        if not self.assumptions:
            return ""
        if for_user:
            # Split: user_message overrides | derived estimates | true defaults
            overrides = [a for a in self.assumptions if a.get("source") == "user_message"]
            derived = [a for a in self.assumptions if a.get("source") == "derived"]
            defaults = [
                a
                for a in self.assumptions
                if a.get("source") not in ("user_message", "derived")
            ]
            lines: list[str] = []
            if overrides:
                lines.append("**이번 계산에 반영한 질문 내용** (프로필과 다를 수 있음):")
                for a in overrides:
                    lines.append(f"- {a['field']}: `{a['value']}` — {a['reason']}")
            if derived:
                lines.append(
                    "**추정으로 쓴 값** (중위소득 등 공식 기준이 아님 · 실제와 다를 수 있음):"
                )
                for a in derived:
                    lines.append(f"- {a['field']}: `{a['value']}` — {a['reason']}")
            if defaults:
                lines.append("**이번 답변에 쓰인 가정** (실제 정보와 다를 수 있음):")
                for a in defaults:
                    lines.append(f"- {a['field']}: `{a['value']}` — {a['reason']}")
                lines.append("_프로필·가계부를 채우면 가정이 줄고 맞춤도가 올라갑니다._")
            elif overrides or derived:
                lines.append(
                    "_온보딩·프로필(나이·소득 등)을 질문에 맞게 맞춰 두면 이 안내가 줄어듭니다._"
                )
            return "\n".join(lines)
        lines = [f"{a['field']}={a['value']} ({a['reason']})" for a in self.assumptions]
        return "; ".join(lines)

    def benefit_tool_args(self, query: str = "") -> dict:
        """
        Args for check_benefit_eligibility.

        Age priority: message (e.g. 25세) → profile → default + assumption.
        Other missing fields → defaults + assumptions.
        """
        from .income_parse import (
            parse_age_years,
            parse_employment_status,
            parse_has_house,
        )

        parsed_age = parse_age_years(query)

        if parsed_age is not None:
            age = int(parsed_age)
            prev = self.state.age
            if prev is not None and int(prev) != age:
                self.record_assumption(
                    "age",
                    age,
                    f"이번 질문에 적힌 나이({age}세)를 프로필({int(prev)}세)보다 우선해 조회",
                    "user_message",
                )
            self.state.age = age
        elif self.state.age is not None:
            age = self.state.age
        else:
            age = self.DEFAULTS["age"]
            self.record_assumption("age", age, "나이 미입력 → 혜택 조회용 기본값", "default")

        if self.state.income_level:
            income_level = self.state.income_level
        else:
            # Prefer derived bands from onboarding range or stated monthly income
            # (not measured 중위소득 — still disclosed as assumption/derived)
            from .user_context import (
                income_range_to_income_level,
                monthly_income_to_income_level,
            )

            derived = None
            derived_why = ""
            if self.state.income_range:
                derived = income_range_to_income_level(self.state.income_range)
                derived_why = (
                    f"온보딩 소득구간({self.state.income_range})에서 추정 "
                    f"(중위소득 실측 아님)"
                )
            if not derived and self.state.monthly_income is not None:
                derived = monthly_income_to_income_level(int(self.state.monthly_income))
                derived_why = (
                    f"월소득 {int(self.state.monthly_income):,}원에서 구간 추정 "
                    f"(중위소득 실측 아님)"
                )
            if derived:
                income_level = derived
                self.state.income_level = derived
                self.record_assumption(
                    "income_level",
                    income_level,
                    derived_why,
                    "derived",
                )
            else:
                income_level = self.DEFAULTS["income_level"]
                self.record_assumption(
                    "income_level",
                    income_level,
                    "소득수준 미입력 → 중위 100% 이하 가정",
                    "default",
                )

        parsed_emp = parse_employment_status(query)
        if parsed_emp is not None:
            employment_status = parsed_emp
            prev_e = self.state.employment_status
            if prev_e and prev_e != employment_status:
                self.record_assumption(
                    "employment_status",
                    employment_status,
                    f"이번 질문에 적힌 고용({employment_status})을 프로필({prev_e})보다 우선",
                    "user_message",
                )
            self.state.employment_status = employment_status
        elif self.state.employment_status:
            employment_status = self.state.employment_status
        else:
            employment_status = self.DEFAULTS["employment_status"]
            self.record_assumption(
                "employment_status",
                employment_status,
                "고용상태 미입력 → 미취업 가정",
                "default",
            )

        parsed_house = parse_has_house(query)
        if parsed_house is not None:
            has_house = bool(parsed_house)
            prev_h = self.state.has_house
            if prev_h is not None and bool(prev_h) != has_house:
                self.record_assumption(
                    "has_house",
                    has_house,
                    f"이번 질문에 적힌 주택({'있음' if has_house else '무주택'})을 프로필보다 우선",
                    "user_message",
                )
            self.state.has_house = has_house
        elif self.state.has_house is not None:
            has_house = self.state.has_house
        else:
            has_house = self.DEFAULTS["has_house"]
            self.record_assumption(
                "has_house", has_house, "주택보유 미입력 → 무주택 가정", "default"
            )

        args = {
            "age": age,
            "income_level": income_level,
            "employment_status": employment_status,
            "has_house": has_house,
        }
        q = (query or "").strip()
        if q:
            args["query"] = q[:80]
        return args

    def savings_tool_args(
        self,
        savings_level: Optional[int] = None,
        user_message: str = "",
    ) -> dict:
        """
        Income priority:
          1) amount explicitly stated in this user_message (e.g. 230만원)
          2) profile monthly_income
          3) default + assumption
        """
        from .income_parse import parse_monthly_income_won

        parsed = parse_monthly_income_won(user_message)
        if parsed is not None:
            income = int(parsed)
            prev = self.state.monthly_income
            # User-stated income is evidence, not a "default assumption".
            # Still surface a short note when it overrides a different profile value.
            if prev is not None and int(prev) != income:
                self.record_assumption(
                    "monthly_income",
                    income,
                    f"이번 질문에 적힌 소득({income:,}원)을 프로필({int(prev):,}원)보다 우선해 계산",
                    "user_message",
                )
            # Align state with what we calculate this turn
            self.state.monthly_income = income
        elif self.state.monthly_income is not None:
            income = int(self.state.monthly_income)
            # H5 honesty: onboarding band midpoint is derived, not measured
            uc = getattr(self, "last_user_context", None)
            src = None
            if uc is not None:
                src = (getattr(uc, "sources", None) or {}).get("monthly_income")
            if src == "onboarding_range_mid":
                self.record_assumption(
                    "monthly_income",
                    income,
                    f"온보딩 소득구간({self.state.income_range or '?'}) 중위 추정으로 저축 계산",
                    "onboarding_range_mid",
                )
        else:
            # Last resort: range string on state without won (pre-H5 sessions)
            mid = None
            try:
                from .user_context import income_range_to_monthly_won

                mid = income_range_to_monthly_won(self.state.income_range)
            except Exception:
                mid = None
            if mid is not None:
                income = int(mid)
                self.record_assumption(
                    "monthly_income",
                    income,
                    f"온보딩 소득구간({self.state.income_range}) 중위 추정으로 저축 계산",
                    "onboarding_range_mid",
                )
            else:
                income = self.DEFAULTS["monthly_income"]
                self.record_assumption(
                    "monthly_income", income,
                    "월소득 미입력 → 예시 소득으로 저축 계획 계산", "default"
                )
        # Level: explicit arg > synced state (Savings/Main session) > default
        if savings_level is not None:
            level = int(savings_level)
        elif self.state.savings_level is not None:
            try:
                level = int(self.state.savings_level)
            except Exception:
                level = self.DEFAULTS["savings_level"]
            if not (1 <= level <= 10):
                level = self.DEFAULTS["savings_level"]
        else:
            level = self.DEFAULTS["savings_level"]
        return {"income": income, "savings_level": level}

    def _safe_id(self) -> str:
        return _safe_user_id(self.user_id)

    def _get_persist_path(self) -> str:
        """Canonical path: data/agent_state/agent_state_{id}.json"""
        AGENT_STATE_DIR.mkdir(parents=True, exist_ok=True)
        return str(AGENT_STATE_DIR / f"agent_state_{self._safe_id()}.json")

    def _legacy_persist_path(self) -> str:
        """Old root-level path (pre Phase 1-4). Used only for one-time migrate/load."""
        return str(_PROJECT_ROOT / f"agent_state_{self._safe_id()}.json")

    def _migrate_legacy_if_needed(self) -> None:
        """
        If canonical file missing but root-level legacy file exists, copy once.
        Does not delete the legacy file (operator may clean later).
        """
        new_path = Path(self._get_persist_path())
        legacy = Path(self._legacy_persist_path())
        if new_path.is_file() or not legacy.is_file():
            return
        try:
            AGENT_STATE_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(legacy, new_path)
        except Exception:
            pass

    def _load(self):
        self._migrate_legacy_if_needed()
        path = self._get_persist_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.state = UserState(**data.get("state", {}))
                self.memory = MemoryStore(**data.get("memory", {}))
            except Exception:
                pass  # corrupted, start fresh

    def save(self):
        path = self._get_persist_path()
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "state": asdict(self.state),
                "memory": {"facts": self.memory.facts, "episodes": self.memory.episodes}
            }, f, ensure_ascii=False, indent=2)

    def update_from_onboarding(self, level=None, income_range=None, first_goal=None):
        if level:
            self.state.level = level
        if income_range:
            self.state.income_range = income_range
        if first_goal:
            self.state.first_goal = first_goal
        self.save()

    def sync_from_session(self, session: dict):
        """
        Single path: finfit_youth.user_context builds a sourced profile from
        onboarding / ledger / savings / benefit form, then applies to UserState.
        Does not invent defaults (those stay in benefit_tool_args assumptions).
        """
        from .user_context import sync_session_and_state

        try:
            self.last_user_context = sync_session_and_state(session, self.state)
        except Exception:
            # Never break chat if session shape is unexpected
            self.last_user_context = None
        self.save()
        return getattr(self, "last_user_context", None)

    def get_context_for_llm(self) -> str:
        ctx_extra = ""
        uc = getattr(self, "last_user_context", None)
        if uc is not None:
            miss_b = uc.missing_for_benefits()
            miss_s = uc.missing_for_savings()
            if miss_b or miss_s:
                ctx_extra = (
                    f"\n[미입력 — 도구 시 가정 가능] 혜택:{miss_b or '없음'} 저축:{miss_s or '없음'}"
                )
            if uc.sources:
                src = ", ".join(f"{k}←{v}" for k, v in list(uc.sources.items())[:10])
                ctx_extra += f"\n[필드 출처] {src}"
        return f"""
[사용자 상태]
{self.state.to_context_string()}
{ctx_extra}

[기억 및 과거]
{self.memory.get_relevant_context()}
"""

    def extract_facts(self, user_message: str, final_answer: str, tools_used: List[str]) -> List[Dict[str, Any]]:
        """Deeper fact extraction returning typed facts for structured memory."""
        typed_facts = []
        text = (user_message + " " + final_answer).lower()

        if any(word in text for word in ["살", "나이", "세"]):
            import re
            m = re.search(r'(\d{2})살', user_message)
            if m:
                typed_facts.append({"type": "profile", "value": f"나이 약 {m.group(1)}세", "confidence": 0.8})

        if "도약" in text or "적금" in text or "자산형성" in text:
            typed_facts.append({"type": "goal", "value": "청년도약계좌 등 자산형성 상품에 관심", "confidence": 0.7})

        if "월세" in text or "주택" in text or "전세" in text:
            typed_facts.append({"type": "interest", "value": "주거 지원/주택 관련 관심", "confidence": 0.7})

        if tools_used:
            typed_facts.append({"type": "behavior", "value": f"최근 사용 도구: {', '.join(tools_used)}", "confidence": 0.9})

        return typed_facts

    def plan(self, user_message: str, trajectory: list = None) -> dict:
        """
        Deeper + trajectory-aware: Return structured research plan.
        Uses past reflections and actions from trajectory to:
        - Avoid repetition
        - Learn what succeeded (from reflections)
        - Prioritize missing pillars (execution -> structurization stages)
        Cumulative deep research (Reflexion + CoALA).
        """
        relevant_mem = self.memory.get_relevant_context(user_message)
        state_str = self.state.to_context_string()
        trajectory = trajectory or self.research_trajectory or []

        # Tools already executed *this turn only* (trajectory is cleared each deep_research).
        # Never block a tool solely because a prior chat message used it.
        covered = set()
        successful_reflections = []
        for t in trajectory:
            for act in t.get("actions", []) or []:
                if act and not str(act).startswith("_"):
                    covered.add(act)
            refl = t.get("reflection", "") or ""
            if "Sufficient" in refl or "충분" in refl:
                successful_reflections.append(refl[:120])
            # Do NOT add plan-only steps to covered — only executed actions
            # (old bug: planned-but-skipped tools permanently blocked re-plan)

        # Build structured plan with stages
        research_steps = []

        # Stage 1: benefits (keyword OR open-ended first_goal — not on pure 저축/통계)
        need_benefit = wants_benefit_query(user_message, self.state.first_goal)
        if need_benefit and "check_benefit_eligibility" not in covered:
            research_steps.append({
                "step": len(research_steps) + 1,
                "tool": "check_benefit_eligibility",
                "args": self.benefit_tool_args(user_message),
                "purpose": "온통청년 정책 캐시 매칭 (프로필·질문 키워드, 부족 시 가정 기록)"
            })

        # Stage 2: savings (explicit intent only)
        need_savings = wants_savings_query(user_message)
        if need_savings and "calculate_savings_plan" not in covered:
            research_steps.append({
                "step": len(research_steps) + 1,
                "tool": "calculate_savings_plan",
                "args": self.savings_tool_args(None, user_message),
                "purpose": "저축 계획 (질문 소득·세션 저축강도 우선 · 없으면 기본)"
            })

        # Stage 3: stats (explicit data intent only)
        need_stats = wants_stats_query(user_message)
        if need_stats and "get_gunsan_youth_stats" not in covered:
            cat = stats_category_for_query(user_message)
            research_steps.append({
                "step": len(research_steps) + 1,
                "tool": "get_gunsan_youth_stats",
                "args": {"category": cat},
                "purpose": f"통계 맥락 제공 (category={cat}; 취업 지표는 지역·단위 분리)"
            })

        # Insufficient recovery: only tools the *question* still wants (no random pillar inject)
        if getattr(self.state, "last_research_was_insufficient", False):
            if (
                need_savings
                and "calculate_savings_plan" not in covered
                and not any(s["tool"] == "calculate_savings_plan" for s in research_steps)
            ):
                research_steps.append({
                    "step": len(research_steps) + 1,
                    "tool": "calculate_savings_plan",
                    "args": self.savings_tool_args(None, user_message),
                    "purpose": "이전 결과 부족 → 저축 의도 보완"
                })
            if (
                need_stats
                and "get_gunsan_youth_stats" not in covered
                and not any(s["tool"] == "get_gunsan_youth_stats" for s in research_steps)
            ):
                cat = stats_category_for_query(user_message)
                research_steps.append({
                    "step": len(research_steps) + 1,
                    "tool": "get_gunsan_youth_stats",
                    "args": {"category": cat},
                    "purpose": f"이전 결과 부족 → 현황 데이터 보완 (category={cat})"
                })
            if (
                need_benefit
                and "check_benefit_eligibility" not in covered
                and not any(s["tool"] == "check_benefit_eligibility" for s in research_steps)
            ):
                research_steps.append({
                    "step": len(research_steps) + 1,
                    "tool": "check_benefit_eligibility",
                    "args": self.benefit_tool_args(user_message),
                    "purpose": "이전 결과 부족 → 혜택 의도 보완"
                })

        # Build plan_text with stages
        clarify = (not research_steps) and is_unclear_intent(
            user_message, self.state.first_goal
        )
        plan_text = f"""[관찰]
상태: {state_str}
기억: {relevant_mem[:300]}...

[질문] {user_message}

[연구 계획 - {len(research_steps)} steps | trajectory 사용: {len(trajectory)} prior rounds | 성공 reflection: {len(successful_reflections)}]
"""
        for s in research_steps:
            plan_text += f"- Step {s['step']}: {s['tool']} ({s['purpose']})\n"
        if clarify:
            plan_text += (
                "\n[의도 불명 — 도구 미선택]\n"
                "과호출을 피하기 위해 혜택/저축/통계 도구를 자동 실행하지 않습니다.\n"
                f"{CLARIFY_INTENT_TEXT}\n"
            )

        plan_dict = {
            "plan_text": plan_text,
            "steps": research_steps,
            "user_goal": self.state.first_goal,
            "covered_so_far": list(covered),
            "learned_from_reflections": successful_reflections[:2],
            "clarify": clarify,
            "clarify_text": CLARIFY_INTENT_TEXT if clarify else "",
        }
        self._last_plan = plan_dict

        return plan_dict

    def run(self, user_message: str, llm_caller, tools: dict) -> tuple[str, list]:
        """
        The core reasoning loop - made more fundamental.
        This agent now owns the full Observe-Plan- (execute delegated) -Reflect-Learn cycle.
        The LLM is used as a powerful reasoner within the structure we provide.
        """
        # 1. Observe
        context = self.get_context_for_llm()

        # 2. Explicit Plan
        plan = self.plan(user_message, trajectory=self.research_trajectory)

        full_context = f"""{context}

{plan}

[지시] 위 관찰과 계획을 바탕으로 사용자의 장기 목표를 염두에 두고 행동하라."""

        # 3. Execution is still delegated (to support multiple LLM providers cleanly)
        # but the context now forces deeper, state-aware reasoning.
        return full_context, []

    def get_suggested_tools(self, user_message: str, plan: dict = None, previous_results: list = None) -> list:
        """
        Agent decides tools from the structured plan.
        Now trajectory-aware: skips tools already heavily used in this research session.
        """
        if plan is None or not isinstance(plan, dict):
            plan = self.plan(user_message, trajectory=self.research_trajectory)

        previous_results = previous_results or []
        done_recent = [r.get("tool") for r in previous_results if r.get("tool") and not str(r.get("tool")).startswith("_")][-4:]

        suggested = []
        for step in plan.get("steps", []):
            t = step["tool"]
            if t not in done_recent:
                suggested.append((t, step["args"]))

        # If all main steps already done in trajectory, the caller will hit synthesize path.
        # Still return what remains (or empty -> synthesize).
        return suggested or []

    def evaluate_research_sufficiency(
        self, user_message: str, tool_results: list
    ) -> bool:
        """
        Whether another tool round is warranted.

        True only when a pillar the *question* cares about is missing,
        errored, or empty — NOT when profile fields (first_goal/age/…)
        are blank. Profile gaps are handled via assumptions, not loops.
        """
        cares_benefit = wants_benefit_query(user_message, self.state.first_goal)
        cares_savings = wants_savings_query(user_message)
        cares_stats = wants_stats_query(user_message)
        if not (cares_benefit or cares_savings or cares_stats):
            return False

        results = [
            r
            for r in (tool_results or [])
            if r.get("tool") and not str(r.get("tool")).startswith("_")
        ]

        def _out(r: dict) -> dict:
            o = r.get("output") or {}
            return o if isinstance(o, dict) else {}

        def _errored(out: dict) -> bool:
            if out.get("error"):
                return True
            # common tool failure shapes
            err = out.get("error_detail") or out.get("message")
            return bool(err) and out.get("from_db") is False and not out.get("data")

        if cares_benefit:
            bens = [r for r in results if r.get("tool") == "check_benefit_eligibility"]
            if not bens:
                return True
            for r in bens:
                out = _out(r)
                if _errored(out):
                    return True
                if len(out.get("benefits") or []) < 1:
                    # ensure defaults/assumptions recorded for a retry path
                    self.benefit_tool_args(user_message)
                    return True

        if cares_savings:
            savs = [r for r in results if r.get("tool") == "calculate_savings_plan"]
            if not savs:
                return True
            for r in savs:
                out = _out(r)
                if out.get("error") or "monthly_savings" not in out:
                    return True

        if cares_stats:
            stats = [r for r in results if r.get("tool") == "get_gunsan_youth_stats"]
            if not stats:
                return True
            for r in stats:
                out = _out(r)
                if out.get("error"):
                    return True
                if out.get("from_db") is False and not (out.get("data") or out.get("figures")):
                    return True

        return False

    def reflect_and_learn(self, user_message: str, tool_results: list, final_answer: str):
        """
        Fundamental reflection step with deep research decision.
        The agent evaluates results and decides if more deep research (additional tools) is needed.
        Returns dict with 'needs_more_research' so the caller can iterate instead of giving up.
        This prevents UX-damaging "more information needed" responses.
        """
        # 1. Extract structured learnings
        new_facts = self.extract_facts(user_message, final_answer, [t.get("tool") for t in (tool_results or [])])

        for f in new_facts:
            self.memory.add_fact(f["value"], f.get("type", "general"))

        # 2. Update state from tool outputs more intelligently
        if tool_results:
            for tr in tool_results:
                tool_name = tr.get("tool")
                output = tr.get("output", {}) or {}

                if tool_name == "check_benefit_eligibility":
                    for b in output.get("benefits", []):
                        name = b.get("name")
                        if name and name not in self.state.known_benefits:
                            self.state.known_benefits.append(name)

                elif tool_name == "calculate_savings_plan":
                    if "monthly_savings" in output:
                        self.state.current_savings_rate = output.get("savings_rate")

        # 3. Update state from facts
        self.state.update_from_facts(new_facts)

        # 4. Sufficiency: only question-scoped tool gaps/errors (not empty profile)
        needs_more_research = self.evaluate_research_sufficiency(
            user_message, tool_results or []
        )

        # 5. get_suggested_tools가 다음 라운드에서 더 공격적으로 tool을 고를 수 있게 힌트 저장
        self.state.last_research_was_insufficient = needs_more_research

        # 6. Build verbal reflection (Reflexion style) and append to trajectory
        verbal_reflection = f"After this round: {'More research needed' if needs_more_research else 'Sufficient for synthesis'}. Key learnings: {new_facts}. Critique: {self.critique(user_message, tool_results or [], final_answer)}"
        self.research_trajectory.append({
            "round": len(self.research_trajectory) + 1,
            "user_message": user_message,
            "plan": getattr(self, '_last_plan', {}),
            "actions": [t.get("tool") for t in (tool_results or [])],
            "observations": [str(t.get("output", {}))[:100] for t in (tool_results or [])],
            "reflection": verbal_reflection
        })
        self.memory.add_fact(verbal_reflection, "reflection")

        # 7. Record episode
        self.memory.add_episode(user_message, final_answer, [t.get("tool") for t in (tool_results or [])])

        self.save()

        return {
            "new_facts": new_facts,
            "needs_more_research": needs_more_research,
            "verbal_reflection": verbal_reflection
        }

    def after_response(self, user_message: str, final_answer: str, tools_used: List[str], tool_results: list = None):
        """Legacy wrapper - now delegates to reflect_and_learn for depth."""
        return self.reflect_and_learn(user_message, tool_results or [], final_answer)

    def synthesize_final(self, raw_llm_output: str, tool_results: list, user_message: str) -> str:
        """
        Post-process LLM output: surface assumptions honestly, avoid empty/weak replies.
        Soft numeric guard (answer_guard) warns when large unmatched figures appear.
        """
        from .answer_guard import soft_check_answer

        state_str = self.state.to_context_string()
        synthesized = (raw_llm_output or "").strip()

        # Strip noisy technical prefixes if model echoed them
        for noise in ("[Agent 상태 요약]", "[Agent Research Summary"):
            if synthesized.startswith(noise):
                # keep body after first blank line if possible
                parts = synthesized.split("\n\n", 1)
                if len(parts) == 2:
                    synthesized = parts[1]

        # User-facing assumptions first (financial honesty)
        assume_block = self.get_assumptions_text(for_user=True)
        if assume_block and assume_block not in synthesized:
            synthesized = assume_block + "\n\n" + synthesized

        if self.state.active_goals and "목표" not in synthesized:
            synthesized += f"\n\n(참고 목표: {', '.join(self.state.active_goals[:2])})"

        bad_phrases = ["more info", "정보가 필요", "추가 정보", "더 많은 정보", "충분한 정보가"]
        if any(p in synthesized.lower() for p in bad_phrases) or len(synthesized) < 60:
            synthesized = (
                "보유한 프로필·가계부·조회 결과로 답변했습니다. "
                "아래 가정이 있으면 참고하세요.\n\n" + synthesized
            )

        if len(synthesized.strip()) < 20:
            synthesized = (
                f"{assume_block + chr(10) + chr(10) if assume_block else ''}"
                f"현재 파악된 정보({state_str}) 기준으로 안내합니다. "
                f"질문: {user_message}. "
                f"목표({self.state.first_goal or '자산 형성'})에 맞춰 혜택 자격과 저축 계획을 함께 확인하는 것을 권합니다."
            )

        # B2 soft: unmatched significant numbers vs tool + profile grounding
        external = [
            r
            for r in (tool_results or [])
            if r.get("tool") and not str(r.get("tool")).startswith("_")
        ]
        plan = getattr(self, "_last_plan", None) or {}
        clarify_only = (not external) and (
            bool(plan.get("clarify"))
            or is_unclear_intent(user_message, self.state.first_goal)
        )
        # Profile / known-benefit text figures allowed (not invented stats)
        # Live false positives: monthly_income 2e6; year 2026 in "청년미래적금(2026신설)"
        extra_allowed: set[float] = set()
        if self.state.monthly_income is not None:
            extra_allowed.add(float(self.state.monthly_income))
        if self.state.monthly_spend is not None:
            extra_allowed.add(float(self.state.monthly_spend))
        if self.state.age is not None:
            extra_allowed.add(float(self.state.age))
        for name in (self.state.known_benefits or [])[:20]:
            from .answer_guard import numbers_from_text, is_calendar_year

            for n in numbers_from_text(str(name)):
                if is_calendar_year(n) or abs(n) >= 100:
                    extra_allowed.add(n)
        guard = soft_check_answer(
            synthesized,
            tool_results,
            clarify_only=clarify_only,
            extra_allowed=extra_allowed,
        )
        self._last_answer_guard = guard
        if guard.get("warning_text") and guard["warning_text"] not in synthesized:
            synthesized = guard["warning_text"] + "\n\n" + synthesized

        return synthesized

    def critique(self, user_message: str, tool_results: list, current_answer: str) -> str:
        """
        Lightweight gap check scoped to the question (avoid forcing unrelated tools).
        """
        q = (user_message or "").lower()
        cares_benefit = wants_benefit_query(user_message, self.state.first_goal)
        cares_savings = wants_savings_query(user_message)
        cares_stats = wants_stats_query(user_message)

        missing = []
        if cares_benefit:
            if self.state.age is None:
                missing.append("나이(가정 가능)")
            if not self.state.income_level:
                missing.append("소득수준(가정 가능)")
            n_ben = 0
            for r in tool_results or []:
                if r.get("tool") == "check_benefit_eligibility":
                    n_ben = max(n_ben, len((r.get("output") or {}).get("benefits") or []))
            if n_ben < 1 and not any(r.get("tool") == "check_benefit_eligibility" for r in (tool_results or [])):
                missing.append("혜택_도구_미실행")
        if cares_savings and not any(r.get("tool") == "calculate_savings_plan" for r in (tool_results or [])):
            missing.append("저축_도구_미실행")
        if cares_stats and not any(r.get("tool") == "get_gunsan_youth_stats" for r in (tool_results or [])):
            missing.append("통계_도구_미실행")

        if missing:
            return f"질문 범위 내 부족: {', '.join(missing)}."
        return "질문 범위 내 핵심 도구/정보는 확보된 것으로 보임."

    def refine_plan_with_critique(
        self,
        original_plan: dict,
        critique: str,
        tool_results: list,
        user_message: str = "",
    ) -> dict:
        """
        Add only tools that the critique explicitly marks as missing for this question.
        Stats category follows stats_category_for_query(user_message) — not a fixed population.
        """
        new_steps = original_plan.get("steps", [])[:]
        # Prefer message from plan context if caller forgot (research_step should pass it)
        msg = user_message or (original_plan.get("plan_text") or "")

        if "혜택_도구_미실행" in critique:
            if not any(s["tool"] == "check_benefit_eligibility" for s in new_steps):
                new_steps.append({
                    "step": len(new_steps) + 1,
                    "tool": "check_benefit_eligibility",
                    "args": self.benefit_tool_args(),
                    "purpose": "질문에 필요한 혜택 조회 보완"
                })

        if "저축_도구_미실행" in critique:
            if not any(s["tool"] == "calculate_savings_plan" for s in new_steps):
                new_steps.append({
                    "step": len(new_steps) + 1,
                    "tool": "calculate_savings_plan",
                    "args": self.savings_tool_args(None, user_message=msg),
                    "purpose": "질문에 필요한 저축 계산 보완"
                })

        if "통계_도구_미실행" in critique:
            if not any(s["tool"] == "get_gunsan_youth_stats" for s in new_steps):
                cat = stats_category_for_query(msg)
                new_steps.append({
                    "step": len(new_steps) + 1,
                    "tool": "get_gunsan_youth_stats",
                    "args": {"category": cat},
                    "purpose": f"질문에 필요한 현황 데이터 보완 (category={cat})"
                })

        new_plan_text = original_plan.get("plan_text", "") + f"\n\n[보완]\n{critique}"

        return {
            "plan_text": new_plan_text,
            "steps": new_steps,
            "user_goal": self.state.first_goal
        }

    def cross_verify_results(self, tool_results: list) -> str:
        """
        Deeper verification step: Agent cross-checks tool results against its current state and memory.
        This prevents accepting bad data and triggers re-research if inconsistencies.
        """
        issues = []
        state = self.state

        for tr in tool_results:
            tool = tr.get("tool")
            out = tr.get("output", {}) or {}
            if tool == "check_benefit_eligibility":
                if "benefits" in out and len(out["benefits"]) == 0 and state.first_goal:
                    issues.append(f"혜택 결과가 없는데 목표({state.first_goal})가 있음. 추가 확인 필요.")
            if "error" in str(out):
                issues.append(f"{tool} 에서 에러 발생.")

        if issues:
            return "검증 이슈: " + "; ".join(issues)
        return "결과 일관성 확인됨. 상태와 일치."

    def deep_research(self, user_message: str, max_rounds: int = 3) -> dict:
        """
        Start a research turn: clear scratch, build plan, return initial tools.
        """
        self.clear_turn_scratch()
        plan = self.plan(user_message, trajectory=self.research_trajectory)
        initial_tools = self.get_suggested_tools(user_message, plan)
        return {
            "plan": plan,
            "initial_tools": initial_tools,
            "state_snapshot": self.state.to_context_string(),
            "assumptions": list(self.assumptions),
            "research_id": f"research_{datetime.now().isoformat()}"
        }

    def ingest_tool_result(self, tool_name: str, args: dict, output: dict):
        """Deeper: Agent ingests each tool result, updates state/memory immediately, and records finding."""
        if tool_name and tool_name.startswith("_"):
            # internal actions already recorded their finding in _perform_internal_reason
            return
        finding = {
            "tool": tool_name,
            "args": args,
            "output": output,
            "ts": datetime.now().isoformat()
        }
        self.research_findings.append(finding)

        # Immediate state update from this result
        if tool_name == "check_benefit_eligibility":
            for b in output.get("benefits", []):
                name = b.get("name")
                if name and name not in self.state.known_benefits:
                    self.state.known_benefits.append(name)
        elif tool_name == "calculate_savings_plan":
            if "savings_rate" in output:
                self.state.current_savings_rate = output["savings_rate"]

        self.memory.add_fact(f"Tool {tool_name} result: {str(output)[:200]}", "research_finding")

    def prepare_synthesis_context(self, user_message: str, all_steps: list) -> str:
        """Deeper: Agent prepares the richest possible context for the final LLM synthesis call.
        This ensures the LLM gets a clean, state-grounded research summary instead of raw tool dumps.
        Includes ALLOWED FIGURES block so synthesis stays tool-grounded (answer_guard).
        """
        from .answer_guard import build_allowed_figures_block

        findings_summary = []
        for f in self.research_findings:
            findings_summary.append(f"[{f['tool']}] {str(f['output'])[:150]}")

        # Prefer explicit step list (page loop) when research_findings empty
        steps_for_guard = all_steps if all_steps else list(self.research_findings)
        allowed_block = build_allowed_figures_block(steps_for_guard)

        critique = self.critique(user_message, all_steps, "")
        verification = self.cross_verify_results(all_steps)

        # Include compact trajectory for cumulative reflection (Reflexion/CoALA)
        traj_summary = ""
        if self.research_trajectory:
            recent = self.research_trajectory[-3:]
            traj_summary = "\n".join([f"Round {t.get('round')}: actions={t.get('actions')} | {t.get('reflection','')[:80]}" for t in recent])

        state_ctx = self.state.to_context_string()
        goals = ", ".join(self.state.active_goals[:3]) if self.state.active_goals else self.state.first_goal or "자산 형성/안정"
        spend_note = f" (지출 {self.state.monthly_spend:,}원 추정)" if getattr(self.state, 'monthly_spend', None) else ""
        assumptions_block = self.get_assumptions_text(for_user=False) or "(없음 — 프로필 필드가 채워져 있음)"
        plan = getattr(self, "_last_plan", None) or {}
        clarify = bool(plan.get("clarify")) or is_unclear_intent(
            user_message, self.state.first_goal
        )
        clarify_block = ""
        if clarify and not findings_summary:
            clarify_block = f"""
[INTENT CLARIFY — no tools selected]
{plan.get("clarify_text") or CLARIFY_INTENT_TEXT}

Instructions for clarify mode:
- Do NOT invent statistics or benefit eligibility.
- Politely ask the user to pick one of the three options above (or rephrase).
- Keep the reply short (4-8 sentences) in Korean.
"""
        # Scope synthesis to tools actually run this turn (avoid stats Q → long benefit dump)
        ext_tools = {
            str(s.get("tool") or "")
            for s in (all_steps or [])
            if s.get("tool") and not str(s.get("tool")).startswith("_")
        }
        pillar_focus = []
        if "get_gunsan_youth_stats" in ext_tools:
            pillar_focus.append(
                "STATS-ONLY FOCUS: Lead with tool statistics (reasons, %, source). "
                "Do NOT list known_benefits or open savings accounts unless the user also asked for benefits/savings. "
                "Next actions should be about interpreting the data or asking a follow-up stats/benefit question — not inventing program details."
            )
        if "check_benefit_eligibility" in ext_tools:
            pillar_focus.append(
                "BENEFIT FOCUS: Use only benefits from this turn's tool findings."
            )
        if "calculate_savings_plan" in ext_tools:
            pillar_focus.append(
                "SAVINGS FOCUS: Use only savings figures from this turn's tool findings."
            )
        if not ext_tools and not clarify:
            pillar_focus.append("No tools this turn — do not invent stats or benefit eligibility.")
        focus_block = "\n".join(f"- {x}" for x in pillar_focus) if pillar_focus else "- (general)"

        return f"""[Research Summary for final answer]
User State: {state_ctx}{spend_note}
Primary Goals: {goals}

[ASSUMPTIONS — must surface to user if any]
{assumptions_block}

{allowed_block}

Findings:
{chr(10).join(findings_summary) or "(도구 결과 없음)"}

Recent steps:
{traj_summary or "(none)"}

Critique: {critique}
Verification: {verification}
{clarify_block}
Question: {user_message}

[ANSWER SCOPE]
{focus_block}

Instructions:
- Write a complete, actionable answer in Korean only (no other languages / no mixed scripts).
- Do not say "more information is needed" as a dead-end.
- If INTENT CLARIFY is present, follow clarify-mode instructions instead of inventing tool data.
- If ASSUMPTIONS is non-empty, start with a short "가정" section listing them clearly.
- ONLY use magnitudes listed under ALLOWED FIGURES as factual numbers; do not invent KOSIS/population/employment counts.
- Prefer verified state/ledger/tool numbers; mark estimates.
- Calendar years in program names (e.g. 2026) are fine; do not invent new statistics.
- Benefits: name, condition, amount when available from tool findings only — and only if BENEFIT FOCUS or user asked.
- Savings: concrete monthly figures when available from tool findings only — and only if SAVINGS FOCUS or user asked.
- End with 1-2 next actions aligned with ANSWER SCOPE.
- Do not invent government program details beyond tool findings."""

    def research_depth(self, user_message: str, plan: dict = None) -> str:
        """
        Adaptive depth for this turn (step 3 quality work).
        - shallow: single-pillar simple question → few steps
        - standard: two pillars
        - deep: three pillars / complex multi-intent
        """
        plan = plan or getattr(self, "_last_plan", None) or self.plan(
            user_message, trajectory=self.research_trajectory
        )
        n_tools = len(plan.get("steps") or [])
        q = (user_message or "").lower()
        pillars = 0
        if wants_benefit_query(user_message, self.state.first_goal):
            pillars += 1
        if wants_savings_query(user_message):
            pillars += 1
        if wants_stats_query(user_message):
            pillars += 1
        # plan size is a hard signal (keyword plan already scoped)
        if n_tools <= 1 and pillars <= 1:
            return "shallow"
        if n_tools <= 2 and pillars <= 2:
            return "standard"
        return "deep"

    def research_step(self, user_message: str, previous_results: list = None) -> dict:
        """
        Adaptive research step.
        shallow: tools → prepare → synthesize
        standard: tools → (optional assess) → prepare → synthesize
        deep: tools → structure → cross_verify → prepare → synthesize
        """
        if previous_results is None:
            previous_results = []

        # Ingest ONLY new external tool results
        already = {
            (f.get("tool"), str(f.get("output"))[:100])
            for f in self.research_findings
            if f.get("tool") and not str(f.get("tool")).startswith("_")
        }
        newly_ingested = []
        for res in previous_results:
            tname = res.get("tool") or ""
            if not tname or tname.startswith("_"):
                continue
            key = (tname, str(res.get("output"))[:100])
            if key in already:
                continue
            self.ingest_tool_result(tname, res.get("input", {}), res.get("output", {}) or {})
            newly_ingested.append(res)
            already.add(key)

        current_plan = getattr(self, "_last_plan", None) or self.plan(
            user_message, trajectory=self.research_trajectory
        )
        depth = self.research_depth(user_message, current_plan)
        real_tools = [
            r.get("tool")
            for r in previous_results
            if r.get("tool") and not str(r.get("tool")).startswith("_")
        ]
        last_tool = previous_results[-1].get("tool", "") if previous_results else ""
        has_assess = any("_internal_assess" in str(r.get("tool", "")) for r in previous_results)
        has_structure = any("_internal_structure" in str(r.get("tool", "")) for r in previous_results)
        has_cross = any("_internal_cross" in str(r.get("tool", "")) for r in previous_results)
        has_prepare = any("_internal_prepare" in str(r.get("tool", "")) for r in previous_results)

        needs_more = getattr(self.state, "last_research_was_insufficient", False)
        if newly_ingested:
            critique = self.critique(user_message, previous_results, "")
            verification = self.cross_verify_results(previous_results)
            if needs_more or "부족" in critique or "미실행" in critique:
                current_plan = self.refine_plan_with_critique(
                    current_plan,
                    critique + " | " + verification,
                    previous_results,
                    user_message=user_message,
                )
                self._last_plan = current_plan
                depth = self.research_depth(user_message, current_plan)
            reflect = self.reflect_and_learn(user_message, newly_ingested, "")
            needs_more = reflect.get("needs_more_research", False)

        raw_suggested = self.get_suggested_tools(
            user_message, current_plan, previous_results=previous_results
        )
        done = set(real_tools)
        suggested = [(t, a) for (t, a) in raw_suggested if t not in done]
        plan_tool_count = len(current_plan.get("steps") or [])

        def _internal(kind: str) -> dict:
            res = self._perform_internal_action(kind, user_message, previous_results, current_plan)
            return {
                "action": "internal",
                "internal_type": kind,
                "summary": res.get("summary", ""),
                "plan": current_plan,
                "findings": self.research_findings,
                "reason": res.get("reason", "internal"),
                "stage": kind,
                "depth": depth,
            }

        def _tool(t: str, a: dict, reason: str) -> dict:
            return {
                "action": "tool",
                "tool": t,
                "args": a,
                "plan": current_plan,
                "reason": reason,
                "stage": "execute",
                "depth": depth,
            }

        def _synth() -> dict:
            return {
                "action": "synthesize",
                "context": self.prepare_synthesis_context(user_message, previous_results),
                "plan": current_plan,
                "findings": self.research_findings,
                "stage": "synthesize",
                "depth": depth,
            }

        # --- Finish planned tools first (no assess gate between tools) ---
        if suggested and len(done) < plan_tool_count:
            if (not last_tool) or last_tool.startswith("_") or (
                last_tool and not last_tool.startswith("_") and len(done) < plan_tool_count
            ):
                if last_tool and not last_tool.startswith("_"):
                    t, a = suggested[0]
                    return _tool(t, a, "Complete planned tools")
                if not last_tool:
                    t, a = suggested[0]
                    return _tool(t, a, "Start planned tools")
                if last_tool.startswith("_internal") and suggested:
                    t, a = suggested[0]
                    return _tool(t, a, "Continue after internal")

        if suggested and not previous_results:
            t, a = suggested[0]
            return _tool(t, a, "Initial plan execution")

        tools_done = plan_tool_count == 0 or len(done) >= plan_tool_count or not suggested

        # --- After tools complete: synthesize (UI grounds answer; skip prepare theater) ---
        if tools_done and real_tools:
            if depth == "deep":
                # light structure only for complex multi-pillar
                if not has_structure:
                    return _internal("structure_findings")
                if has_structure and not has_cross:
                    return _internal("cross_verify")
                return _synth()
            # shallow / standard: tools → synthesize
            return _synth()

        # After internals mid-flight
        if last_tool and str(last_tool).startswith("_internal"):
            if suggested:
                t, a = suggested[0]
                return _tool(t, a, "Continue tools after internal")
            if depth == "deep":
                if not has_structure:
                    return _internal("structure_findings")
                if not has_cross:
                    return _internal("cross_verify")
            return _synth()

        if previous_results:
            return _synth()

        # No plan tools: clarify then synthesize (page uses fixed clarify template)
        if plan_tool_count == 0:
            has_clarify = any(
                "_internal_clarify" in str(r.get("tool", "")) for r in previous_results
            )
            if current_plan.get("clarify") or is_unclear_intent(
                user_message, self.state.first_goal
            ):
                if not has_clarify:
                    return _internal("clarify_intent")
                return _synth()
            return _synth()

        return _synth()

    def _perform_internal_action(self, kind: str, user_message: str, previous_results: list, current_plan: dict) -> dict:
        """CoALA internal actions (no LLM/provider call, pure agent reasoning).
        Supports multiple types for deeper Observe-InternalAct-Reflect:
        - "reason": basic integration of observations
        - "assess_coverage": evaluate what is missing vs plan/goals, may flip needs_more or suggest implicit next
        - "structure_findings": organize findings into structured insights, update memory/state
        Returns dict with summary + reason.
        """
        findings_str = "\n".join([f"- [{f.get('tool','?')}] {str(f.get('output',{}))[:110]}" for f in self.research_findings[-5:]])
        state_snap = self.state.to_context_string()[:140]
        base = f"[{kind.upper()}] on '{user_message}': {len(previous_results)} obs. State: {state_snap}."
        extra_output = {}

        if kind == "assess_coverage":
            real = [r.get("tool") for r in previous_results if r.get("tool") and not str(r.get("tool")).startswith("_")]
            div = len(set(real))
            missing = []
            if "check_benefit_eligibility" not in real: missing.append("benefits")
            if "calculate_savings_plan" not in real and self.state.monthly_income: missing.append("savings_calc")
            if not self.state.known_benefits: missing.append("known_benefits")
            summary = base + f" Coverage: diversity={div}. Missing pillars: {missing or 'none'}. "
            if missing:
                summary += "More research or assumptions from state recommended."
                self.state.last_research_was_insufficient = True
            else:
                summary += "Good coverage. Ready for deeper structure or synthesis."
                self.state.last_research_was_insufficient = False
            reason = "Coverage assessment to drive next decision (tool or synth)"

        elif kind == "structure_findings":
            insights = []
            for f in self.research_findings[-3:]:
                if "benefit" in str(f.get("tool","")).lower():
                    bs = f.get("output", {}).get("benefits", [])
                    if bs: insights.append(f"Benefits matched: {[b.get('name') for b in bs[:2]]}")
            if self.state.monthly_spend:
                insights.append(f"Spend-aware savings possible (~{int((self.state.monthly_income or 0) - self.state.monthly_spend):,}원 surplus est.)")
            summary = base + " Structured insights: " + "; ".join(insights or ["Findings integrated with state."])
            self.memory.add_fact("Structured: " + summary[:180], "structured_finding")
            # Update state if useful facts
            self.state.update_from_facts([{"value": summary, "type": "research"}])
            reason = "Structurization of findings (CoALA internal memory/procedural update)"

        elif kind == "prepare_synthesis":
            # Explicit structurization stage before final answer (CoALA)
            synth_ctx = self.prepare_synthesis_context(user_message, previous_results)
            key_points = []
            for f in self.research_findings[-4:]:
                if isinstance(f.get("output"), dict):
                    for k in ["benefits", "summary", "insight", "monthly_savings"]:
                        if k in f["output"]:
                            key_points.append(str(f["output"][k])[:80])
            summary = base + f" Prepared synthesis context. Key extracted: {'; '.join(key_points[:3]) or 'state + findings'}. Ready for complete grounded answer. Assumptions will be noted."
            self.memory.add_fact("Synthesis prep: " + summary[:150], "prepare_synthesis")
            reason = "Final internal structurization / preparation for synthesis (ensures complete answer)"
            # Force no more research
            self.state.last_research_was_insufficient = False
            # Store extra for output
            extra_output = {"draft_context_preview": synth_ctx[:400], "key_points": key_points}

        elif kind == "cross_verify":
            # Cross-verify findings against state, memory, and prior reflections (deeper Reflexion/CoALA)
            issues = []
            verified = []
            for f in self.research_findings[-4:]:
                t = f.get("tool", "")
                out = f.get("output", {}) or {}
                if t == "check_benefit_eligibility":
                    bens = out.get("benefits", [])
                    if bens and self.state.known_benefits:
                        verified.append(f"Benefits cross-checked: {len(bens)} matched to state.known")
                    elif not bens and self.state.first_goal:
                        issues.append("No benefits despite goal - state assumption used")
                if "savings" in t.lower() and self.state.monthly_spend:
                    verified.append("Savings calc verified against ledger spend")
            if issues:
                summary = base + f" Verification issues found: {'; '.join(issues)}. Using state assumptions to fill."
            else:
                summary = base + f" Cross-verified OK. Confirmed: {'; '.join(verified or ['state + findings consistent'])}"
            self.memory.add_fact("Cross-verify: " + summary[:160], "verification")
            # Update critique in state for next
            self.state.last_research_was_insufficient = bool(issues)
            reason = "Cross-verification of execution results against internal state/memory (ensures accuracy)"
            extra_output = {"verified": verified, "issues": issues}

        elif kind == "clarify_intent":
            text = (current_plan or {}).get("clarify_text") or CLARIFY_INTENT_TEXT
            summary = base + " Unclear intent — no tools auto-selected. " + text.replace("\n", " ")[:220]
            self.memory.add_fact("Clarify intent offered", "clarify_intent")
            self.state.last_research_was_insufficient = False
            reason = "Ask user to choose benefit / savings / stats instead of guessing tools"
            extra_output = {"clarify_text": text, "options": ["benefit", "savings", "stats"]}

        else:  # "reason" default
            summary = base + f" Key from findings: {findings_str[:280]}. "
            crit = self.critique(user_message, previous_results, summary)
            summary += f"Critique: {crit[:100]}"
            reason = "General internal reflection / reasoning"
            extra_output = {}

        # Always record (with extra for special kinds)
        tool_name = f"_internal_{kind}"
        out_rec = {"summary": summary, "round": len(previous_results)}
        if extra_output:
            out_rec.update(extra_output)
        self.research_findings.append({
            "tool": tool_name,
            "args": {"kind": kind},
            "output": out_rec,
            "ts": datetime.now().isoformat()
        })
        self.memory.add_fact(summary, f"internal_{kind}")

        # Re-eval stop condition
        if kind in ("assess_coverage", "structure_findings") or "충분" in summary or len(self.research_findings) >= 4:
            if not getattr(self.state, 'last_research_was_insufficient', True):
                pass  # already set above

        return {"summary": summary, "reason": reason, "kind": kind}