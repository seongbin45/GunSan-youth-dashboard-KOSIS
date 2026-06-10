import streamlit as st

st.set_page_config(page_title="금융 용어 사전", page_icon="📚", layout="wide")
st.title("📚 사회초년생 필수 금융 용어")
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

keyword = st.text_input("🔍 용어 검색")

for category, items in terms.items():
    filtered = [(t, d) for t, d in items
                if not keyword or keyword.lower() in t.lower() or keyword.lower() in d.lower()]
    if not filtered:
        continue
    st.subheader(category)
    cols = st.columns(2)
    for i, (term, desc) in enumerate(filtered):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="background:#f8f9fa; border-radius:10px; padding:14px 16px;
                        margin-bottom:10px; border-left:4px solid #667eea;">
                <b style="color:#333">{term}</b><br>
                <span style="color:#555; font-size:0.9em">{desc}</span>
            </div>""", unsafe_allow_html=True)
    #st.divider()

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
        background: #ffffff;
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
        color: #ffffff;
        margin-bottom: 0.8rem;
    }
    
    .card-description {
        font-size: 1em;
        color: #eceff1;
        line-height: 1.7;
        margin-bottom: 1.5rem;
        flex-grow: 1;
    }
    
    .card-features {
        background: linear-gradient(135deg, #f5f5f5 0%, #1a1a1a 100%);
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    
    .card-features-title {
        font-size: 0.9em;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 0.8rem;
        display: block;
    }
    
    .feature-item {
        font-size: 0.95em;
        color: #ffffff;
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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

st.markdown("""
<div class="footer">
    <p>💌 저희는 더 나은 경험을 드리기 위해 꾸준히 준비 중입니다. 소중한 의견을 들려주시면 서비스 개선에 큰 도움이 됩니다.</p>
    <p>🔒 개인정보 보호</p>
    <a href="https://docs.google.com/forms/d/e/1FAIpQLSco-O4cGhbt1iMOwrEkqX5Vt0-8ctAtCxM5Z6JjmFlP-Uqq-Q/viewform?usp=header" target="_blank"><button style="color: #667eea;">설문 링크로 이동</button></a>
</div>
""", unsafe_allow_html=True)





