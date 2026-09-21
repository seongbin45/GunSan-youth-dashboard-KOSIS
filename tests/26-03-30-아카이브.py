"""
FinFit AI Agent - pages/finfit_agent.py
기존 app.py의 pages/ 폴더에 이 파일을 넣으면 됩니다.
필요 패키지: pip install anthropic
"""

import streamlit as st
import anthropic
import json
import sqlite3
import pandas as pd

# ─────────────────────────────────────────
# 0. 페이지 설정
# ─────────────────────────────────────────
st.set_page_config(page_title="FinFit AI Agent", page_icon="🤖", layout="wide")

st.title("🤖 FinFit AI Agent")
st.markdown("**자연어로 물어보세요.** Agent가 필요한 정보를 스스로 판단하고 찾아드립니다.")
st.divider()

# ─────────────────────────────────────────
# 1. Tool 구현체 (기존 app.py 로직 재활용)
# ─────────────────────────────────────────

LEVELS = {
    1: {"name": "여가 최우선",   "save": 0.05, "fix": 0.45, "leisure": 0.50},
    2: {"name": "여가 중심",     "save": 0.10, "fix": 0.50, "leisure": 0.40},
    3: {"name": "균형 여가형",   "save": 0.15, "fix": 0.55, "leisure": 0.30},
    4: {"name": "생활 균형형",   "save": 0.20, "fix": 0.55, "leisure": 0.25},
    5: {"name": "균형형",        "save": 0.25, "fix": 0.55, "leisure": 0.20},
    6: {"name": "저축 균형형",   "save": 0.30, "fix": 0.55, "leisure": 0.15},
    7: {"name": "저축 집중형",   "save": 0.40, "fix": 0.50, "leisure": 0.10},
    8: {"name": "고강도 저축",   "save": 0.50, "fix": 0.45, "leisure": 0.05},
    9: {"name": "극한 저축",     "save": 0.65, "fix": 0.35, "leisure": 0.00},
    10: {"name": "생존형 저축",  "save": 0.80, "fix": 0.20, "leisure": 0.00},
}


def tool_check_benefit_eligibility(age: int, income_level: str,
                                    employment_status: str, has_house: bool) -> dict:
    """기존 app.py의 혜택 매칭 로직을 함수화"""
    matched = []

    # ── 조건 변수 ──────────────────────────────────
    is_unemployed  = employment_status == "미취업"
    is_worker      = employment_status == "취업자"
    is_founder     = employment_status == "창업자"
    is_farmer      = employment_status == "농업종사자"
    is_over_limit  = income_level == "소득기준초과"

    if is_over_limit:
        is_u60 = is_u100 = is_u140 = is_u150 = is_u180 = False
    else:
        is_u60  = income_level == "60%이하"
        is_u100 = is_u60 or income_level == "100%이하"
        is_u140 = is_u100 or income_level == "140%이하"
        is_u150 = is_u140 or income_level == "150%이하"
        is_u180 = is_u150 or income_level == "180%이하"

    # ── 자산 형성 ──────────────────────────────────
    if 19 <= age <= 34 and not is_over_limit:
        matched.append({
            "category": "자산형성",
            "name": "청년미래적금 (2026 신설)",
            "benefit": "월 최대 50만원 × 3년, 정부기여금 포함 최대 2,200만원",
            "condition": "만 19~34세, 개인소득 6,000만원 이하"
        })

    if 19 <= age <= 34 and is_u180:
        matched.append({
            "category": "자산형성",
            "name": "청년도약계좌",
            "benefit": "5년간 월 최대 70만원 납입 → 최대 5,000만원 + 비과세",
            "condition": "만 19~34세, 가구소득 중위 250% 이하"
        })

    if 18 <= age <= 39 and is_u140 and (is_worker or is_founder):
        matched.append({
            "category": "자산형성",
            "name": "전북청년 함께두배적금",
            "benefit": "월 10만원 저축 시 지자체 1:1 매칭, 2년 후 두 배",
            "condition": "전북 거주 및 근로·창업 중인 만 18~39세"
        })

    # ── 주거 ───────────────────────────────────────
    if not has_house:
        if 19 <= age <= 34 and is_u60:
            matched.append({
                "category": "주거",
                "name": "청년월세 한시 특별지원",
                "benefit": "월 최대 20만원 × 24개월 (총 480만원)",
                "condition": "무주택, 청년가구 중위 60% 이하"
            })
        if 19 <= age <= 39 and not is_over_limit:
            matched.append({
                "category": "주거",
                "name": "전세보증금 반환보증 보증료 지원",
                "benefit": "이미 납부한 전세보증 보증료 최대 40만원 환급",
                "condition": "무주택, 연소득 5,000만원 이하"
            })
        if 18 <= age <= 39 and not is_over_limit:
            matched.append({
                "category": "주거",
                "name": "신혼·청년 전세자금 대출이자 지원",
                "benefit": "대출 잔액의 최대 2%, 연 최대 200만원",
                "condition": "가구 중위소득 180% 이하, 보증금 3억 이하"
            })

    # ── 구직·창업 ──────────────────────────────────
    if is_unemployed and 18 <= age <= 34 and is_u100:
        matched.append({
            "category": "구직",
            "name": "국민취업지원제도 1유형",
            "benefit": "구직촉진수당 월 60만원 × 6개월",
            "condition": "만 15~34세, 중위 120% 이하"
        })

    if is_unemployed and 18 <= age <= 39 and is_u150:
        matched.append({
            "category": "구직",
            "name": "전북형 청년활력수당",
            "benefit": "월 50만원 × 6개월 (총 300만원)",
            "condition": "군산 거주 미취업 청년, 중위 150% 이하"
        })

    if is_worker and 18 <= age <= 34:
        matched.append({
            "category": "구직",
            "name": "청년일자리도약장려금 (비수도권 근속)",
            "benefit": "2년간 최대 720만원 인센티브",
            "condition": "군산 등 비수도권 기업 6개월 이상 근속"
        })

    if 18 <= age <= 34:
        matched.append({
            "category": "구직",
            "name": "청년도전지원사업 (군산 청년뜰)",
            "benefit": "맞춤 프로그램 + 참여수당 최대 350만원",
            "condition": "구직단념 청년 포함 만 18~34세"
        })

    # ── 생활·복지 ──────────────────────────────────
    if 18 <= age <= 39:
        matched.append({
            "category": "생활복지",
            "name": "전국민 마음투자 지원사업",
            "benefit": "전문 심리상담 바우처 8회 제공",
            "condition": "만 18~39세, 보건소 또는 복지로 신청"
        })
        matched.append({
            "category": "생활복지",
            "name": "대중교통 K-패스",
            "benefit": "월 5.5만원 정액, 전국 대중교통 월 20만원 한도 무제한",
            "condition": "만 18~39세 청년 요금 적용"
        })

    return {
        "matched_count": len(matched),
        "benefits": matched,
        "summary": f"총 {len(matched)}개 혜택 해당"
    }


def tool_get_gunsan_youth_stats(category: str) -> dict:
    """KOSIS DB에서 군산 청년 통계 조회"""
    try:
        conn = sqlite3.connect("gunsan_youth_data.db")

        if category == "population":
            return {
                "data": "군산시 전체 인구 약 259,000명 중 청년(18~39세) 56,117명 (약 21.7%)",
                "source": "KOSIS 2024년 기준",
                "insight": "청년 인구 비중이 전국 평균보다 낮아 청년 유입 정책이 활발히 운영 중"
            }
        elif category == "employment":
            try:
                df = pd.read_sql("SELECT * FROM 전북특별자치도_연령별취업자_20211231", conn)
                youth_cols = [c for c in df.columns if any(x in c for x in ['15~', '20~', '25~', '30~', '35~'])]
                return {
                    "data": "전북 청년층(15~39세) 취업자 비중 약 28%",
                    "source": "KOSIS 전북 연령별 취업자 통계",
                    "insight": "청년 취업률이 전국 대비 낮아 각종 취업 장려금 혜택 활발"
                }
            except:
                return {"data": "취업 통계 데이터 로드 실패", "source": "KOSIS DB"}

        elif category == "housing":
            try:
                df = pd.read_sql("SELECT * FROM gunsan_youth_housing_data", conn)
                return {
                    "data": df.to_dict(orient="records")[:5],
                    "source": "KOSIS 군산시 청년 주택 소유 데이터",
                    "insight": "청년층 주택 소유율이 낮아 전세/월세 지원 정책 수혜 가능성 높음"
                }
            except:
                return {"data": "주거 통계 조회 실패", "source": "KOSIS DB"}

        elif category == "income":
            return {
                "data": "군산시 청년 평균 월 소득 약 210~250만원 (중소기업 기준)",
                "source": "KOSIS 임금 데이터 추정치",
                "insight": "전국 평균 대비 낮은 소득으로 청년 금융 혜택 수혜 대상자 多"
            }
        else:
            return {"error": f"알 수 없는 카테고리: {category}. population/employment/housing/income 중 선택"}

    except Exception as e:
        return {"error": str(e), "note": "DB 파일이 같은 폴더에 있어야 합니다"}
    finally:
        try:
            conn.close()
        except:
            pass


def tool_calculate_savings_plan(income: int, savings_level: int) -> dict:
    """기존 LEVELS 딕셔너리로 저축 계획 계산"""
    if not (1 <= savings_level <= 10):
        return {"error": "savings_level은 1~10 사이여야 합니다"}

    lv = LEVELS[savings_level]
    save_amt    = int(income * lv["save"])
    fix_amt     = int(income * lv["fix"])
    leisure_amt = int(income * lv["leisure"])

    yearly_save = save_amt * 12

    return {
        "level_name": lv["name"],
        "monthly_income": income,
        "monthly_savings": save_amt,
        "monthly_fixed": fix_amt,
        "monthly_leisure": leisure_amt,
        "yearly_savings": yearly_save,
        "savings_rate": f"{int(lv['save'] * 100)}%",
        "tip": f"1년 후 예상 저축액 {yearly_save:,}원. "
               f"청년도약계좌(월 {min(save_amt, 700000):,}원 납입) 연동 시 정부기여금 추가 수령 가능."
    }


# ─────────────────────────────────────────
# 2. Tool 정의 (Claude API 형식)
# ─────────────────────────────────────────

TOOLS = [
    {
        "name": "check_benefit_eligibility",
        "description": (
            "사용자의 나이, 소득 수준, 고용 상태, 주택 소유 여부를 입력받아 "
            "받을 수 있는 청년 금융 혜택 목록을 반환합니다. "
            "어떤 혜택이 있는지 물을 때 반드시 먼저 호출하세요."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "age": {
                    "type": "integer",
                    "description": "사용자의 만 나이"
                },
                "income_level": {
                    "type": "string",
                    "enum": ["60%이하", "100%이하", "140%이하", "150%이하", "180%이하", "소득기준초과"],
                    "description": "가구 소득 기준 중위소득 대비 수준"
                },
                "employment_status": {
                    "type": "string",
                    "enum": ["미취업", "취업자", "창업자", "농업종사자"],
                    "description": "현재 고용 상태"
                },
                "has_house": {
                    "type": "boolean",
                    "description": "주택 소유 여부 (true=유주택, false=무주택)"
                }
            },
            "required": ["age", "income_level", "employment_status", "has_house"]
        }
    },
    {
        "name": "get_gunsan_youth_stats",
        "description": (
            "KOSIS에서 수집한 군산시 청년 통계 데이터를 조회합니다. "
            "군산시 청년 현황, 취업률, 주거 상황, 소득 수준 등을 알고 싶을 때 사용합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["population", "employment", "housing", "income"],
                    "description": "조회할 통계 카테고리"
                }
            },
            "required": ["category"]
        }
    },
    {
        "name": "calculate_savings_plan",
        "description": (
            "월 소득과 저축 강도(1~10단계)를 입력받아 "
            "저축, 고정비, 여가비 예산 계획을 계산합니다. "
            "얼마나 저축해야 하는지, 예산을 어떻게 짜야 하는지 물을 때 사용합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "income": {
                    "type": "integer",
                    "description": "월 소득 또는 용돈 (원 단위)"
                },
                "savings_level": {
                    "type": "integer",
                    "description": "저축 강도 1(여가 최우선)~10(생존형 저축)"
                }
            },
            "required": ["income", "savings_level"]
        }
    }
]

# ─────────────────────────────────────────
# 3. Tool 실행 함수
# ─────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "check_benefit_eligibility":
        result = tool_check_benefit_eligibility(**tool_input)
    elif tool_name == "get_gunsan_youth_stats":
        result = tool_get_gunsan_youth_stats(**tool_input)
    elif tool_name == "calculate_savings_plan":
        result = tool_calculate_savings_plan(**tool_input)
    else:
        result = {"error": f"알 수 없는 tool: {tool_name}"}
    return json.dumps(result, ensure_ascii=False)


# ─────────────────────────────────────────
# 4. Agent 루프
# ─────────────────────────────────────────

def run_agent(user_message: str, api_key: str):
    """
    Claude tool_use 루프.
    tool_steps: Agent가 실행한 단계별 기록 (UI 표시용)
    """
    client = anthropic.Anthropic(api_key=api_key)

    messages = [{"role": "user", "content": user_message}]
    tool_steps = []  # Agent 판단 과정 기록

    system_prompt = """당신은 FinFit의 청년 금융 AI Agent입니다.
군산시에 거주하는 한국 청년들의 금융 생활을 돕습니다.

규칙:
1. 사용자의 상황을 파악하여 적절한 tool을 자율적으로 선택해 호출하세요.
2. 혜택 관련 질문은 반드시 check_benefit_eligibility를 먼저 호출하세요.
3. 저축/예산 관련 질문은 calculate_savings_plan을 호출하세요.
4. 군산시 현황이 필요하면 get_gunsan_youth_stats를 호출하세요.
5. 복합적인 질문은 여러 tool을 순서대로 호출해 종합 답변을 만드세요.
6. 답변은 친근하고 쉬운 말로, 핵심 숫자와 신청 방법을 포함하세요."""

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            tools=TOOLS,
            messages=messages
        )

        # tool_use가 있으면 실행
        if response.stop_reason == "tool_use":
            # 이번 턴의 Assistant 메시지 기록
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    # Agent 판단 과정 기록 (UI 표시용)
                    tool_steps.append({
                        "tool": block.name,
                        "input": block.input,
                        "tool_use_id": block.id
                    })

                    # Tool 실행
                    result_str = execute_tool(block.name, block.input)

                    # 실행 결과 저장
                    tool_steps[-1]["output"] = json.loads(result_str)

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str
                    })

            # Tool 결과를 messages에 추가
            messages.append({"role": "user", "content": tool_results})

        else:
            # end_turn: 최종 텍스트 답변
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return final_text, tool_steps


# ─────────────────────────────────────────
# 5. Streamlit UI
# ─────────────────────────────────────────

# API Key 입력 (사이드바)
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input(
        "Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="https://console.anthropic.com 에서 발급"
    )
    st.divider()
    st.markdown("**사용 가능한 Agent 도구**")
    st.markdown("🔍 `check_benefit_eligibility`\n청년 혜택 자격 확인")
    st.markdown("📊 `get_gunsan_youth_stats`\n군산시 청년 통계 조회")
    st.markdown("💰 `calculate_savings_plan`\n저축 계획 계산")
    st.divider()
    st.markdown("**예시 질문**")
    examples = [
        "나 25살 취준생인데 군산에 살아. 무주택이고 소득 없어. 받을 수 있는 혜택 다 알려줘.",
        "월급 230만원 받는데 저축 어떻게 해야 해?",
        "군산시 청년들 취업 상황 어때?",
        "창업하려는 26살인데 뭘 받을 수 있어?"
    ]
    for ex in examples:
        if st.button(ex, key=ex, use_container_width=True):
            st.session_state["prefill"] = ex

# 채팅 히스토리 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# 이전 대화 표시
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("tool_steps"):
            # Agent 판단 과정 표시
            with st.expander(f"🔧 Agent 판단 과정 ({len(msg['tool_steps'])}개 도구 사용)", expanded=False):
                for i, step in enumerate(msg["tool_steps"], 1):
                    tool_labels = {
                        "check_benefit_eligibility": "🔍 혜택 자격 확인",
                        "get_gunsan_youth_stats":    "📊 군산 통계 조회",
                        "calculate_savings_plan":    "💰 저축 계획 계산"
                    }
                    label = tool_labels.get(step["tool"], step["tool"])
                    st.markdown(f"**Step {i}: {label}**")
                    st.json(step["input"])
                    if "output" in step:
                        st.caption("결과:")
                        st.json(step["output"])
                    if i < len(msg["tool_steps"]):
                        st.divider()
        st.markdown(msg["content"])

# 입력창
prefill_value = st.session_state.pop("prefill", "")
user_input = st.chat_input("질문하세요. 예) 나 25살 취준생인데 받을 수 있는 혜택 알려줘")

if not user_input and prefill_value:
    user_input = prefill_value

if user_input:
    if not api_key:
        st.error("사이드바에서 Anthropic API Key를 입력해주세요.")
        st.stop()

    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Agent 실행
    with st.chat_message("assistant"):
        with st.spinner("🤖 Agent가 분석 중입니다..."):
            try:
                answer, tool_steps = run_agent(user_input, api_key)

                # Agent 판단 과정 표시
                if tool_steps:
                    tool_labels = {
                        "check_benefit_eligibility": "🔍 혜택 자격 확인",
                        "get_gunsan_youth_stats":    "📊 군산 통계 조회",
                        "calculate_savings_plan":    "💰 저축 계획 계산"
                    }
                    step_names = [tool_labels.get(s["tool"], s["tool"]) for s in tool_steps]
                    with st.expander(
                        f"🔧 Agent 판단 과정: {' → '.join(step_names)}",
                        expanded=True
                    ):
                        for i, step in enumerate(tool_steps, 1):
                            label = tool_labels.get(step["tool"], step["tool"])
                            st.markdown(f"**Step {i}: {label}**")
                            col_in, col_out = st.columns(2)
                            with col_in:
                                st.caption("입력 (Agent 판단)")
                                st.json(step["input"])
                            with col_out:
                                st.caption("출력 (Tool 결과)")
                                if "output" in step:
                                    st.json(step["output"])
                            if i < len(tool_steps):
                                st.divider()

                st.markdown(answer)

                # 히스토리 저장
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "tool_steps": tool_steps
                })

            except anthropic.AuthenticationError:
                st.error("API Key가 잘못되었습니다. 사이드바에서 다시 확인해주세요.")
            except Exception as e:
                st.error(f"오류 발생: {e}")
