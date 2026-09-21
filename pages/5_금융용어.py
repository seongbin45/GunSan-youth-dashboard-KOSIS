import streamlit as st
import textwrap

st.set_page_config(page_title="금융 용어 사전", page_icon="📚", layout="wide")

# Inject dark theme
from finfit_youth.config import inject_finfit_theme
inject_finfit_theme()

# Additional page specific dark styles
st.markdown("""
<style>
.stApp { background: #111111 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header matching TSX Glossary ──
st.markdown(textwrap.dedent("""
<div style="background:#1a1a1a; padding:12px 16px 8px; margin:-8px -8px 8px; border-bottom:1px solid #333;">
  <div style="display:flex; align-items:center; gap:12px;">
    <div onclick="window.history.back()" style="width:36px; height:36px; background:#222; border-radius:50%; display:flex; align-items:center; justify-content:center; cursor:pointer;">
      <span style="font-size:18px; color:#aaa;">←</span>
    </div>
    <div style="font-size:20px; font-weight:700; color:#f0f0f0;">AI 금융 용어 해설</div>
  </div>
</div>
"""), unsafe_allow_html=True)

# Search and popular tags - TSX style
keyword = st.text_input("🔍 어려운 용어를 입력하세요 — AI가 설명해드려요", placeholder="ETF, 신용점수, 복리 등", label_visibility="collapsed")

POPULAR_TAGS = ["ETF", "청약", "신용점수", "적금", "펀드", "ISA", "복리", "연말정산", "CMA", "IRP", "DSR", "비상금"]

if not keyword:
    st.markdown(textwrap.dedent("""
    <div style="padding: 0 4px 8px;">
      <p style="color:#888; font-size:11px; font-weight:600; margin-bottom:6px;">인기 검색어</p>
      <div style="display:flex; flex-wrap:wrap; gap:6px;">
    """), unsafe_allow_html=True)

    tag_cols = st.columns(6)
    for i, tag in enumerate(POPULAR_TAGS[:6]):
        with tag_cols[i]:
            if st.button(f"#{tag}", key=f"tag_{i}", use_container_width=True):
                keyword = tag
                st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

# AI Banner matching TSX
if not keyword:
    st.markdown(textwrap.dedent("""
    <div style="background: linear-gradient(135deg,#6366F1,#8B5CF6); border-radius:16px; padding:14px; margin:8px 0; box-shadow:0 4px 16px rgba(99,102,241,0.3);">
      <div style="display:flex; align-items:center; gap:10px;">
        <div style="width:40px; height:40px; background:rgba(255,255,255,0.2); border-radius:12px; display:flex; align-items:center; justify-content:center; font-size:20px;">🤖</div>
        <div>
          <p style="color:white; font-size:14px; font-weight:700; margin:0;">AI 금융 용어 해설</p>
          <p style="color:#C7D2FE; font-size:11px; margin:0;">장벽 해소 — V2 핵심 기능</p>
        </div>
      </div>
      <p style="color:#C7D2FE; font-size:11px; margin-top:6px; line-height:1.4;">
        혜택 신청서에 나오는 어려운 금융 용어,<br>비유와 실생활 예시로 AI가 실시간 풀어드려요
      </p>
    </div>
    """), unsafe_allow_html=True)

# Terms data (kept from original for content fidelity)
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
        ("체크카드 vs 신용카드", "체크카드 = 잔액 내에서 사용. 신용카드 = 나중에 결제. 연말정산 공제율은 체크카드가 더 높음(30%)."),
        ("자동이체", "정해진 날짜에 자동으로 이체. 저축은 월급날 바로 자동이체 설정이 핵심."),
        ("비상금", "갑작스런 지출을 대비한 생활비 3~6개월치. 손대기 어려운 별도 통장에 보관."),
        ("페이 서비스", "카카오페이·네이버페이·토스 등. 편리하지만 소비 내역 관리가 중요."),
        ("환율", "원화와 외화의 교환 비율. 환율 높을수록 달러 구매 비용 증가."),
    ],
}

# Term count
filtered_count = sum(1 for items in terms.values() for t, d in items if not keyword or keyword.lower() in t.lower() or keyword.lower() in d.lower())
st.markdown(f'<p style="color:#888; font-size:11px; margin:4px 0 8px;">{f"\"{keyword}\" 검색 결과 {filtered_count}개" if keyword else f"전체 {filtered_count}개 용어"}</p>', unsafe_allow_html=True)

# Terms list - TSX style cards with expand simulation using expanders for functionality
for category, items in terms.items():
    filtered = [(t, d) for t, d in items if not keyword or keyword.lower() in t.lower() or keyword.lower() in d.lower()]
    if not filtered:
        continue

    st.markdown(f'<div style="color:#aaa; font-size:12px; font-weight:600; margin:8px 0 4px;">{category}</div>', unsafe_allow_html=True)

    for term, desc in filtered:
        with st.expander(f"**{term}**", expanded=False):
            st.markdown(f'<span style="color:#ccc; font-size:0.95em; line-height:1.5;">{desc}</span>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer" style="margin-top:20px;">
    <p>💌 저희는 더 나은 경험을 드리기 위해 꾸준히 준비 중입니다. 소중한 의견을 들려주시면 서비스 개선에 큰 도움이 됩니다.</p>
    <p>🔒 개인정보 보호</p>
</div>
""", unsafe_allow_html=True)





