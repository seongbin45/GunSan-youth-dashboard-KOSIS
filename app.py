import streamlit as st

st.set_page_config(page_title="FinFit", page_icon="💚", layout="wide")

st.markdown("""
<style>
    /* 카드 전체를 감싸는 컨테이너 위치 설정 */
    .card-container {
        position: relative;
        cursor: pointer;
    }
    
    /* Streamlit 버튼을 카드 크기만큼 키우고 투명하게 만들기 */
    .card-container .stButton > button {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        opacity: 0; /* 완전히 투명하게 설정 */
        z-index: 10; /* HTML 카드보다 위에 오도록 설정 */
        cursor: pointer;
    }

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
    <div class="header-title">💚 FinFit</div>
    <div class="header-subtitle">청년이 받아야 할 혜택을, AI가 먼저 찾아줍니다</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# 세 가지 기능 카드
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    # 카드 전체를 클릭하면 해당 페이지로 이동하도록 <a> 태그로 감싸기
    # 디자인 유지를 위해 스타일(텍스트 데코레이션 제거, 색상 유지)을 부여합니다.
    st.markdown("""
    <a href="4_군산시민_맞춤_혜택_찾기.py" target="_self" style="text-decoration: none; color: inherit;">
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
    
    # 하단 버튼 (이제 레이아웃이 깨지지 않고 정상적으로 카드의 정중앙 하단에 위치합니다)
    if st.button("지금 혜택 찾아보기 →", key="btn_benefit", use_container_width=True):
        st.switch_page("pages/4_군산시민 맞춤 혜택 찾기.py")

with col2:
    # col2도 똑같이 전체 클릭 기능을 넣고 싶다면 아래처럼 <a> 태그로 감싸주면 됩니다.
    st.markdown("""
    <a href="pages/6_금융용어.py" target="_self" style="text-decoration: none; color: inherit;">
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
        st.switch_page("pages/6_금융용어.py")

with col3:
    st.markdown("""
    <a href="pages/0_FinFit_Agent.py" target="_self" style="text-decoration: none; color: inherit;">
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
        st.switch_page("pages/0_FinFit_Agent.py")

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
    <p>💡 FinFit은 군산시청 · 군산시 창업지원센터 · 국립군산대학교와 함께 만들었습니다</p>
    <p>🔒 개인정보 보호 | 📞 문의: 010-4666-9672 | 📧 choiseongbin45@gmail.com</p>
</div>
""", unsafe_allow_html=True)


