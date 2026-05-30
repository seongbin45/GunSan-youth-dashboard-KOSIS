import streamlit as st
import json
import pandas as pd
import google.generativeai as genai

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
        return ["gemini-3.5-flash", "gemini-2.5-pro"]

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

st.set_page_config(page_title="FinFit AI Agent", page_icon="🤖", layout="wide")
st.title("🤖 FinFit AI Agent")
st.markdown("**자연어로 물어보세요.** Agent가 필요한 정보를 스스로 판단하고 찾아드립니다.")
st.divider()

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
    matched = []
    is_over = income_level == "소득기준초과"
    is_u60  = not is_over and income_level == "60%이하"
    is_u100 = is_u60  or (not is_over and income_level == "100%이하")
    is_u140 = is_u100 or (not is_over and income_level == "140%이하")
    is_u150 = is_u140 or (not is_over and income_level == "150%이하")
    is_u180 = is_u150 or (not is_over and income_level == "180%이하")
    is_un = employment_status == "미취업"
    is_wo = employment_status == "취업자"
    is_fo = employment_status == "창업자"
    if 19<=age<=34 and not is_over:
        matched.append({"category":"자산형성","name":"청년미래적금(2026신설)","benefit":"월 최대 50만원x3년, 최대 2,200만원","condition":"만 19~34세, 소득 6천만원 이하"})
    if 19<=age<=34 and is_u180:
        matched.append({"category":"자산형성","name":"청년도약계좌","benefit":"5년 월 최대 70만원, 최대 5,000만원+비과세","condition":"만 19~34세, 중위 250% 이하"})
    if 18<=age<=39 and is_u140 and (is_wo or is_fo):
        matched.append({"category":"자산형성","name":"전북청년 함께두배적금","benefit":"월 10만원 1:1 매칭, 2년 후 두 배","condition":"전북 거주 근로창업 청년"})
    if not has_house:
        if 19<=age<=34 and is_u60:
            matched.append({"category":"주거","name":"청년월세 한시 특별지원","benefit":"월 최대 20만원x24개월(총 480만원)","condition":"무주택, 중위 60% 이하"})
        if 19<=age<=39 and not is_over:
            matched.append({"category":"주거","name":"전세보증금 반환보증 보증료 지원","benefit":"최대 40만원 환급","condition":"무주택, 연소득 5천만원 이하"})
        if 18<=age<=39 and not is_over:
            matched.append({"category":"주거","name":"신혼청년 전세자금 대출이자 지원","benefit":"대출잔액 최대 2%, 연 최대 200만원","condition":"중위 180% 이하, 보증금 3억 이하"})
    if is_un and 18<=age<=34 and is_u100:
        matched.append({"category":"구직","name":"국민취업지원제도 1유형","benefit":"구직촉진수당 월 60만원x6개월","condition":"만 15~34세, 중위 120% 이하"})
    if is_un and 18<=age<=39 and is_u150:
        matched.append({"category":"구직","name":"전북형 청년활력수당","benefit":"월 50만원x6개월(총 300만원)","condition":"군산 거주 미취업, 중위 150% 이하"})
    if is_wo and 18<=age<=34:
        matched.append({"category":"구직","name":"청년일자리도약장려금","benefit":"2년간 최대 720만원","condition":"비수도권 기업 6개월 이상 근속"})
    if 18<=age<=39:
        matched.append({"category":"생활복지","name":"K-패스 무제한 정액권","benefit":"월 5.5만원 정액, 전국 대중교통 월 20만원 한도","condition":"만 18~39세"})
        matched.append({"category":"생활복지","name":"전국민 마음투자 지원사업","benefit":"전문 심리상담 바우처 8회","condition":"만 18~39세"})
    return {"matched_count":len(matched),"benefits":matched,"summary":f"총 {len(matched)}개 혜택 해당"}

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

def run_google(user_message, key, model="gemini-3.5-flash"):
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
            ### Streamlit secrets에서 키를 가져와 설정합니다.
            #genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
            
            #available_models = []
            #for m in genai.list_models():
                ### 텍스트 생성(generateContent)을 지원하는 모델만 걸러냅니다.
                #if 'generateContent' in m.supported_generation_methods:
                    ### 모델 이름에서 'models/' 부분을 제외하고 깔끔하게 저장합니다.
                    #clean_name = m.name.replace('models/', '')
                    #available_models.append(clean_name)
            
            ### 사이드바에 화면에 목록을 출력합니다.
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

prefill=st.session_state.pop("prefill","")
user_input=st.chat_input("질문하세요. 예) 나 25살 취준생인데 받을 수 있는 혜택 알려줘") or prefill

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
