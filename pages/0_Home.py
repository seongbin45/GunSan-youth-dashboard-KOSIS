import streamlit as st
import pandas as pd
import sqlite3  # 👈 이 녀석이 빠져 있어서 에러가 났던 겁니다!
import plotly.express as px

st.set_page_config(page_title="FinFit", page_icon="💰", layout="wide")

# ── 세션 초기화 ──────────────────────────────────────────────────────────────
if "income" not in st.session_state:
    st.session_state.income = 2000000
if "level" not in st.session_state:
    st.session_state.level = 5
if "expenses" not in st.session_state:
    st.session_state.expenses = []






st.markdown("""
<style>
    .main {
        background-color: #ffffff;
    }
    
    .header-container {
        text-align: center;
        margin-bottom: 2rem;
        padding-top: 2rem;
    }
    
    .header-title {
        font-size: 3em;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.2em;
    }
    
    .header-subtitle {
        font-size: 1.3em;
        color: #666666;
        font-weight: 500;
        margin-bottom: 2em;
    }
    
    .feature-card {
        background: white;
        border-radius: 16px;
        padding: 2.5rem 2rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        border-left: 6px solid;
        transition: all 0.3s ease;
        min-height: 350px;
        display: flex;
        flex-direction: column;
    }
    
    .feature-card:hover {
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
        transform: translateY(-6px);
    }
    
    .card-icon {
        font-size: 3.5em;
        margin-bottom: 1rem;
    }
    
    .card-title {
        font-size: 1.6em;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 0.8rem;
    }
    
    .card-description {
        font-size: 1em;
        color: #555555;
        line-height: 1.7;
        margin-bottom: 1.5rem;
        flex-grow: 1;
    }
    
    .card-features {
        background: linear-gradient(135deg, #f5f5f5 0%, #f9f9f9 100%);
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    
    .card-features-title {
        font-size: 0.9em;
        font-weight: 700;
        color: #333333;
        margin-bottom: 0.8rem;
        display: block;
    }
    
    .feature-item {
        font-size: 0.95em;
        color: #444444;
        margin-bottom: 0.5rem;
        padding-left: 1.5rem;
        position: relative;
    }
    
    .feature-item:before {
        content: "✓";
        position: absolute;
        left: 0;
        color: #4CAF50;
        font-weight: bold;
        font-size: 1.1em;
    }
    
    .feature-item:last-child {
        margin-bottom: 0;
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
    
    .card-red {
        border-left-color: #FF6B6B;
    }
    
    .card-teal {
        border-left-color: #20B2AA;
    }
    
    .card-mint {
        border-left-color: #95E1D3;
    }

    .card-peach {
        border-left-color: #FF9E7D;
    }
    
    .card-blue {
        border-left-color: #579BB1;
    }

    .card-pastel-milk {
        border-left-color: #AEC6CF;
    }
    
    .card-pastel-powder {
        border-left-color: #B0C4DE;
    }
    
    .card-pastel-ice {
        border-left-color: #BCEEFA;
    }
    

    .card-pastel-fog {
        border-left-color: #C1D3DB;
    }

    
    .card-lavender {
        border-left-color: #A7BBC7;
    }
    
    .card-yellow {
        border-left-color: #F4D160;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.8rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stat-card:nth-child(2) {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
    }
    
    .stat-card:nth-child(3) {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        box-shadow: 0 4px 12px rgba(79, 172, 254, 0.3);
    }
    
    .stat-number {
        font-size: 2.2em;
        font-weight: 700;
        margin: 0.5rem 0;
    }
    
    .stat-label {
        font-size: 0.95em;
        opacity: 0.95;
    }
    
    hr {
        margin: 3rem 0;
        border: none;
        border-top: 2px solid #f0f0f0;
    }
    
    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #999999;
        font-size: 0.95em;
        border-top: 1px solid #f0f0f0;
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


LEVELS = {
    1:  {"name":"여가 최우선",    "save":0.05, "fix":0.45, "leisure":0.50, "color":"#4CAF50"},
    2:  {"name":"여가 중심",      "save":0.10, "fix":0.50, "leisure":0.40, "color":"#8BC34A"},
    3:  {"name":"균형 여가형",    "save":0.15, "fix":0.55, "leisure":0.30, "color":"#CDDC39"},
    4:  {"name":"생활 균형형",    "save":0.20, "fix":0.55, "leisure":0.25, "color":"#FFEB3B"},
    5:  {"name":"균형형",         "save":0.25, "fix":0.55, "leisure":0.20, "color":"#FFC107"},
    6:  {"name":"저축 균형형",    "save":0.30, "fix":0.55, "leisure":0.15, "color":"#FF9800"},
    7:  {"name":"저축 집중형",    "save":0.40, "fix":0.50, "leisure":0.10, "color":"#FF5722"},
    8:  {"name":"고강도 저축",    "save":0.50, "fix":0.45, "leisure":0.05, "color":"#F44336"},
    9:  {"name":"극한 저축",      "save":0.65, "fix":0.35, "leisure":0.00, "color":"#E91E63"},
    10: {"name":"생존형 저축",    "save":0.80, "fix":0.20, "leisure":0.00, "color":"#9C27B0"},
}
st.session_state.LEVELS = LEVELS

# ── 메인 화면 ─────────────────────────────────────────────────────────────────
st.title("💰 FinFit")
st.markdown("#### 금융 미경험 청년을 위한 저축·소비 습관 서비스")
st.divider()

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📋 기본 정보 입력")
    income = st.number_input(
        "월 소득 / 용돈 (원)",
        min_value=10000, max_value=10000000,
        value=st.session_state.income, step=100000,
        format="%d"
    )
    st.session_state.income = income

    st.subheader("🎚️ 저축 강도 선택 (1~10단계)")
    level = st.slider(
        "1 = 여가 최우선 ~ 10 = 생존형 저축",
        min_value=1, max_value=10,
        value=st.session_state.level
    )
    st.session_state.level = level

    lv = LEVELS[level]
    st.markdown(f"""
    <div style="background:{lv['color']}22; border-left:5px solid {lv['color']};
                padding:14px 18px; border-radius:8px; margin-top:10px;">
        <b style="font-size:1.1em">{level}단계 · {lv['name']}</b><br>
        저축 <b>{int(lv['save']*100)}%</b> &nbsp;|&nbsp;
        고정비 <b>{int(lv['fix']*100)}%</b> &nbsp;|&nbsp;
        여가·식비 <b>{int(lv['leisure']*100)}%</b>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.subheader("📊 이번 달 예산 배분")
    save_amt    = int(income * lv['save'])
    fix_amt     = int(income * lv['fix'])
    leisure_amt = int(income * lv['leisure'])

    metrics = [
        ("💎 저축 목표",     save_amt,    lv['color']),
        ("🏠 고정비 예산",   fix_amt,     "#2196F3"),
        ("🎉 여가·식비 예산", leisure_amt, "#4CAF50"),
    ]
    for label, amt, color in metrics:
        st.markdown(f"""
        <div style="background:#f8f9fa; border-radius:10px; padding:14px 20px; margin-bottom:10px;
                    border-left:5px solid {color};">
            <span style="color:#555; font-size:0.9em">{label}</span><br>
            <span style="font-size:1.6em; font-weight:bold; color:#222">
                {amt:,}원
            </span>
            <span style="color:#888; font-size:0.85em"> / 월</span>
        </div>
        """, unsafe_allow_html=True)

st.divider()
st.markdown("#### 🗺️ 아래에서 기능을 선택하세요")
cols = st.columns(4)
#pages = [
    #("📒 가계부",        "수입·지출 기록 및 월별 분석"),
    #("🎯 저축단계 상세", "단계별 상세 가이드 및 팁"),
    #("🎁 청년 혜택",     "국가 청년 금융 지원 정보"),
    #("📚 금융 용어",     "꼭 알아야 할 금융 개념 정리"),
#]
#for col, (title, desc) in zip(cols, pages):
    #with col:
        #st.info(f"**{title}**\n\n{desc}")

#st.write("---")


# 기능 카드
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    # 카드 전체를 <a> 태그로 감싸고 주소 뒤에 ?page=Household_Ledger이 붙도록 만듭니다.
    cols = st.columns(4)
    st.markdown("""
    <a href="/?page=Household_Ledger" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-yellow">
            <div class="card-icon">📒</div>
            <div class="card-title">가계부</div>
            <div class="card-description">
                내역만 입력하면<br/>
                수입·지출 기록 및 월별 분석
            </div>
            <div class="card-features">
                <span class="card-features-title">이런 것들을 얻을 수 있어요</span>
                <div class="feature-item">고정비, 식비, 여가 등 정보</div>
                <div class="feature-item">구글 시트에 데이터 자동 동기화</div>
                <div class="feature-item">구글 시트 데이터 초기화 가능</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    # 이 버튼이 클릭되면 안전하게 st.switch_page가 작동합니다.
    if st.button("지금 입력해보기 →", key="btn_benefit", use_container_width=True):
        st.switch_page("pages/Household_Ledger.py")

with col2:
    # col2도 똑같이 전체 클릭 기능을 넣고 싶다면 아래처럼 <a> 태그로 감싸주면 됩니다.
    st.markdown("""
    <a href="/?page=finance" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-mint">
            <div class="card-icon">📚</div>
            <div class="card-title">금융 용어</div>
            <div class="card-description">
                CMA, ETF, 청년도약계좌,<br/>
                전세대출... 경제 신문에 나오는<br/>
                어려운 용어를 쉽게 설명해줍니다
            </div>
            <div class="card-features">
                <span class="card-features-title">이 정도는 꼭 알아야 해요</span>
                <div class="feature-item">30개 금융 개념 정리</div>
                <div class="feature-item">실생활 예시로 이해</div>
                <div class="feature-item">개념 + 행동 가이드</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    if st.button("금융 용어 배우기 →", key="btn_finance", use_container_width=True):
        st.switch_page("pages/5_금융용어.py")

with col3:
    st.markdown("""
    <a href="/?page=ai" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-pastel-fog">
            <div class="card-icon">🤖</div>
            <div class="card-title">AI 금융 상담</div>
            <div class="card-description">
                "전세금 대출은 언제까지 나올까?"<br/>
                "내가 받을 수 있는 혜택이 뭐야?"<br/>
                "자연어로 물어보면 AI가 즉답
            </div>
            <div class="card-features">
                <span class="card-features-title">AI가 도와줄 수 있어요</span>
                <div class="feature-item">50개 청년 정책 데이터 학습</div>
                <div class="feature-item">실시간 금융 계산</div>
                <div class="feature-item">군산시 맞춤 정보</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    if st.button("AI와 상담하기 →", key="btn_ai_agent", use_container_width=True):
        st.switch_page("pages/2_AI와_대화하기.py")


#st.divider()

# 기능 카드
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    cols = st.columns(4)
    st.markdown("""
    <a href="/?page=Government_Backed_Benefits" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-peach">
            <div class="card-icon">🎁</div>
            <div class="card-title">군산 시민 혜택 찾기</div>
            <div class="card-description">
                나이, 소득, 지역만 입력하면<br/>
                군산시에서 나에게 주는<br/>
                금융 지원과 대출을 자동 추천
            </div>
            <div class="card-features">
                <span class="card-features-title">이런 정보를 얻을 수 있어요</span>
                <div class="feature-item">50개 이상 청년 정책 매칭</div>
                <div class="feature-item">연 최대 1,000만원 이상 지원액</div>
                <div class="feature-item">신청 방법과 기한 안내</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    # 이 버튼이 클릭되면 안전하게 st.switch_page가 작동합니다.
    if st.button("지금 혜택 찾아보기 →", key="btn_Savings_Step_Setting_Guid_For", use_container_width=True):
        st.switch_page("pages/3_정부 지원 혜택 목록.py")

with col2:
    # col2도 똑같이 전체 클릭 기능을 넣고 싶다면 아래처럼 <a> 태그로 감싸주면 됩니다.
    st.markdown("""
    <a href="/?page=Government_Backed_Benefits" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-pastel-powder">
            <div class="card-icon">🌐</div>
            <div class="card-title">정부 지원 혜택</div>
            <div class="card-description">
                국가 청년 금융 지원 정보<br/>
                정부 사이트 실시간 동기화<br/>
                모든 정책을 한 화면에 보여줍니다
            </div>
            <div class="card-features">
                <span class="card-features-title">이 정도는 꼭 알아야 해요</span>
                <div class="feature-item">30개 금융 개념 정리</div>
                <div class="feature-item">실생활 예시로 이해</div>
                <div class="feature-item">개념 + 행동 가이드</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    if st.button("확인해 보러 가기 →", key="btn_finances", use_container_width=True):
        st.switch_page("pages/3_정부 지원 혜택 목록")

with col3:
    st.markdown("""
    <a href="/?page=ai" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-blue">
            <div class="card-icon">🤖</div>
            <div class="card-title">AI 금융 상담</div>
            <div class="card-description">
                "전세금 대출은 언제까지 나올까?"<br/>
                "내가 받을 수 있는 혜택이 뭐야?"<br/>
                "자연어로 물어보면 AI가 즉답
            </div>
            <div class="card-features">
                <span class="card-features-title">AI가 도와줄 수 있어요</span>
                <div class="feature-item">50개 청년 정책 데이터 학습</div>
                <div class="feature-item">실시간 금융 계산</div>
                <div class="feature-item">군산시 맞춤 정보</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    if st.button("AI와 상담하기 →", key="btn_ai", use_container_width=True):
        st.switch_page("pages/2_AI와_대화하기.py")
        

st.divider()

