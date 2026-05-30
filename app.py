import streamlit as st

st.set_page_config(page_title="FinFit", page_icon="💙", layout="wide")

# 주소창의 흔적을 감지해서 페이지를 이동시키는 네비게이터 역할을 합니다.
if "page" in st.query_params:
    target = st.query_params["page"]
    st.query_params.clear() # 무한 루프 방지를 위해 흔적 지우기
    
    if target == "benefit":
        st.switch_page("pages/4_군산시민 맞춤 혜택 찾기.py")
    elif target == "finance":
        st.switch_page("pages/5_금융용어.py")
    elif target == "ai":
        st.switch_page("pages/2_AI와_대화하기.py")
    elif target == "Household_Ledger":
        st.switch_page("pages/Household_Ledger.py")
    elif target == "Savings_Step_Setting_Guide":
        st.switch_page("pages/Savings_Step_Setting_Guide.py")
    elif target == "Government_Backed_Benefits":
        st.switch_page("pages/3_정부 지원 혜택 목록.py")

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

# 헤더
st.markdown("""
<div class="header-container">
    <div class="header-title">💙 FinFit</div>
    <div class="header-subtitle">청년이 받아야 할 혜택을, AI가 먼저 찾아줍니다</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# 세 가지 기능 카드
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    # 카드 전체를 <a> 태그로 감싸고 주소 뒤에 ?page=benefit이 붙도록 만듭니다.
    st.markdown("""
    <a href="/?page=benefit" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-red">
            <div class="card-icon">🎁</div>
            <div class="card-title">내 혜택 찾기</div>
            <div class="card-description">
                나이, 소득, 지역만 입력하면<br/>
                정부·군산시에서 나에게 주는<br/>
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
    if st.button("지금 혜택 찾아보기 →", key="btn_benefit", use_container_width=True):
        st.switch_page("pages/4_군산시민 맞춤 혜택 찾기.py")

with col2:
    # col2도 똑같이 전체 클릭 기능을 넣고 싶다면 아래처럼 <a> 태그로 감싸주면 됩니다.
    st.markdown("""
    <a href="/?page=finance" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-teal">
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
        <div class="feature-card card-mint">
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

# 통계 섹션
st.markdown("## 📊 FinFit이 찾아준 혜택들")

stat_col1, stat_col2, stat_col3 = st.columns(3, gap="large")

with stat_col1:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-label">사용자가 찾은 평균</div>
        <div class="stat-number">7.2개</div>
        <div class="stat-label">청년 정책</div>
    </div>
    """, unsafe_allow_html=True)

with stat_col2:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-label">연간 평균 지원액</div>
        <div class="stat-number">580만원</div>
        <div class="stat-label">1인당</div>
    </div>
    """, unsafe_allow_html=True)

with stat_col3:
    st.markdown("""
    <div class="stat-card">
        <div class="stat-label">사용자 만족도</div>
        <div class="stat-number">4.8/5.0</div>
        <div class="stat-label">⭐ 별점</div>
    </div>
    """, unsafe_allow_html=True)


st.divider()

# FAQ
st.markdown("## ❓ 자주 묻는 질문")

faq_tab1, faq_tab2, faq_tab3 = st.tabs(["무료인가요?", "개인정보는?", "전국 사용 가능?"])

with faq_tab1:
    st.markdown("""
    **Q. FinFit은 정말 무료인가요?**
    
    A. 네, 완전히 무료입니다. 정부 지원금 조회, AI 상담, 금융 용어 설명 모두 무료로 이용할 수 있습니다.
    """)

with faq_tab2:
    st.markdown("""
    **Q. 내 개인정보가 저장되나요?**
    
    A. 아니요. 입력하신 정보는 조회 순간에만 사용되고 저장되지 않습니다.
    """)

with faq_tab3:
    st.markdown("""
    **Q. 군산시에 살지 않아도 쓸 수 있나요?**
    
    A. 네, 가능합니다! 국가 청년 정책은 전국 어디서나, 지역 정책은 해당 지역에서 사용할 수 있습니다.
    """)

st.divider()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="footer">
    <p>💌 저희 서비스는 더 나은 경험을 드리기 위해 꾸준히 준비 중입니다. 소중한 의견을 들려주시면 서비스 개선에 큰 도움이 됩니다.</p>
    <p>🔒 개인정보 보호 | 📞 문의: 010-4666-9672 | 📧 choiseongbin45@gmail.com</p>
</div>
""", unsafe_allow_html=True)


