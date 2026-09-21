import streamlit as st
import json
import pandas as pd
import textwrap
from finfit_youth.config import inject_finfit_theme
from finfit_youth.tools import BASE_TOOLS as _BASE_TOOLS, TOOL_LABELS as _CORE_TOOL_LABELS, execute_tool

# Guarded import for Google (optional dependency)
try:
    import google.generativeai as _genai
    GOOGLE_OK = True
except ImportError:
    GOOGLE_OK = False
    _genai = None

st.set_page_config(page_title="AI 금융 상담", page_icon="💭", layout="wide")
inject_finfit_theme()

st.markdown("""
<style>
.stApp { background: #111111 !important; }
</style>
""", unsafe_allow_html=True)

# Consistent header (matching other pages)
st.markdown(textwrap.dedent("""
<div style="background:#1a1a1a; padding:12px 16px; margin:-8px -8px 8px; border-bottom:1px solid #333;">
  <div style="display:flex; align-items:center; gap:12px;">
    <div onclick="window.history.back()" style="width:36px;height:36px;background:#222;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;">
      <span style="font-size:18px;color:#aaa;">←</span>
    </div>
    <div>
      <div style="font-size:20px;font-weight:700;color:#f0f0f0;">💭 AI 금융 상담</div>
      <div style="font-size:12px;color:#888;">Gemini / Groq / Mistral · 실시간 답변</div>
    </div>
  </div>
</div>
"""), unsafe_allow_html=True)

# Guarded imports for optional AI providers
try:
    import anthropic as _anthropic
    ANTHROPIC_OK = True
except ImportError:
    ANTHROPIC_OK = False
    _anthropic = None

try:
    from openai import OpenAI as _OpenAI
    OPENAI_OK = True
except ImportError:
    OPENAI_OK = False
    _OpenAI = None


def _secret(key):
    import os
    # Try Streamlit secrets (top-level or under [secrets] section)
    try:
        if hasattr(st, "secrets"):
            sec = st.secrets
            # direct
            if key in sec:
                v = sec[key]
                if v and str(v).strip():
                    return str(v).strip()
            # under [secrets]
            if "secrets" in sec and key in sec["secrets"]:
                v = sec["secrets"][key]
                if v and str(v).strip():
                    return str(v).strip()
            # also try .get for safety
            v = sec.get(key) if hasattr(sec, "get") else None
            if v and str(v).strip():
                return str(v).strip()
    except Exception:
        pass
    # Fallback to environment variable
    v = os.getenv(key)
    if v and str(v).strip():
        return str(v).strip()
    return None

KEYS = {
    "Anthropic": _secret("ANTHROPIC_API_KEY"),
    "OpenAI":    _secret("OPENAI_API_KEY"),
    "Google":    _secret("GOOGLE_API_KEY"),
    "Groq":      _secret("GROQ_API_KEY"),
    "Mistral":   _secret("MISTRAL_API_KEY"),
}

# === Fundamental Agent Environment ===
from finfit_youth.agent import FinFitAgent

# Persistent agent instance (keyed by simple user id for now)
if "finfit_agent" not in st.session_state:
    st.session_state.finfit_agent = FinFitAgent(user_id="default")

AGENT: FinFitAgent = st.session_state.finfit_agent

# Single profile path: UserContext (onboarding + ledger + benefits + prior agent)
AGENT.update_from_onboarding(
    level=st.session_state.get("user_level"),
    income_range=st.session_state.get("monthly_income_range"),
    first_goal=st.session_state.get("first_goal"),
)
_uc = AGENT.sync_from_session(st.session_state)

# Legacy compatibility (some old demo code still references these)
USER_PROFILE = {
    "level": AGENT.state.level,
    "income_range": AGENT.state.income_range,
    "first_goal": AGENT.state.first_goal,
}
USER_CONTEXT = (
    _uc.to_context_string()
    if _uc is not None
    else AGENT.state.to_context_string()
)
MEMORY_CONTEXT = AGENT.memory.get_relevant_context()

# Fact extraction is now handled inside FinFitAgent.after_response() for cleaner architecture.
# Tool schemas + execute_tool: finfit_youth.tools (single registry)

def get_system_prompt(current_plan: str = ""):
    """근본적으로 강화된 시스템 프롬프트.
    AI가 단순 tool caller가 아니라, 사용자 상태 + 기억 + 명시적 계획을 바탕으로 깊이 추론하게 만듦.
    """
    plan = current_plan or st.session_state.get("_current_agent_plan", "")
    plan_section = f"\n\n## 현재 턴 계획 (Agent가 명시적으로 생성한 관찰/방향)\n{plan}" if plan else ""
    return f"""당신은 FinFit의 전문 청년 금융 AI Agent입니다.
군산시에 사는 19~39세 청년들의 실질적인 금융 생활을 돕는 것이 목표입니다.

## 현재 사용자 모델 (이걸 항상 최우선으로 고려)
{AGENT.state.to_context_string()}

## 장기 기억 (이전 상호작용에서 학습한 내용)
{AGENT.memory.get_relevant_context()}
{plan_section}

## 핵심 원칙
1. **깊은 추론 + 계획 따르기**: 위 계획을 참고하면서 사용자의 장기 목표와 현재 상태를 연결지어 생각하세요.
2. **도구 사용 규칙**: 혜택 질문 → check_benefit_eligibility 우선. 저축 → calculate_savings_plan. 통계 → get_gunsan_youth_stats.
   취업 통계 category를 섞지 말 것: 어려움%=employment_difficulty(군산), 취업자 수=employment_count(전북 분기평균), 둘 다=employment.
3. **상태 업데이트**: 대화 중 알게 된 새로운 사실은 내부적으로 기억하고, 가능하면 상태를 개선하는 방향으로 유도하세요.
4. **답변 품질**: 친근 + 구체적 숫자 + 실행 가능한 다음 단계 + 근거 제시.
5. **정직성 (필수)**: 도구 결과의 `disclaimer`·`data_source`·`from_db`·`is_fallback`·`source` 필드를 존중하세요.
   - 혜택 매칭은 **추천 점수**이지 공식 신청 가능 확정이 아닙니다. 폴백이면 명시하세요.
   - 통계는 DB 수치만 인용하고, 없는 값은 지어내지 마세요. 연도·출처를 함께 말하세요.

사용자의 전체 맥락을 이해하고, 단기 질문에만 답하지 말고 장기적으로 이 사용자의 목표에 어떻게 기여할지 고려하세요.
최종 답변은 자연스럽고 전문가처럼 작성하세요. "저는 AI입니다" 같은 말 금지.
"""

def _anthropic_tools():
    return [{"name":t["name"],"description":t["description"],"input_schema":{"type":"object","properties":t["properties"],"required":t["required"]}} for t in _BASE_TOOLS]

def _openai_tools():
    return [{"type":"function","function":{"name":t["name"],"description":t["description"],"parameters":{"type":"object","properties":t["properties"],"required":t["required"]}}} for t in _BASE_TOOLS]

def _google_declarations():
    if _genai is None:
        return []
    TYPE_MAP={"integer":_genai.protos.Type.INTEGER,"string":_genai.protos.Type.STRING,"boolean":_genai.protos.Type.BOOLEAN}
    out=[]
    for t in _BASE_TOOLS:
        props={}
        for pname,pdef in t["properties"].items():
            kw={"type":TYPE_MAP.get(pdef["type"],_genai.protos.Type.STRING),"description":pdef.get("description","")}
            if "enum" in pdef: kw["enum"]=pdef["enum"]
            props[pname]=_genai.protos.Schema(**kw)
        out.append(_genai.protos.FunctionDeclaration(name=t["name"],description=t["description"],parameters=_genai.protos.Schema(type=_genai.protos.Type.OBJECT,properties=props,required=t["required"])))
    return out

def run_anthropic(user_message, key):
    if not (ANTHROPIC_OK and key and _anthropic is not None):
        return "Anthropic을 사용할 수 없습니다.", []
    client=_anthropic.Anthropic(api_key=key)
    messages=[{"role":"user","content":user_message}]
    tool_steps=[]
    while True:
        resp=client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=get_system_prompt(),  # uses current agent plan
            tools=_anthropic_tools(),
            messages=messages,
            temperature=0.3,   # 추론 안정성 향상 (낮을수록 일관됨)
        )
        if resp.stop_reason=="tool_use":
            messages.append({"role":"assistant","content":resp.content})
            results=[]
            for block in resp.content:
                if block.type=="tool_use":
                    out=execute_tool(block.name,block.input)
                    tool_steps.append({"tool":block.name,"input":block.input,"output":json.loads(out)})
                    results.append({"type":"tool_result","tool_use_id":block.id,"content":out})
            messages.append({"role":"user","content":results})
        else:
            return "".join(b.text for b in resp.content if hasattr(b,"text")),tool_steps

def run_openai(user_message, key, model="gpt-4o", base_url=None):
    if not (OPENAI_OK and key and _OpenAI is not None):
        return "OpenAI 호환 provider를 사용할 수 없습니다 (키 또는 라이브러리).", []
    client = _OpenAI(api_key=key, base_url=base_url) if base_url else _OpenAI(api_key=key)
    messages=[{"role":"system","content":get_system_prompt()},{"role":"user","content":user_message}]  # uses session plan
    tool_steps=[]
    while True:
        resp=client.chat.completions.create(
            model=model,
            messages=messages,
            tools=_openai_tools(),
            tool_choice="auto",
            temperature=0.3,      # 추론 품질 안정화
            top_p=0.9,
        )
        choice=resp.choices[0]
        if choice.finish_reason=="tool_calls":
            messages.append(choice.message)
            for tc in choice.message.tool_calls:
                inp=json.loads(tc.function.arguments)
                out=execute_tool(tc.function.name,inp)
                tool_steps.append({"tool":tc.function.name,"input":inp,"output":json.loads(out)})
                messages.append({"role":"tool","tool_call_id":tc.id,"content":out})
        else:
            return choice.message.content or "",tool_steps

def run_google(user_message, key, model="gemini-2.0-flash"):
    if not (GOOGLE_OK and key and _genai is not None):
        return "Google Gemini를 사용할 수 없습니다 (google-generativeai 패키지 또는 API 키 필요).", []
    _genai.configure(api_key=key)

    def _try_model(mname):
        gm = _genai.GenerativeModel(
            model_name=mname,
            system_instruction=get_system_prompt(),  # pulls current plan from session
            tools=[_genai.protos.Tool(function_declarations=_google_declarations())],
            generation_config={
                "temperature": 0.3,   # 추론 안정성을 위해 낮춤
                "top_p": 0.9,
                "max_output_tokens": 2000,
            }
        )
        c = gm.start_chat(enable_automatic_function_calling=False)
        r = c.send_message(user_message)
        return c, r

    chat = None
    response = None
    used_model = model
    try:
        chat, response = _try_model(model)
    except Exception as e:
        err = str(e)
        if "404" in err or "not found" in err.lower() or "not supported" in err.lower():
            fallback = "gemini-2.0-flash"
            if model != fallback:
                try:
                    chat, response = _try_model(fallback)
                    used_model = fallback
                except Exception as e2:
                    return f"Google 모델 오류 ({model}): {err}\n대체 모델({fallback})도 실패: {e2}", []
            else:
                return f"Google 모델을 찾을 수 없습니다: {model}\n사용 가능한 모델 목록은 AI Studio > Model list에서 확인하세요.", []
        else:
            return f"Google 호출 오류: {err}", []

    # Tool calling loop
    tool_steps = []
    while True:
        fn_calls = [p.function_call for p in response.candidates[0].content.parts if getattr(p.function_call, "name", None)]
        if not fn_calls:
            break
        fn_responses = []
        for fc in fn_calls:
            inp = dict(fc.args)
            out = execute_tool(fc.name, inp)
            tool_steps.append({"tool": fc.name, "input": inp, "output": json.loads(out)})
            fn_responses.append(_genai.protos.Part(function_response=_genai.protos.FunctionResponse(name=fc.name, response={"result": json.loads(out)})))
        response = chat.send_message(fn_responses)

    text = "".join(p.text for p in response.candidates[0].content.parts if hasattr(p, "text"))
    return text, tool_steps

# Core tool labels from finfit_youth.tools + agent internal step labels
TOOL_LABELS = {
    **_CORE_TOOL_LABELS,
    "_internal_reason": "🧠 내부 정리",
    "_internal_assess_coverage": "🧭 정보 충분성 점검",
    "_internal_structure_findings": "📐 결과 정리",
    "_internal_cross_verify": "✅ 결과 교차 확인",
    "_internal_prepare_synthesis": "✍️ 답변 준비",
    "_internal_clarify_intent": "❓ 의도 확인 안내",
    "_agent_plan": "📋 조회 계획",
}

def get_dynamic_google_models(key):
    """
    Gemini API에서 현재 사용 가능한 모든 모델을 동적으로 불러옵니다.
    'generateContent'를 지원하는 Gemini 모델만 필터링.
    유지보수를 쉽게 하기 위해 하드코딩을 최소화하고 API 결과를 직접 사용.
    """
    # 안전한 fallback (API 호출 실패 시)
    fallback = [
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
        "gemini-2.0-flash-thinking-exp",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
    ]

    if not (key and GOOGLE_OK):
        return fallback[:2]

    try:
        _genai.configure(api_key=key)
        available = []
        for m in _genai.list_models():
            methods = getattr(m, "supported_generation_methods", [])
            if "generateContent" in methods:
                name = m.name.replace("models/", "")
                if name.startswith("gemini"):
                    available.append(name)

        if available:
            # 최신 모델 우선 정렬 (2.0 > 1.5, thinking 모델은 뒤로)
            def sort_key(name):
                if "2.0" in name or "2.5" in name:
                    base = 100
                elif "1.5" in name:
                    base = 50
                else:
                    base = 10
                if "thinking" in name.lower() or "exp" in name.lower():
                    base -= 5  # experimental은 약간 뒤로
                if "lite" in name.lower() or "8b" in name.lower():
                    base -= 1
                return -base   # 높은 값이 앞에 오도록 음수

            sorted_models = sorted(set(available), key=sort_key)
            return sorted_models   # **모든** 사용 가능한 모델 반환 (사용자가 직접 선택)
        return fallback
    except Exception as e:
        # API 호출 실패 시 (키 권한, rate limit, 네트워크 등)
        # 진단 expander에서 원인을 볼 수 있게 하되, UI는 계속 동작
        return fallback


def run_demo(user_message):
    """
    API 키 없이도 동작하는 로컬 데모.
    순수 구현: finfit_youth.demo_mode (가정 노출 · wants_* 정렬).
    """
    from finfit_youth.demo_mode import run_demo_turn

    def _rec(field, value, reason):
        AGENT.record_assumption(field, value, reason, "demo_default")

    return run_demo_turn(
        user_message,
        state=AGENT.state,
        execute_tool=execute_tool,
        record_assumption=_rec,
    )


# Init chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

DEMO_MODE = False  # will be overridden inside sidebar

with st.sidebar:
    st.header("⚙️ 설정")

    provider_options = []
    # 키가 있으면 옵션에 추가 (라이브러리는 실행 시점에 확인)
    if KEYS.get("Google"):
        provider_options.append("🔵 Google (Gemini)")
    if KEYS.get("Groq"):
        provider_options.append("⚡ Groq (무료)")
    if KEYS.get("Mistral"):
        provider_options.append("🌊 Mistral (무료)")
    if KEYS.get("OpenAI"):
        provider_options.append("🟢 OpenAI")
    if KEYS.get("Anthropic"):
        provider_options.append("🟣 Anthropic")

    # missing list is mostly replaced by the detailed diagnosis expander below
    # (kept minimal to avoid duplicate noise)

    # === 진단 정보 (키가 왜 안 잡히는지 확인용) ===
    with st.expander("🔍 키/라이브러리 진단 (클릭해서 확인)", expanded=(len(provider_options) == 0)):
        import sys
        st.caption(f"Python: {sys.executable}")
        st.markdown("**감지된 AI 키 (마스킹):**")
        for name, val in KEYS.items():
            if val:
                masked = val[:6] + "..." + val[-4:] if len(val) > 12 else val
                st.success(f"✅ {name}: {masked}")
            else:
                st.error(f"❌ {name}: 없음 (None)")
        st.markdown("**라이브러리 로드 상태:**")
        st.write(f"- google.generativeai (Gemini): {'✅' if GOOGLE_OK else '❌'}")
        st.write(f"- openai (Groq/Mistral/OpenAI): {'✅' if OPENAI_OK else '❌'}")
        st.write(f"- anthropic: {'✅' if ANTHROPIC_OK else '❌'}")
        if len(provider_options) == 0:
            st.warning("→ 위에서 키가 보이는데도 provider_options가 비었다면, 해당 라이브러리가 설치되지 않았을 수 있습니다.")
            st.code("pip install -r requirements.txt\n# 또는\npip install openai google-generativeai anthropic")

    DEMO_MODE = len(provider_options) == 0

    if DEMO_MODE:
        has_any_key = any(KEYS.get(k) for k in ["Google", "Groq", "Mistral", "OpenAI", "Anthropic"])
        if has_any_key:
            st.warning("⚠️ 키는 감지됐지만 라이브러리가 로드되지 않아 **데모 모드**로 동작합니다. 진단을 확인하세요.")
        else:
            st.warning("⚠️ 사용 가능한 AI Provider 키가 없어 **데모 모드**로 동작합니다. (로컬 도구만 사용)")
        with st.expander("키 설정 방법 (선택)"):
            st.markdown("""
            실제 AI 응답을 받으려면 requirements.txt 설치 후 Streamlit 재시작하세요.
            - Groq (무료 추천): console.groq.com
            """)
        provider = "🔵 데모 (로컬)"
        model_selected = None
    else:
        provider = st.selectbox("AI Provider", provider_options)
        model_selected = None
        if "Google" in (provider or ""):
            google_key = KEYS.get("Google")
            # 세션 캐시로 list_models() 반복 호출 방지 (유지보수성 ↑)
            cache_key = f"gemini_models_{google_key[:10] if google_key else 'none'}"
            if cache_key not in st.session_state:
                st.session_state[cache_key] = get_dynamic_google_models(google_key)

            google_models = st.session_state[cache_key]

            # 모델 목록 새로고침 버튼 (전체 목록을 API에서 불러오므로 유용)
            c1, c2 = st.columns([5, 1])
            with c1:
                model_selected = st.selectbox(
                    "모델 (Gemini API에서 실시간 조회된 전체 목록)",
                    google_models,
                    index=0,
                    help="API에서 직접 불러온 모든 사용 가능 모델. pro 계열이 추론 품질이 더 좋음. flash 계열이 빠름."
                )
            with c2:
                if st.button("↻", key="refresh_gemini_models", help="모델 목록 새로 불러오기"):
                    if cache_key in st.session_state:
                        del st.session_state[cache_key]
                    st.rerun()
        elif "Groq" in (provider or ""):
            # 추론 품질을 위해 70b 모델을 기본 추천
            groq_models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
            model_selected = st.selectbox("모델", groq_models, index=0)
            st.caption("⚡ Groq는 매우 빠름. 70b 모델이 추론 품질이 훨씬 좋음 (추천)")
        elif "Mistral" in (provider or ""):
            mistral_models = ["mistral-large-latest", "mistral-small-latest", "open-mistral-7b"]
            model_selected = st.selectbox("모델", mistral_models, index=0)
            st.caption("🌊 mistral-large가 추론 품질 최고 (무료 tier는 small 제한 있음)")
        elif "OpenAI" in (provider or ""):
            model_selected = st.selectbox("모델", ["gpt-4o-mini", "gpt-4o"])
        elif "Anthropic" in (provider or ""):
            model_selected = "claude-sonnet-4-20250514"
            st.caption("Anthropic Claude")

    st.divider()
    st.markdown("**🔧 사용 가능한 도구**")
    st.markdown("🔍 `check_benefit_eligibility` — 온통청년 정책 캐시 매칭 (**추천 ≠ 자격 확정**)")
    st.markdown("📊 `get_gunsan_youth_stats` — 군산 통계 (6페이지·동일 `gunsan_stats`, 추정 금지)")
    st.markdown("💰 `calculate_savings_plan` — 저축 계획 계산")
    st.caption(
        "혜택: youth_cache 스냅샷 · 폴백 시 명시. 통계: gunsan_youth_data.db · 도구 JSON에 disclaimer 포함."
    )
    with st.expander("⚠️ 도구 출처·한계", expanded=False):
        from finfit_youth.trust_copy import benefits_trust_markdown, stats_trust_markdown
        st.markdown("**혜택**")
        st.markdown(benefits_trust_markdown())
        st.markdown("**통계**")
        st.markdown(stats_trust_markdown())

    # 성능 팁
    with st.expander("💡 AI 추론 성능 팁", expanded=False):
        st.markdown("""
        - **품질 우선**: Gemini pro 계열 또는 Groq 70b 모델 사용
        - **속도 우선**: Gemini flash 또는 Groq 8b/9b
        - Temperature 0.3으로 설정되어 있어 일관된 답변
        - 모델 목록은 실시간 API 조회 → 새 모델 나오면 자동 반영
        """)
    st.divider()

    # 현재 AI가 알고 있는 사용자 상태 표시 (학습 환경 시각화)
    with st.expander("🧠 AI가 학습한 사용자 상태 (UserContext + Memory)", expanded=False):
        uc = getattr(AGENT, "last_user_context", None)
        if uc is not None:
            st.caption(f"**UserContext**: {uc.to_context_string()}")
            miss_b = uc.missing_for_benefits()
            miss_s = uc.missing_for_savings()
            if miss_b or miss_s:
                st.warning(
                    "미입력 필드는 도구 호출 시 **가정**으로 채워질 수 있습니다. "
                    f"혜택: {miss_b or '없음'} · 저축: {miss_s or '없음'}"
                )
            if uc.provenance_lines():
                st.markdown("**필드 출처**")
                st.markdown("\n".join(uc.provenance_lines()))
        else:
            st.caption(f"**현재 상태**: {AGENT.state.to_context_string()}")
        mem_ctx = AGENT.memory.get_relevant_context()
        if mem_ctx and "아직" not in mem_ctx:
            st.markdown("**장기 기억**")
            st.text(mem_ctx[:800])
        else:
            st.caption("아직 충분한 장기 기억이 쌓이지 않았습니다.")

    st.markdown("**💬 예시 질문**")
    examples = [
        "나 25살 취준생, 군산 거주 무주택이야. 받을 수 있는 혜택 다 알려줘.",
        "월급 230만원인데 저축 어떻게 해야 해?",
        "군산시 청년 취업 상황 어때?",
        "창업하려는 26살인데 혜택이랑 저축 계획 같이 알려줘."
    ]
    for ex in examples:
        if st.button(ex, key=f"ex_{hash(ex)}", use_container_width=True):
            st.session_state["prefill"] = ex
            st.rerun()
    st.write("---")
    st.markdown("**📑 대화 기록 지우기**")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state["chat_history"] = []
        st.rerun()

# Sidebar가 끝난 후 안전하게 DEMO_MODE 확정
if "DEMO_MODE" not in locals() or DEMO_MODE is None:
    DEMO_MODE = "데모" in str(locals().get("provider", ""))

# === Main chat UI (outside sidebar) ===
# H3/H4: always-visible one-liner — which session sources feed the agent this load
if _uc is not None and getattr(_uc, "sources", None):
    _src = _uc.sources or {}
    _order = (
        "age",
        "income_level",
        "employment_status",
        "has_house",
        "monthly_income",
        "savings_level",
        "first_goal",
    )
    _bits = [f"{k}←{_src[k]}" for k in _order if k in _src]
    if _bits:
        st.caption("📎 **이번 AI 로드 프로필 출처:** " + " · ".join(_bits))

# Render previous messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg.get("content", ""))
        if msg.get("tool_steps"):
            steps = msg["tool_steps"]
            chain = " → ".join(TOOL_LABELS.get(s["tool"], s["tool"]) for s in steps)
            with st.expander(f"🔧 Agent 판단 과정: {chain}", expanded=False):
                for i, step in enumerate(steps, 1):
                    label = TOOL_LABELS.get(step['tool'], step['tool'])
                    st.markdown(f"**Step {i}: {label}**")
                    if step['tool'] == "_agent_plan":
                        # Special pretty display for the agent's research plan
                        ptext = step.get("output", {}).get("plan_text", "")
                        st.text(ptext[:1200] if ptext else "Plan details in agent state.")
                        substeps = step.get("output", {}).get("steps", [])
                        if substeps:
                            st.caption("Planned actions:")
                            for ss in substeps:
                                st.markdown(f"- {ss.get('tool')}: {ss.get('purpose')}")
                    elif step['tool'].startswith("_internal"):
                        # Nicer for various CoALA internal actions
                        out = step.get("output", {})
                        st.caption(out.get("reason", "Internal CoALA action"))
                        preview = out.get("draft_context_preview") or out.get("summary", "")
                        st.text(preview[:900])
                        if "verified" in out or "issues" in out:
                            st.caption(f"Verified: {out.get('verified', [])} | Issues: {out.get('issues', [])}")
                        if "verified" in out or "issues" in out:
                            st.caption(f"Verified: {out.get('verified', [])} | Issues: {out.get('issues', [])}")
                    else:
                        c1, c2 = st.columns(2)
                        c1.caption("입력 (Agent 판단)"); c1.json(step.get("input", {}))
                        c2.caption("출력 (Tool/내부 결과)"); c2.json(step.get("output", {}))
                    if i < len(steps):
                        st.divider()

# Input handling (supports example buttons via prefill)
prefill = st.session_state.pop("prefill", None)
user_input = st.chat_input("질문을 입력하세요 (혜택, 저축, 통계 등)...")

if prefill:
    user_input = prefill

if user_input:
    # Record + show user message
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Generate assistant reply
    with st.chat_message("assistant"):
        spinner_name = (provider or "AI").split("(")[0].strip() if "provider" in locals() else "AI"
        if DEMO_MODE or "데모" in str(provider or ""):
            spinner_name = "데모"

        # === Pure agent-driven deep research loop (ReAct interleaved + Reflexion reflection + CoALA internal actions) ===
        # research_step is the single source of truth for decisions: agent decides tool / internal / synthesize each turn.
        # Page is a thin executor + renderer. No manual step lists or duplicate reflect loops.
        # Agent owns full Observe (state/mem/trajectory) - Plan/Refine (critique) - Decide - (internal or external) - Reflect.
        research_plan = AGENT.deep_research(user_input)
        plan_result = research_plan.get("plan", {})
        st.session_state["_current_agent_plan"] = plan_result
        # Seed the steps display with the agent's explicit initial plan (deep research transparency)
        plan_steps_display = [{"tool": "_agent_plan", "input": {}, "output": {"plan_text": plan_result.get("plan_text", ""), "steps": plan_result.get("steps", []) }}]

        with st.spinner(f"🤖 {spinner_name} 딥리서치 중..."):
            answer = ""
            steps = plan_steps_display[:]  # start with agent's declared plan for visibility
            agent_results = []  # observations fed back to research_step (agent ingests inside)

            try:
                prov = (provider or "")

                from finfit_youth.grounded_answer import (
                    try_grounded_answer,
                    grounded_preamble_for_ui,
                    plan_external_tools_complete,
                )

                # Clarify / empty plan: grounded immediately (no prepare_synthesis theater)
                grounded = try_grounded_answer(
                    user_input,
                    agent_results,
                    state=AGENT.state,
                    plan=plan_result if isinstance(plan_result, dict) else {},
                )
                early_grounded = bool(
                    grounded.get("skip_llm")
                    and grounded.get("answer")
                    and plan_external_tools_complete(plan_result, agent_results)
                    and not (plan_result.get("steps") or [])
                )

                # Clean while: sole driver is AGENT.research_step
                max_rounds = 12  # safety; full pipeline ~8 steps (execute+assess+structure+verify+prepare+synth)
                round_idx = 0
                synth_context = None
                while (not early_grounded) and round_idx < max_rounds:
                    round_idx += 1
                    decision = AGENT.research_step(user_input, previous_results=agent_results)
                    action = decision.get("action")

                    if action == "internal":
                        # CoALA internal action: agent thought without tool. Use specific type for display.
                        itype = decision.get("internal_type", "reason")
                        # Skip prepare/structure when tools already complete & answer is fully grounded
                        if itype in (
                            "prepare_synthesis",
                            "structure_findings",
                            "cross_verify",
                            "assess_coverage",
                        ) and plan_external_tools_complete(plan_result, agent_results):
                            g_chk = try_grounded_answer(
                                user_input,
                                agent_results,
                                state=AGENT.state,
                                plan=plan_result if isinstance(plan_result, dict) else {},
                            )
                            if g_chk.get("skip_llm") and g_chk.get("answer"):
                                grounded = g_chk
                                break
                        tool_key = f"_internal_{itype}"
                        int_out = {"summary": decision.get("summary", ""), "reason": decision.get("reason", ""), "type": itype}
                        steps.append({"tool": tool_key, "input": {}, "output": int_out})
                        # Feed back so next research_step sees it
                        agent_results.append({"tool": tool_key, "input": {}, "output": int_out})
                        continue

                    elif action == "synthesize":
                        # Prefer grounded over LLM context when tools fully determine the answer
                        g_chk = try_grounded_answer(
                            user_input,
                            agent_results,
                            state=AGENT.state,
                            plan=plan_result if isinstance(plan_result, dict) else {},
                        )
                        if g_chk.get("skip_llm") and g_chk.get("answer"):
                            grounded = g_chk
                            break
                        synth_context = decision.get("context") or AGENT.prepare_synthesis_context(user_input, agent_results)
                        break

                    elif action == "tool":
                        tname = decision.get("tool")
                        targs = decision.get("args", {})
                        try:
                            raw = execute_tool(tname, targs)
                            out = json.loads(raw)
                        except Exception as te:
                            out = {"error": str(te)}
                        step_rec = {"tool": tname, "input": targs, "output": out}
                        steps.append(step_rec)
                        agent_results.append(step_rec)
                        # Accuracy path: all planned tools done → grounded, skip further internals
                        if plan_external_tools_complete(plan_result, agent_results):
                            g_chk = try_grounded_answer(
                                user_input,
                                agent_results,
                                state=AGENT.state,
                                plan=plan_result if isinstance(plan_result, dict) else {},
                            )
                            if g_chk.get("skip_llm") and g_chk.get("answer"):
                                grounded = g_chk
                                break
                        continue

                    else:
                        # Unknown -> synthesize to guarantee answer
                        synth_context = decision.get("context") or AGENT.prepare_synthesis_context(user_input, agent_results)
                        break

                # If loop ended without explicit synthesize decision, force it
                if not synth_context and not (
                    grounded.get("skip_llm") and grounded.get("answer")
                ):
                    try:
                        synth_context = AGENT.prepare_synthesis_context(user_input, agent_results)
                    except Exception:
                        synth_context = f"[Agent deep research complete after {len(steps)} external + internal steps]\nState: {AGENT.state.to_context_string()}\n\nQuestion: {user_input}"

                # Final grounded attempt (covers late completion / re-check)
                if not (grounded.get("skip_llm") and grounded.get("answer")):
                    grounded = try_grounded_answer(
                        user_input,
                        agent_results,
                        state=AGENT.state,
                        plan=plan_result if isinstance(plan_result, dict) else {},
                    )
                used_grounded = bool(grounded.get("skip_llm") and grounded.get("answer"))
                answer = ""

                if used_grounded:
                    pre = grounded_preamble_for_ui(grounded)
                    answer = (pre + "\n\n" if pre else "") + grounded["answer"]
                    steps.append(
                        {
                            "tool": "_internal_grounded_answer",
                            "input": {"mode": grounded.get("mode"), "skip_llm": True},
                            "output": {
                                "reason": grounded.get("reason"),
                                "mode": grounded.get("mode"),
                            },
                        }
                    )
                elif (DEMO_MODE if "DEMO_MODE" in locals() else False) or "데모" in str(
                    prov or ""
                ):
                    answer, _ = run_demo(user_input)
                    try:
                        answer = AGENT.synthesize_final(answer, steps, user_input)
                    except Exception:
                        pass
                else:
                    # LLM only as last resort (grounded path covers single + multi + clarify)
                    synthesis_input = synth_context or f"""[Agent Research Complete]
Plan: {plan_result}
Findings: {json.dumps(steps, ensure_ascii=False)[:2000]}

[사용자 질문]
{user_input}

상태와 리서치 결과를 바탕으로 완전하고 실행 가능한 답변을 작성하세요. '더 정보 필요' 절대 금지. 누락 시 상태 가정 명시."""

                    if "Google" in prov:
                        _genai.configure(api_key=KEYS.get("Google"))
                        gm = _genai.GenerativeModel(
                            model_name=model_selected or "gemini-2.0-flash",
                            system_instruction=get_system_prompt()
                        )
                        resp = gm.generate_content(synthesis_input)
                        answer = "".join(p.text for p in resp.candidates[0].content.parts if hasattr(p, "text")) if resp.candidates else ""
                    elif "Groq" in prov or "Mistral" in prov or "OpenAI" in prov:
                        key = KEYS.get("Groq") if "Groq" in prov else (KEYS.get("Mistral") if "Mistral" in prov else KEYS.get("OpenAI"))
                        base = "https://api.groq.com/openai/v1" if "Groq" in prov else ("https://api.mistral.ai/v1" if "Mistral" in prov else None)
                        client = _OpenAI(api_key=key, base_url=base) if base else _OpenAI(api_key=key)
                        resp = client.chat.completions.create(
                            model=model_selected or ("llama-3.1-8b-instant" if "Groq" in prov else "mistral-small-latest" if "Mistral" in prov else "gpt-4o-mini"),
                            messages=[{"role": "user", "content": synthesis_input}],
                            temperature=0.3
                        )
                        answer = resp.choices[0].message.content or ""
                    elif "Anthropic" in prov:
                        client = _anthropic.Anthropic(api_key=KEYS.get("Anthropic"))
                        resp = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=2000,
                            system=get_system_prompt(),
                            messages=[{"role": "user", "content": synthesis_input}],
                            temperature=0.3
                        )
                        answer = "".join(b.text for b in resp.content if hasattr(b, "text"))
                    else:
                        answer = "Provider를 확인할 수 없습니다."

                # 최종 reflect + synthesis
                try:
                    AGENT.reflect_and_learn(user_input, steps, answer)
                    st.session_state.finfit_agent = AGENT
                except Exception:
                    pass

                # Grounded stats/savings already tool-faithful — skip LLM post-process that
                # can re-inject assumptions/benefit chatter; still run soft-check path lightly
                try:
                    if used_grounded:
                        # Template restates tools only — soft-check false positives
                        # (cache_size, URL digits) must not scold the user.
                        AGENT._last_answer_guard = {
                            "ok": True,
                            "unmatched": [],
                            "skipped": "grounded_template",
                        }
                    else:
                        answer = AGENT.synthesize_final(answer, steps, user_input)
                except Exception:
                    pass

                # Honesty: surface assumptions before the answer body (also embedded in synthesize_final)
                if getattr(AGENT, "assumptions", None):
                    with st.container():
                        st.info(AGENT.get_assumptions_text(for_user=True))

                # Clarify path: when agent skipped tools due to unclear intent
                try:
                    from finfit_youth.agent import CLARIFY_INTENT_TEXT

                    _plan = getattr(AGENT, "_last_plan", None) or {}
                    _clarified = any(
                        str(s.get("tool", "")).endswith("clarify_intent") for s in (steps or [])
                    ) or _plan.get("clarify")
                    if _clarified:
                        st.warning(
                            _plan.get("clarify_text")
                            or CLARIFY_INTENT_TEXT
                        )
                except Exception:
                    pass

                # Tool provenance: surface disclaimer from benefits/stats tool JSON
                try:
                    _trust_notes = []
                    for _s in steps or []:
                        _t = _s.get("tool")
                        _o = _s.get("output")
                        if isinstance(_o, str):
                            try:
                                _o = json.loads(_o)
                            except Exception:
                                _o = {}
                        if not isinstance(_o, dict):
                            _o = {}
                        if _t == "check_benefit_eligibility":
                            if _o.get("is_fallback"):
                                _trust_notes.append("혜택: 로컬 폴백 목록 사용 중 (캐시 매칭 아님)")
                            if _o.get("disclaimer"):
                                _trust_notes.append(f"혜택: {_o['disclaimer']}")
                            if _o.get("data_source"):
                                _trust_notes.append(
                                    f"혜택 출처: {_o['data_source']} · 캐시 {_o.get('cache_size', '?')}건"
                                    + (f" · {_o.get('cache_age_text')}" if _o.get("cache_age_text") else "")
                                )
                        if _t == "get_gunsan_youth_stats":
                            if _o.get("from_db") is False:
                                _trust_notes.append("통계: DB 미사용(폴백/오류) — 숫자를 확정으로 말하지 마세요")
                            if _o.get("disclaimer"):
                                _trust_notes.append(f"통계: {_o['disclaimer']}")
                            if _o.get("source"):
                                _trust_notes.append(f"통계 출처: {_o['source']}")
                    # unique preserve order
                    _seen = set()
                    _uniq = []
                    for n in _trust_notes:
                        if n not in _seen:
                            _seen.add(n)
                            _uniq.append(n)
                    if _uniq:
                        with st.expander("📎 이번 답변 데이터 출처·한계", expanded=True):
                            for n in _uniq[:6]:
                                st.caption(f"• {n}")
                except Exception:
                    pass

                st.markdown(answer)

                # Research depth (plain language)
                ext = len([s for s in steps if not str(s.get("tool", "")).startswith("_")])
                ints = len([s for s in steps if str(s.get("tool", "")).startswith("_internal")])
                depth_label = {
                    "shallow": "간단",
                    "standard": "보통",
                    "deep": "복합",
                }.get(getattr(AGENT, "_last_depth", None) or "", "")
                # last decision depth may be on agent if stored; fallback from plan size
                try:
                    depth_label = depth_label or {
                        "shallow": "간단", "standard": "보통", "deep": "복합"
                    }.get(AGENT.research_depth(user_input), "")
                except Exception:
                    pass
                st.caption(
                    f"조회 깊이: {depth_label or '-'} · 도구 {ext}회 · 정리 {ints}회 · "
                    f"가정 {len(getattr(AGENT, 'assumptions', []) or [])}건"
                )

                # Show the deep research decision chain for *this* turn immediately (plan + tools + internal)
                if steps:
                    chain = " → ".join(TOOL_LABELS.get(s["tool"], s["tool"]) for s in steps)
                    with st.expander(f"🔧 Agent 판단 과정 (이번 턴): {chain}", expanded=False):
                        for i, step in enumerate(steps, 1):
                            label = TOOL_LABELS.get(step['tool'], step['tool'])
                            st.markdown(f"**Step {i}: {label}**")
                            if step['tool'] == "_agent_plan":
                                ptext = step.get("output", {}).get("plan_text", "")
                                st.text((ptext or "")[:1100])
                                for ss in step.get("output", {}).get("steps", [])[:4]:
                                    st.caption(f"• {ss.get('tool')}: {ss.get('purpose')}")
                            elif step['tool'].startswith("_internal"):
                                out = step.get("output", {})
                                st.caption(out.get("reason", "Internal CoALA action"))
                                preview = out.get("draft_context_preview") or out.get("summary", "")
                                st.text(preview[:900])
                            else:
                                st.json({"input": step.get("input"), "output": step.get("output")})

                st.session_state.chat_history.append({"role": "assistant", "content": answer, "tool_steps": steps})

                # Offline turn log (JSONL) for manual cross-check — no API keys
                try:
                    from finfit_youth.turn_log import log_agent_turn

                    _mode = "demo" if (
                        (DEMO_MODE if "DEMO_MODE" in locals() else False)
                        or "데모" in str(prov or "")
                    ) else "live"
                    log_agent_turn(
                        query=user_input,
                        plan=plan_result if isinstance(plan_result, dict) else {},
                        tool_steps=steps,
                        answer=answer or "",
                        agent=AGENT,
                        mode=_mode,
                        provider=str(prov or "")[:40],
                    )
                except Exception:
                    pass

            except Exception as e:
                err = str(e)
                err_l = err.lower()
                # Google Gemini project deny — not a FinFit logic bug
                if (
                    "403" in err
                    or "permission_denied" in err_l
                    or "denied access" in err_l
                    or "project has been denied" in err_l
                ):
                    st.error(
                        "**LLM API 접근 거부 (403)** — FinFit 코드 오류가 아닙니다.\n\n"
                        "주로 **Google Gemini** 키가 연결된 프로젝트가 Generative Language API "
                        "사용을 거부당한 경우입니다 "
                        "(`Your project has been denied access`).\n\n"
                        "**바로 쓰는 방법**\n"
                        "1. 사이드바 **AI Provider**를 **Groq / Mistral / OpenAI / Anthropic** 으로 바꾸기\n"
                        "2. 또는 키 없이 **데모** 경로 (로컬 도구만)\n"
                        "3. Gemini를 쓰려면 AI Studio에서 **새 API 키·새 프로젝트** 후 "
                        "`GOOGLE_API_KEY` 교체\n"
                        "4. Google 정책/조직 차단이면 지원 문의 (앱에서 해제 불가)\n\n"
                        f"원문: `{err[:280]}`"
                    )
                    try:
                        demo_ans, demo_steps = run_demo(user_input)
                        demo_ans = (
                            "⚠️ **LLM 호출이 403으로 실패**해 **로컬 데모 도구 결과**로 대신 답합니다. "
                            "사이드바에서 Groq/Mistral 등으로 바꿔 보세요.\n\n"
                            + (demo_ans or "")
                        )
                        st.warning("LLM 실패 → 데모 폴백으로 도구 결과만 표시합니다.")
                        st.markdown(demo_ans)
                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "content": demo_ans,
                                "tool_steps": demo_steps,
                            }
                        )
                    except Exception:
                        st.session_state.chat_history.append(
                            {
                                "role": "assistant",
                                "content": f"오류가 발생했습니다: {err}",
                            }
                        )
                elif "auth" in err_l or "api_key" in err_l or "401" in err:
                    st.error("API Key 오류. `.streamlit/secrets.toml` 의 해당 키를 확인하세요.")
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": f"오류가 발생했습니다: {err}"}
                    )
                elif "quota" in err_l or "429" in err:
                    st.error(
                        "API 사용량 한도 초과. 잠시 후 다시 시도하거나 다른 Provider를 선택하세요."
                    )
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": f"오류가 발생했습니다: {err}"}
                    )
                else:
                    st.error(f"오류: {err}")
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": f"오류가 발생했습니다: {err}"}
                    )
