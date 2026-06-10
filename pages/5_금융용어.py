import streamlit as st

import json
import pandas as pd
import google.generativeai as genai

from services.models import UserProfile
from services.policy_loader import load_policies
from services.recommendation import match_policies



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 1. ⚠️ 핵심 개선점: 캐싱 추가 (55분마다 한 번만 구글 인증 수행)
@st.cache_resource(ttl=3300)
def get_gspread_client():
    # Secrets에서 통째로 저장된 JSON 문자열을 가져옴
    json_string = st.secrets["gspread_json"]
    
    # 문자열을 파이썬 딕셔너리로 변환
    credentials = json.loads(json_string)
    
    # 구글 서비스 계정 인증 수행
    gc = gspread.service_account_from_dict(credentials)
    return gc

st.markdown(
   '<a href="https://docs.google.com/forms/d/e/1FAIpQLSco-O4cGhbt1iMOwrEkqX5Vt0-8ctAtCxM5Z6JjmFlP-Uqq-Q/viewform?usp=header" target="_blank"><button style="color: peach;">💌 설문 링크로 이동</button></a>', 
    unsafe_allow_html=True        
           )


# 의견 입력 창
user_feedback = st.text_area(
    "여러분의 생각을 자유롭게 적어주세요 👇", 
    placeholder="예: 이런 기능이 추가되면 좋겠어요 / 이 부분이 사용하기 조금 불편해요"
)

# 의견 남기기 버튼 (CTA)
if st.button("피드백 남기기", use_container_width=True):
    if user_feedback.strip() == "":
        st.warning("내용을 입력한 후 버튼을 눌러주세요! ⚠️")
    else:
        try:
            # 2. 구글 인증 및 시트 열기 (이제 캐시된 클라이언트를 빠르게 불러옴)
            gc = get_gspread_client()
            sh = gc.open_by_key(st.secrets["spreadsheet_id"])
            
            # 시트 이름으로 명확하게 지정하는 것을 권장하나, 인덱스(0)도 무방합니다.
            worksheet = sh.get_worksheet(0) 
            
            # 3. 데이터 추가
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([current_time, user_feedback])
            
            # 4. 제출 성공 완료 메시지 및 시각 효과
            st.balloons()
            st.success("""
            🎉 **소중한 피드백이 성공적으로 전달되었어요!**  
            보내주신 다정한 말씀과 조언은  
            서비스 개선에 적극 반영하겠습니다.  
            앞으로도 많은 기대 부탁드려요! 🙏
            """)
            
        except Exception as e:
            st.error(f"데이터 저장 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요: {e}")
            
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.write("---")

st.set_page_config(page_title="금융 용어 사전", page_icon="📚", layout="wide")
st.title("📚 필수 금융 용어")
st.caption("복잡한 용어를 쉽게 정리했어요")

terms = {
    "💰 저축·투자": [
        ("CMA 통장", "종합자산관리계좌. 하루만 맡겨도 이자가 붙는 통장. 비상금 보관에 최적."),
        ("ISA 계좌", "개인종합자산관리계좌. 예금·펀드·ETF를 한 통장에서 관리. 비과세 혜택."),
        ("ETF", "주식처럼 사고파는 펀드. 코스피200 같은 지수를 따라가는 상품. 분산투자 효과."),
        ("적금 vs 예금", "적금 = 매달 일정 금액 납입. 예금 = 한 번에 목돈 맡기기."),
        ("복리", "이자에 이자가 붙는 구조. 오래 투자할수록 폭발적 증가. 사회초년생이 가장 유리."),
        ("단리", "원금에만 이자가 붙는 구조. 대부분의 1~2년 적금 상품이 단리 적용."),
    ],
    "📊 신용·대출": [
        ("신용점수", "돈을 잘 갚는지 나타내는 점수 (0~1000점). 높을수록 대출 금리가 낮아짐."),
        ("DSR", "총부채원리금상환비율. 연소득 대비 모든 빚 상환액 비율. 대출 심사 기준."),
        ("마이너스 통장", "한도 내에서 자유롭게 빌리고 갚는 통장. 이자는 실제 사용 금액에만 적용."),
        ("연이율 vs 월이율", "연이율 12% = 월이율 약 1%. 대출 광고는 월이율로 속이는 경우 있으니 주의."),
        ("연체", "대출·카드값을 제때 못 갚는 것. 단 하루도 신용점수에 영향. 절대 주의."),
    ],
    "🏦 세금·연금": [
        ("연말정산", "1년간 낸 세금을 다시 계산해 더 낸 세금을 돌려받거나 추가 납부하는 절차."),
        ("국민연금", "노후를 위해 국가가 운영하는 연금. 직장인은 월급의 4.5% 자동 납부."),
        ("건강보험", "직장인은 월급의 약 3.5% 납부. 피부양자 등록 여부도 확인하세요."),
        ("소득공제 vs 세액공제", "소득공제 = 세금 계산 기준인 소득을 줄임. 세액공제 = 최종 세금을 직접 줄임."),
        ("IRP", "개인형 퇴직연금. 연 900만원까지 세액공제. 직장 퇴직금도 이 계좌로 수령."),
    ],
    "💳 일상 금융": [
        ("체크카드 vs 신용카드", "체크카드 = 잔액 내에서 사용._. 신용카드 = 나중에 결제._.  연말정산 공제율은 체크카드가 더 높음(30%)."),
        ("자동이체", "정해진 날짜에 자동으로 이체. 저축은 월급날 바로 자동이체 설정이 핵심."),
        ("비상금", "갑작스런 지출을 대비한 생활비 3~6개월치. 손대기 어려운 별도 통장에 보관."),
        ("페이 서비스", "카카오페이·네이버페이·토스 등. 편리하지만 소비 내역 관리가 중요."),
        ("환율", "원화와 외화의 교환 비율. 환율 높을수록 달러 구매 비용 증가."),
    ],
}

# 1. 상단 용어 검색 기능 (구조 통일 및 라벨 숨김)
keyword = st.text_input(
    label="용어 검색",
    placeholder="🔍 찾으시는 금융 용어를 입력해주세요 (예: CMA, DSR)",
    label_visibility="collapsed"  # 입력창 위쪽의 글자를 숨겨서 깔끔하게 만듭니다.
)

for category, items in terms.items():
    filtered = [(t, d) for t, d in items
                if not keyword or keyword.lower() in t.lower() or keyword.lower() in d.lower()]
    if not filtered:
        continue
    st.subheader(category)
    cols = st.columns(2)
    for i, (term, desc) in enumerate(filtered):
        with cols[i % 2]:
            # ✨ 수정된 부분: 어두운 배경(#2b2b36)과 밝은 글자색(#ffffff, #cccccc) 적용
            st.markdown(f"""
            <div style="background:#2b2b36; border-radius:10px; padding:14px 16px;
                        margin-bottom:10px; border-left:4px solid #667eea; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                <b style="color:#ffffff; font-size:1.1em;">{term}</b><br>
                <span style="color:#cccccc; font-size:0.95em; line-height: 1.5; display: inline-block; margin-top: 5px;">{desc}</span>
            </div>""", unsafe_allow_html=True)
    #st.divider()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 다크 모드에 맞춘 스타일 업데이트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<style>
    /* 배경을 투명하게 만들어 Streamlit 다크 모드 기본 테마를 따르도록 변경 */
    .main {
        background-color: transparent;
    }
    
    .header-container {
        text-align: center;
        margin-bottom: 2rem;
        padding-top: 2rem;
    }
    
    .header-title {
        font-size: 3em;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.2em;
    }
    
    .header-subtitle {
        font-size: 1.3em;
        color: #aaaaaa;
        font-weight: 500;
        margin-bottom: 2em;
    }
    
    /* 사용하지 않는 카드의 스타일도 다크 모드에 맞게 미리 세팅 */
    .feature-card {
        background: #1e1e24;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border-left: 6px solid;
        transition: all 0.3s ease;
        min-height: 350px;
        display: flex;
        flex-direction: column;
    }
    
    .feature-card:hover {
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.5);
        transform: translateY(-6px);
    }
    
    div[data-testid="stButton"] > button {
        width: 100%;
        font-size: 1.05em !important;
        font-weight: 600 !important;
        padding: 0.8em 1.5em !important;
        height: auto !important;
        min-height: 45px !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    
    hr {
        margin: 3rem 0;
        border: none;
        border-top: 2px solid #333333;
    }
    
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #888888;
        font-size: 0.95em;
        border-top: 1px solid #333333;
    }
    
    @media (max-width: 768px) {
        .header-title {
            font-size: 2.2em;
        }
        
        .header-subtitle {
            font-size: 1.1em;
        }
        
        .feature-card {
            min-height: 320px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# 한 번 불러온 목록은 24시간(86400초) 동안 기억하여 앱 속도를 빠르게 유지합니다.
@st.cache_data(show_spinner=False, ttl=86400)
def get_dynamic_google_models(api_key):
    try:
        genai.configure(api_key=api_key)
        available_models = []
        for m in genai.list_models():
            # 텍스트 생성용 모델만 필터링합니다.
            if 'generateContent' in m.supported_generation_methods:
                clean_name = m.name.replace('models/', '')
                available_models.append(clean_name)
        return available_models
    except Exception:
        # 만약 네트워크 오류 등으로 실패할 경우를 대비한 안전 장치(Fallback)입니다.
        return ["gemini-2.5-pro", "gemini-3.5-flash"]

try:
    import anthropic as _anthropic
    ANTHROPIC_OK = True
except ImportError:
    ANTHROPIC_OK = False

try:
    from openai import OpenAI as _OpenAI
    OPENAI_OK = True
except ImportError:
    OPENAI_OK = False

try:
    import google.generativeai as _genai
    GOOGLE_OK = True
except ImportError:
    GOOGLE_OK = False

st.divider() 
st.subheader("💬 더 궁금한 점이 있으신가요?")
st.caption("구체적인 상황을 알려주시면 맞춤형 정보를 찾아드릴게요!")

def _secret(key):
    try:
        return st.secrets[key]
    except (KeyError, FileNotFoundError):
        return None

KEYS = {
    "Anthropic": _secret("ANTHROPIC_API_KEY"),
    "OpenAI":    _secret("OPENAI_API_KEY"),
    "Google":    _secret("GOOGLE_API_KEY"),
    "Groq":    _secret("GROQ_API_KEY"),
    "Mistral": _secret("MISTRAL_API_KEY"),
}

LEVELS = {
    1: {"name":"여가 최우선",  "save":0.05,"fix":0.45,"leisure":0.50},
    2: {"name":"여가 중심",    "save":0.10,"fix":0.50,"leisure":0.40},
    3: {"name":"균형 여가형",  "save":0.15,"fix":0.55,"leisure":0.30},
    4: {"name":"생활 균형형",  "save":0.20,"fix":0.55,"leisure":0.25},
    5: {"name":"균형형",       "save":0.25,"fix":0.55,"leisure":0.20},
    6: {"name":"저축 균형형",  "save":0.30,"fix":0.55,"leisure":0.15},
    7: {"name":"저축 집중형",  "save":0.40,"fix":0.50,"leisure":0.10},
    8: {"name":"고강도 저축",  "save":0.50,"fix":0.45,"leisure":0.05},
    9: {"name":"극한 저축",    "save":0.65,"fix":0.35,"leisure":0.00},
    10:{"name":"생존형 저축",  "save":0.80,"fix":0.20,"leisure":0.00},
}

def _tool_check_benefit(age, income_level, employment_status, has_house):
    income_map = {
        "60%이하": 60,
        "100%이하": 100,
        "140%이하": 140,
        "150%이하": 150,
        "180%이하": 180,
        "소득기준초과": None,
    }
    employment_map = {
        "미취업": "job_seeker",
        "취업자": "worker",
        "창업자": "founder",
        "농업종사자": "farmer",
    }
    profile = UserProfile(
        age=int(age),
        employment_status=employment_map.get(employment_status, "job_seeker"),
        has_house=bool(has_house),
        region="군산시",
        median_income_percent=income_map.get(income_level),
    )
    matches = match_policies(profile, load_policies())
    benefits = [
        {
            "category": match.policy.category,
            "name": match.policy.name,
            "benefit": match.policy.benefit,
            "condition": ", ".join(match.reasons),
            "source": match.policy.source,
            "url": match.policy.url,
        }
        for match in matches
    ]
    return {"matched_count": len(benefits), "benefits": benefits, "summary": f"총 {len(benefits)}개 혜택 해당"}

def _tool_gunsan_stats(category):
    INFO = {
        "population":{"data":"군산시 전체 인구 약 259,000명 중 청년(18~39세) 56,117명 (약 21.7%)","source":"KOSIS 2024년 기준","insight":"청년 인구 비중이 전국 평균보다 낮아 청년 유입 정책 활발"},
        "employment":{"data":"전북 청년층(15~39세) 취업자 비중 약 28%","source":"KOSIS 전북 연령별 취업자 통계","insight":"청년 취업률이 전국 대비 낮아 취업 장려금 혜택 활발"},
        "housing":{"data":"군산시 청년층 주택 소유율 약 18% (전국 평균 22%보다 낮음)","source":"KOSIS 군산시 청년 주택 소유 데이터","insight":"청년층 주택 소유율 낮아 전세월세 지원 수혜 가능성 높음"},
        "income":{"data":"군산시 청년 평균 월 소득 약 210~250만원 (중소기업 기준)","source":"KOSIS 임금 데이터 추정치","insight":"전국 평균 대비 낮은 소득으로 청년 금융 혜택 수혜 대상자 多"},
    }
    return INFO.get(category, {"error":f"알 수 없는 카테고리: {category}"})

def _tool_savings_plan(income, savings_level):
    if not (1<=savings_level<=10):
        return {"error":"savings_level은 1~10 사이여야 합니다"}
    lv = LEVELS[savings_level]
    save = int(income*lv["save"])
    return {"level_name":lv["name"],"monthly_income":income,"monthly_savings":save,
            "monthly_fixed":int(income*lv["fix"]),"monthly_leisure":int(income*lv["leisure"]),
            "yearly_savings":save*12,"savings_rate":f"{int(lv['save']*100)}%",
            "tip":f"1년 후 예상 저축액 {save*12:,}원. 청년도약계좌 연동 시 정부기여금 추가 수령 가능."}

def execute_tool(name, inputs):
    dispatch={"check_benefit_eligibility":_tool_check_benefit,"get_gunsan_youth_stats":_tool_gunsan_stats,"calculate_savings_plan":_tool_savings_plan}
    fn=dispatch.get(name)
    if fn is None:
        return json.dumps({"error":f"알 수 없는 tool: {name}"},ensure_ascii=False)
    try:
        result=fn(**inputs)
    except TypeError as e:
        result={"error":str(e)}
    return json.dumps(result,ensure_ascii=False)

_BASE_TOOLS=[
    {"name":"check_benefit_eligibility","description":"사용자의 나이소득고용상태주택여부로 청년 금융 혜택 자격 확인. 혜택 관련 질문엔 반드시 먼저 호출.","properties":{"age":{"type":"integer","description":"만 나이"},"income_level":{"type":"string","description":"중위소득 기준","enum":["60%이하","100%이하","140%이하","150%이하","180%이하","소득기준초과"]},"employment_status":{"type":"string","description":"고용 상태","enum":["미취업","취업자","창업자","농업종사자"]},"has_house":{"type":"boolean","description":"주택 소유 여부"}},"required":["age","income_level","employment_status","has_house"]},
    {"name":"get_gunsan_youth_stats","description":"KOSIS 기반 군산시 청년 통계 조회. 현황취업주거소득 분석 시 사용.","properties":{"category":{"type":"string","description":"조회 카테고리","enum":["population","employment","housing","income"]}},"required":["category"]},
    {"name":"calculate_savings_plan","description":"월 소득과 저축 강도(1~10단계)로 예산 계획 계산. 저축예산 질문 시 사용.","properties":{"income":{"type":"integer","description":"월 소득 (원)"},"savings_level":{"type":"integer","description":"저축 강도 1(여가 최우선)~10(생존형 저축)"}},"required":["income","savings_level"]},
]

SYSTEM_PROMPT="""당신은 FinFit의 청년 금융 AI Agent입니다.
군산시에 거주하는 한국 청년들의 금융 생활을 돕습니다.
1. 사용자 상황을 파악하여 적절한 tool을 자율적으로 선택해 호출하세요.
2. 혜택 관련 질문은 반드시 check_benefit_eligibility를 먼저 호출하세요.
3. 저축예산 질문은 calculate_savings_plan을 호출하세요.
4. 군산 현황이 필요하면 get_gunsan_youth_stats를 호출하세요.
5. 복합 질문은 여러 tool을 순서대로 호출해 종합 답변을 만드세요.
6. 답변은 친근하고 쉬운 말로, 핵심 숫자와 신청 방법을 포함하세요."""

def _anthropic_tools():
    return [{"name":t["name"],"description":t["description"],"input_schema":{"type":"object","properties":t["properties"],"required":t["required"]}} for t in _BASE_TOOLS]

def _openai_tools():
    return [{"type":"function","function":{"name":t["name"],"description":t["description"],"parameters":{"type":"object","properties":t["properties"],"required":t["required"]}}} for t in _BASE_TOOLS]

def _google_declarations():
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

def run_anthropic(user_message,key):
    client=_anthropic.Anthropic(api_key=key)
    messages=[{"role":"user","content":user_message}]
    tool_steps=[]
    while True:
        resp=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=2000,system=SYSTEM_PROMPT,tools=_anthropic_tools(),messages=messages)
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
    # base_url 지정 시 Groq/Mistral 등 OpenAI 호환 Provider 재사용 가능
    client = _OpenAI(api_key=key, base_url=base_url) if base_url else _OpenAI(api_key=key)
    messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":user_message}]
    tool_steps=[]
    while True:
        resp=client.chat.completions.create(model=model,messages=messages,tools=_openai_tools(),tool_choice="auto")
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

def run_openai(user_message, key, model="gpt-4o", base_url=None):
    # base_url 지정 시 Groq/Mistral 등 OpenAI 호환 Provider 재사용 가능
    client = _OpenAI(api_key=key, base_url=base_url) if base_url else _OpenAI(api_key=key)
    messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":user_message}]
    tool_steps=[]
    while True:
        resp=client.chat.completions.create(model=model,messages=messages,tools=_openai_tools(),tool_choice="auto")
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

def run_google(user_message, key, model="gemini-2.5-pro"):
    _genai.configure(api_key=key)
    gem_model=_genai.GenerativeModel(model_name=model,system_instruction=SYSTEM_PROMPT,tools=[_genai.protos.Tool(function_declarations=_google_declarations())])
    chat=gem_model.start_chat(enable_automatic_function_calling=False)
    response=chat.send_message(user_message)
    tool_steps=[]
    while True:
        fn_calls=[p.function_call for p in response.candidates[0].content.parts if p.function_call.name]
        if not fn_calls: break
        fn_responses=[]
        for fc in fn_calls:
            inp=dict(fc.args)
            out=execute_tool(fc.name,inp)
            tool_steps.append({"tool":fc.name,"input":inp,"output":json.loads(out)})
            fn_responses.append(_genai.protos.Part(function_response=_genai.protos.FunctionResponse(name=fc.name,response={"result":json.loads(out)})))
        response=chat.send_message(fn_responses)
    text="".join(p.text for p in response.candidates[0].content.parts if hasattr(p,"text"))
    return text,tool_steps

TOOL_LABELS={"check_benefit_eligibility":"🔍 혜택 자격 확인","get_gunsan_youth_stats":"📊 군산 통계 조회","calculate_savings_plan":"💰 저축 계획 계산"}

with st.sidebar:
    st.header("⚙️ 설정")
    provider_options=[]
    if GOOGLE_OK and KEYS["Google"]:        provider_options.append("🔵 Google (Gemini)")
    ##if OPENAI_OK and KEYS["OpenAI"]:       provider_options.append("🟢 OpenAI (GPT-4o)")
    ##if ANTHROPIC_OK and KEYS["Anthropic"]: provider_options.append("🟣 Anthropic (Claude)")
    if OPENAI_OK   and KEYS["Groq"]:       provider_options.append("⚡ Groq (무료)")
    if OPENAI_OK   and KEYS["Mistral"]:    provider_options.append("🌊 Mistral (무료)")
    
    missing=[]
    if not (GOOGLE_OK and KEYS["Google"]):         missing.append("GOOGLE_API_KEY")
    ##if not (OPENAI_OK and KEYS["OpenAI"]):        missing.append("OPENAI_API_KEY")
    ##if not (ANTHROPIC_OK and KEYS["Anthropic"]): missing.append("ANTHROPIC_API_KEY")
    if not KEYS["Groq"]:                          missing.append("GROQ_API_KEY    (무료: console.groq.com)")
    if not KEYS["Mistral"]:                       missing.append("MISTRAL_API_KEY (무료tier: console.mistral.ai)")
    
    if missing:
        with st.expander("⚠️ 미설정 키"):
            st.markdown("아래 키가 `secrets.toml`에 없습니다:")
            for m in missing: st.code(m)
            st.markdown("**로컬**: `.streamlit/secrets.toml`\n**Cloud**: App settings → Secrets 탭")

    if not provider_options:
        st.error("사용 가능한 API Key가 없습니다.\nsecrets.toml 설정 후 재시작하세요.")
        st.stop()
 
    provider=st.selectbox("AI Provider",provider_options)
    model_selected=None
    if "OpenAI" in provider:
        model_selected=st.selectbox("모델",["gpt-4o","gpt-4o-mini","gpt-4-turbo"])
    elif "Groq" in provider:
        model_selected=st.selectbox("모델",["llama-3.3-70b-versatile","llama-3.1-8b-instant","gemma2-9b-it"])
        st.caption("⚡ Groq는 완전 무료입니다. (분당 요청수 제한 있음)")
    elif "Mistral" in provider:
        model_selected=st.selectbox("모델",["mistral-small-latest","open-mistral-7b","mistral-large-latest"])
        st.caption("🌊 mistral-small / open-mistral-7b 는 무료 tier입니다.")
    elif "Google" in provider:
        # 1. 등록된 구글 API 키를 가져옵니다.
        google_key = KEYS["Google"]
    
        # 2. 동적으로 사용 가능한 모델 목록을 불러옵니다.
        google_models = get_dynamic_google_models(google_key)
    
        # 3. 불러온 목록을 그대로 선택지(selectbox)에 넣습니다.
        model_selected = st.selectbox("모델", google_models)

    #elif "Google" in provider:
        #model_selected = st.selectbox("모델", ["gemini-3.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"])
     
    st.divider()
    st.markdown("**🔧 사용 가능한 도구**")
    st.markdown("🔍 `check_benefit_eligibility` — 청년 혜택 자격 확인")
    st.markdown("📊 `get_gunsan_youth_stats` — 군산시 청년 통계 조회")
    st.markdown("💰 `calculate_savings_plan` — 저축 계획 계산")
    st.divider()
    st.markdown("**💬 예시 질문**")
    examples=["나 25살 취준생, 군산 거주 무주택이야. 받을 수 있는 혜택 다 알려줘.","월급 230만원인데 저축 어떻게 해야 해?","군산시 청년 취업 상황 어때?","창업하려는 26살인데 혜택이랑 저축 계획 같이 알려줘."]
    for ex in examples:
        if st.button(ex,key=ex,use_container_width=True): st.session_state["prefill"]=ex
    st.write("---")
    st.markdown("**📑 대화 기록 지우기**")
    if st.button("🗑️ 대화 초기화",use_container_width=True):
        st.session_state["chat_history"]=[]
        st.rerun()
    st.write("---")

    ### --- [여기에 임시 테스트 코드 추가] ---
    #st.divider()
    #st.markdown("**👨‍💻 관리자 도구**")
    #if st.sidebar.button("🔍 [개발 유지 보수] 현시점 사용 가능한 구글 API 모델 목록 확인하기"):
        #import google.generativeai as genai
        #try:
            # Streamlit secrets에서 키를 가져와 설정합니다.
            #genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            
            #available_models = []
            #for m in genai.list_models():
                # 텍스트 생성(generateContent)을 지원하는 모델만 걸러냅니다.
                #if 'generateContent' in m.supported_generation_methods:
                    # 모델 이름에서 'models/' 부분을 제외하고 깔끔하게 저장합니다.
                    #clean_name = m.name.replace('models/', '')
                    #available_models.append(clean_name)
            
            # 사이드바에 화면에 목록을 출력합니다.
            #st.sidebar.success("사용 가능한 모델 목록:")
            #st.sidebar.write(available_models)
        #except Exception as e:
            #st.sidebar.error(f"목록을 불러오는 중 오류 발생: {e}")
    #st.divider()
    ### ----------------------------------

if "chat_history" not in st.session_state:
    st.session_state.chat_history=[]

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        if msg["role"]=="assistant" and msg.get("tool_steps"):
            steps=msg["tool_steps"]
            chain=" → ".join(TOOL_LABELS.get(s["tool"],s["tool"]) for s in steps)
            with st.expander(f"🔧 Agent 판단 과정: {chain}",expanded=False):
                for i,step in enumerate(steps,1):
                    st.markdown(f"**Step {i}: {TOOL_LABELS.get(step['tool'],step['tool'])}**")
                    c1,c2=st.columns(2)
                    c1.caption("입력 (Agent 판단)"); c1.json(step["input"])
                    c2.caption("출력 (Tool 결과)"); c2.json(step.get("output",{}))
                    if i<len(steps): st.divider()
        st.markdown(msg["content"])

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ✨ 이전에 만들었던 '스크롤형 + 우측 정렬 버튼' UI 연결 부분
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

prefill = st.session_state.pop("prefill", "")

# st.chat_input을 폼 구조로 완벽하게 대체했습니다.
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([6, 1])
    
    with col1:
        user_input = st.text_input(
            label="질문을 적어주세요.", 
            value=prefill,
            placeholder="여기에 전부 적어주세요",
            label_visibility="collapsed"
        )
        
    with col2:
        submit_button = st.form_submit_button(label="질문 보내기", use_container_width=True) or prefill

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.chat_history.append({"role":"user","content":user_input})
    with st.chat_message("assistant"):
        with st.spinner(f"🤖 {provider.split('(')[0].strip()} Agent 분석 중..."):
            try:
                if "Anthropic" in provider:
                    answer,steps=run_anthropic(user_input,KEYS["Anthropic"])
                elif "OpenAI" in provider:
                    answer,steps=run_openai(user_input,KEYS["OpenAI"],model_selected)
                elif "Google" in provider:
                    answer,steps=run_google(user_input,KEYS["Google"],model_selected)
                elif "Groq" in provider:
                    answer,steps=run_openai(user_input,KEYS["Groq"],model_selected,
                                            base_url="https://api.groq.com/openai/v1")
                elif "Mistral" in provider:
                    answer,steps=run_openai(user_input,KEYS["Mistral"],model_selected,
                                            base_url="https://api.mistral.ai/v1")
                else:
                    answer,steps="Provider를 선택할 수 없습니다.",[]
                if steps:
                    chain=" → ".join(TOOL_LABELS.get(s["tool"],s["tool"]) for s in steps)
                    with st.expander(f"🔧 Agent 판단 과정: {chain}",expanded=True):
                        for i,step in enumerate(steps,1):
                            st.markdown(f"**Step {i}: {TOOL_LABELS.get(step['tool'],step['tool'])}**")
                            c1,c2=st.columns(2)
                            c1.caption("입력 (Agent 판단)"); c1.json(step["input"])
                            c2.caption("출력 (Tool 결과)"); c2.json(step.get("output",{}))
                            if i<len(steps): st.divider()
                st.markdown(answer)
                st.session_state.chat_history.append({"role":"assistant","content":answer,"tool_steps":steps})
            except Exception as e:
                err=str(e)
                if "auth" in err.lower() or "api_key" in err.lower() or "401" in err:
                    st.error("API Key 오류. secrets.toml 설정을 확인하세요.")
                elif "quota" in err.lower() or "429" in err:
                    st.error("API 사용량 한도 초과. 잠시 후 다시 시도하세요.")
                else:
                    st.error(f"오류: {err}")


