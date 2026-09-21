import streamlit as st
import textwrap

from finfit_youth.config import LEVELS, render_feedback_form, calculate_budget, inject_finfit_theme  # centralized (removed local dups)


st.set_page_config(page_title="FinFit", page_icon="💙", layout="wide")

# 주소창 ?page= 슬러그 라우팅 (미지 값 → FinFit 404 UI)
from finfit_youth.page_router import handle_query_page_param

if handle_query_page_param():
    st.stop()  # 의도적: 홈 본문과 404를 겹치지 않음

# Centralized theme (styles now travel with this page after st.switch_page from Onboarding/app)
inject_finfit_theme()

# ── 온보딩 데이터 연동 ─────────────────────────
onb_level = st.session_state.get("user_level")
onb_income_range = st.session_state.get("monthly_income_range")
onb_first_goal = st.session_state.get("first_goal")

def _range_to_income(r):
    if not r:
        return 1500000
    m = {
        "under50": 400000,
        "50to100": 750000,
        "100to150": 1250000,
        "150to200": 1750000,
        "over200": 2500000,
    }
    return m.get(r, 1500000)

income = _range_to_income(onb_income_range)
level = 5
budget = calculate_budget(income, level)
save_amt = budget["save"]
fix_amt = budget["fix"]
leisure_amt = budget["leisure"]

# Hide balance (prototype exact toggle)
if "hide_balance" not in st.session_state:
    st.session_state.hide_balance = False

# Demo spending / remaining derived from onboarding budget (adapt to TSX structure)
this_month_spend = leisure_amt + (fix_amt // 3)   # approx "지출"
budget_remaining = max(0, save_amt)               # proxy "예산 잔여" or save target feel
budget_usage = min(95, int((this_month_spend / income) * 100)) if income > 0 else 40

# 온보딩 연동 안내 (개인화)
if onb_first_goal or onb_income_range:
    st.caption(f"🎯 온보딩 연동: 소득 {onb_income_range or '미설정'} | 첫 목표 {onb_first_goal or '미설정'} | 경로 {onb_level or '미설정'}")

# Theme injected above via inject_finfit_theme() (now dark #111111 bg for home/app as requested)
# Uses shared: .asset-card, .finfit-progress, .stat-pill, .benefit-banner, .feature-card, .stat-card etc.

# Additional resets for closer prototype fidelity (reduce Streamlit default chrome/padding like TSX custom layout)
st.markdown("""
<style>
/* tighter container + full page dark background */
.main .block-container { padding-top: 0 !important; padding-left: 12px !important; padding-right: 12px !important; padding-bottom: 8px !important; max-width: 100% !important; }
.stApp > header, .stApp > div[data-testid="stToolbar"], .stApp > div[data-testid="stDecoration"] { display: none !important; }
.stButton > button { font-size: 0.92em !important; }

/* Force entire page background dark as requested */
.stApp, .main, body, .block-container, .stMain {
    background-color: #111111 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Header (closer to TSX Home.tsx: white bar, px-5, pt-12 feel, exact sizes) ─────────────────────────────────────────
st.markdown(textwrap.dedent("""
<div style="background:#111111; padding: 48px 20px 16px 20px; margin: -16px -16px 12px -16px; border-bottom: 1px solid #333333;">
  <div style="display:flex; align-items:center; justify-content:space-between;">
    <div>
      <p style="font-size:11px; color:#888888; margin:0 0 2px;">안녕하세요 👋</p>
      <h1 style="font-size:18px; font-weight:700; color:#ffffff; margin:0; line-height:1.3;">청년님</h1>
    </div>
    <div style="display:flex; align-items:center; gap:12px;">
      <div style="display:flex; align-items:center; gap:4px; background:#222222; padding:5px 12px; border-radius:999px;">
        <span style="font-size:12px; color:#6366F1;">⚡</span>
        <span style="font-size:11px; font-weight:600; color:#6366F1;">Lv.{}</span>
      </div>
      <div style="width:36px; height:36px; background:#222222; border-radius:999px; display:flex; align-items:center; justify-content:center; position:relative;">
        <span style="font-size:18px;">🔔</span>
        <span style="position:absolute; top:7px; right:7px; width:7px; height:7px; background:#EF4444; border-radius:999px;"></span>
      </div>
    </div>
  </div>
</div>
""".format(onb_level or "5")), unsafe_allow_html=True)

# ── Asset Card (literal translation of TSX JSX: gradient, relative, decor circles, exact flex, sub metrics with icons, hide) ─────────────────────
hide = st.session_state.hide_balance
total_assets = income * 8
asset_display = "••••••" if hide else f"{total_assets:,}원"
spend_display = "•••" if hide else f"{this_month_spend:,}원"
remain_display = "•••" if hide else f"{budget_remaining:,}원"

st.components.v1.html(textwrap.dedent(f"""
<div style="
  background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 60%, #A78BFA 100%);
  color: white;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 8px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(99,102,241,0.35);
">
  <!-- background decoration circles (exact from TSX) -->
  <div style="position:absolute; top:0; right:0; width:160px; height:160px; background:white; border-radius:999px; opacity:0.10; transform:translate(30%, -30%);"></div>
  <div style="position:absolute; bottom:0; left:0; width:96px; height:96px; background:white; border-radius:999px; opacity:0.10; transform:translate(-30%, 30%);"></div>

  <div style="position:relative;">
    <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:4px;">
      <p style="color:white; opacity:0.7; font-size:13px; margin:0;">총 자산</p>
      <span style="font-size:16px; opacity:0.6; cursor:pointer;">👁</span>
    </div>
    <p style="color:white; font-size:28px; font-weight:700; letter-spacing:-0.5px; margin:0 0 12px 0; line-height:1.1;">{asset_display}</p>

    <div style="display:flex; gap:12px;">
      <div style="flex:1; background:rgba(255,255,255,0.15); border-radius:12px; padding:10px 12px;">
        <div style="display:flex; align-items:center; gap:4px; margin-bottom:2px;">
          <span style="font-size:12px;">↓</span>
          <p style="color:white; opacity:0.7; font-size:11px; margin:0;">이번 달 지출</p>
        </div>
        <p style="color:white; font-weight:600; font-size:15px; margin:0;">{spend_display}</p>
      </div>
      <div style="flex:1; background:rgba(255,255,255,0.15); border-radius:12px; padding:10px 12px;">
        <div style="display:flex; align-items:center; gap:4px; margin-bottom:2px;">
          <span style="font-size:12px;">↑</span>
          <p style="color:white; opacity:0.7; font-size:11px; margin:0;">예산 잔여</p>
        </div>
        <p style="color:white; font-weight:600; font-size:15px; margin:0;">{remain_display}</p>
      </div>
    </div>
  </div>
</div>
"""), height=180)

# Eye toggle (prototype style, placed close to card for UX)
eye_text = "🙈 잔액 숨기기" if not hide else "👁 잔액 보기"
if st.button(eye_text, key="eye_toggle", use_container_width=False):
    st.session_state.hide_balance = not hide
    st.rerun()

# Budget Progress (literal from TSX: white rounded-2xl p-4, flex headers, thin h-3 bar, conditional color, 11px %)
progress_color = "#EF4444" if budget_usage > 90 else ("#F59E0B" if budget_usage > 70 else "#6366F1")
progress_grad = "linear-gradient(90deg, #EF4444, #F97316)" if budget_usage > 90 else ("linear-gradient(90deg, #F59E0B, #FBBF24)" if budget_usage > 70 else "linear-gradient(90deg, #6366F1, #8B5CF6)")
st.markdown(textwrap.dedent(f"""
<div style="background:#1a1a1a; border-radius:16px; padding:16px; margin:8px 0 4px; border:1px solid #333333;">
  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:10px;">
    <p style="color:#374151; font-size:13px; font-weight:600; margin:0;">이번 달 예산</p>
    <span style="font-size:11px; color:#6366F1; font-weight:500;">자세히 보기 →</span>
  </div>
  <div style="display:flex; justify-content:space-between; font-size:11px; color:#9CA3AF; margin-bottom:6px;">
    <span>{this_month_spend:,}원 사용</span>
    <span>{income:,}원 목표</span>
  </div>
  <div style="width:100%; height:12px; border-radius:999px; background:#F3F4F6; overflow:hidden;">
    <div style="width:{budget_usage}%; height:100%; border-radius:999px; background:{progress_grad}; transition:width .3s;"></div>
  </div>
  <p style="text-align:right; margin-top:4px; font-size:11px; color:{progress_color}; margin-bottom:0;">{budget_usage}% 사용</p>
</div>
"""), unsafe_allow_html=True)

# Quick Stats Row (exact 3 cards from TSX)
st.markdown(textwrap.dedent("""
<div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; margin:6px 0 10px;">
  <div class="stat-pill">
    <div class="label">신용점수</div>
    <div class="value" style="color:#10B981; font-size:18px; font-weight:700;">742</div>
    <span style="font-size:9px; background:#ECFDF5; color:#10B981; padding:1px 6px; border-radius:999px; font-weight:600;">좋음</span>
  </div>
  <div class="stat-pill" style="background:#FEF3C7; border-color:#FDE68A;">
    <div class="label" style="color:#92400E;">다음 결제</div>
    <div class="value" style="color:#EF4444; font-size:18px; font-weight:700;">D-3</div>
    <div style="font-size:10px; color:#92400E;">921,000원</div>
  </div>
  <div class="stat-pill" style="cursor:pointer;">
    <div class="label">연결 계좌</div>
    <div class="value" style="color:#6366F1; font-size:18px; font-weight:700;">3개</div>
    <div style="font-size:9px; color:#9CA3AF;">2개 은행</div>
  </div>
</div>
"""), unsafe_allow_html=True)

# Upcoming Payment Alert (conditional like TSX when dday low)
st.markdown(textwrap.dedent("""
<div style="background:linear-gradient(135deg, #FEF3C7, #FDE68A); border-radius:14px; padding:12px 14px; margin:4px 0;">
  <div style="display:flex; align-items:flex-start; gap:8px;">
    <span style="font-size:18px; margin-top:1px;">⚠️</span>
    <div style="flex:1;">
      <p style="color:#92400E; font-size:13px; font-weight:600; margin:0 0 2px;">D-3 카드 결제일 임박</p>
      <p style="color:#92400E; font-size:11px; margin:0;">신한카드 921,000원이 3일 후 출금됩니다.</p>
    </div>
  </div>
</div>
"""), unsafe_allow_html=True)

# NEW benefit banner (keep close + goal personalization)
goal_text = onb_first_goal or "첫 목표"
st.markdown(textwrap.dedent(f"""
<div class="benefit-banner" style="margin-bottom:8px;">
  <div style="display:flex; align-items:flex-start; gap:8px;">
    <div style="flex:1;">
      <div style="display:flex; align-items:center; gap:6px; margin-bottom:2px;">
        <span class="badge badge-new">🔔 NEW</span>
        <span style="font-size:11px; opacity:0.85;">청년 혜택 알림</span>
      </div>
      <p style="font-weight:700; font-size:14px; margin:0 0 2px; line-height:1.3;">내가 받을 수 있는 혜택이 있어요</p>
      <p style="font-size:11px; opacity:0.9; margin:0; line-height:1.3;">
        {goal_text} 달성 지원<br>최대 <b>연 220만원</b> 지원
      </p>
    </div>
    <div style="font-size:32px; margin-top:2px;">🎁</div>
  </div>
  <div style="margin-top:8px; padding-top:6px; border-top:1px solid rgba(255,255,255,0.25); font-size:11px; font-weight:600; display:flex; justify-content:space-between;">
    <span style="opacity:0.85;">청약통장 · 주거급여 · 장학금 등</span>
    <a href="/?page=benefit" target="_self" style="color:white; text-decoration:none;">확인하기 →</a>
  </div>
</div>
"""), unsafe_allow_html=True)

# Recent Transactions (TSX style list)
st.markdown(textwrap.dedent("""
<div style="margin:4px 0 2px;">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px; padding:0 2px;">
    <span style="font-size:13px; font-weight:600; color:#374151;">최근 거래</span>
    <span style="font-size:11px; color:#6366F1;">전체보기 →</span>
  </div>
  <div style="background:#1a1a1a; border-radius:14px; overflow:hidden; border:1px solid #333333;">
    <div class="tx-row"><div class="tx-icon">☕</div><div style="flex:1; min-width:0;"><div style="font-size:13px; font-weight:500;">카페 결제</div><div style="font-size:10px; color:#9CA3AF;">커피·간식 · 오늘</div></div><div style="font-size:13px; font-weight:600; color:#374151;">-12,000원</div></div>
    <div class="tx-row"><div class="tx-icon">🍕</div><div style="flex:1; min-width:0;"><div style="font-size:13px; font-weight:500;">배달 앱</div><div style="font-size:10px; color:#9CA3AF;">식비 · 어제</div></div><div style="font-size:13px; font-weight:600; color:#374151;">-18,500원</div></div>
    <div class="tx-row"><div class="tx-icon">🏦</div><div style="flex:1; min-width:0;"><div style="font-size:13px; font-weight:500;">적금 자동이체</div><div style="font-size:10px; color:#9CA3AF;">저축 · 6월 12일</div></div><div style="font-size:13px; font-weight:600; color:#10B981;">+25,000원</div></div>
  </div>
</div>
"""), unsafe_allow_html=True)

# Tip banner (TSX style)
st.markdown(textwrap.dedent("""
<div style="margin:8px 0 4px;">
  <div style="background:linear-gradient(135deg,#1E1B4B,#312E81); border-radius:14px; padding:12px 14px; color:white; display:flex; align-items:center; gap:10px; cursor:pointer;">
    <div style="flex:1;">
      <div style="font-size:11px; color:#A5B4FC; margin-bottom:1px;">💡 오늘의 금융 용어</div>
      <div style="font-size:13px; font-weight:600;">ETF가 뭔가요?</div>
      <div style="font-size:11px; color:#C7D2FE; margin-top:1px;">과자 한 개 대신 과자 세트를 사는 것!</div>
    </div>
    <span style="font-size:18px; color:#818CF8;">→</span>
  </div>
</div>
"""), unsafe_allow_html=True)

# Quick Menu 4 (exact from TSX Home "내 자산 관리")
st.markdown(textwrap.dedent("""
<div style="margin:6px 0 4px;">
  <p style="font-size:11px; font-weight:600; color:#374151; margin-bottom:6px; padding:0 2px;">내 자산 관리</p>
  <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:6px;">
    <div class="action-tile" onclick="Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('소비 분석') || el.textContent.includes('지출')).click();" style="background:#EEF0FF; cursor:pointer;">
      <div style="font-size:18px;">📊</div>
      <div style="font-size:10px; color:#6366F1; font-weight:600; margin-top:2px;">소비 분석</div>
    </div>
    <div class="action-tile" onclick="Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('저축 목표') || el.textContent.includes('Savings')).click();" style="background:#FFF7ED; cursor:pointer;">
      <div style="font-size:18px;">🎯</div>
      <div style="font-size:10px; color:#F97316; font-weight:600; margin-top:2px;">저축 목표</div>
    </div>
    <div class="action-tile" onclick="Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('계좌') || el.textContent.includes('Household')).click();" style="background:#F0FDF4; cursor:pointer;">
      <div style="font-size:18px;">🏦</div>
      <div style="font-size:10px; color:#10B981; font-weight:600; margin-top:2px;">계좌 관리</div>
    </div>
    <div class="action-tile" onclick="Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('카드') || el.textContent.includes('혜택')).click();" style="background:#FFF1F2; cursor:pointer;">
      <div style="font-size:18px;">💳</div>
      <div style="font-size:10px; color:#F43F5E; font-weight:600; margin-top:2px;">카드 혜택</div>
    </div>
  </div>
</div>
"""), unsafe_allow_html=True)

st.divider()

# 핵심 기능 (TSX Home core 3 + project extras)
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    st.markdown("""
    <a href="/?page=benefit" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-yellow">
            <div class="card-icon">🔔</div>
            <div class="card-title">혜택 알림</div>
            <div class="card-description">
                내 조건에 맞는<br/>
                청년 지원 자동 추천
            </div>
            <div class="card-features">
                <span class="card-features-title">이런 정보</span>
                <div class="feature-item">50개 이상 정책 매칭</div>
                <div class="feature-item">연 최대 1,000만원 지원</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    if st.button("지금 찾아보기 →", key="btn_benefit_core", use_container_width=True):
        st.switch_page("pages/4_군산시민 맞춤 혜택 찾기.py")

with col2:
    st.markdown("""
    <a href="/?page=finance" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-mint">
            <div class="card-icon">🤖</div>
            <div class="card-title">AI 용어 해설</div>
            <div class="card-description">
                CMA, ETF, 청년도약계좌<br/>
                어려운 용어 쉽게 설명
            </div>
            <div class="card-features">
                <span class="card-features-title">30개 핵심 개념</span>
                <div class="feature-item">실생활 예시 + 행동 가이드</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    if st.button("용어 배우기 →", key="btn_finance_core", use_container_width=True):
        st.switch_page("pages/5_금융용어.py")

with col3:
    st.markdown("""
    <a href="/?page=ai" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-pastel-fog">
            <div class="card-icon">📚</div>
            <div class="card-title">금융 교육</div>
            <div class="card-description">
                일상 사례로 금융<br/>
                핵심 개념 스토리텔링
            </div>
            <div class="card-features">
                <span class="card-features-title">기초부터 투자까지</span>
                <div class="feature-item">AI 상담으로 즉시 질문</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    if st.button("AI와 상담하기 →", key="btn_ai_core", use_container_width=True):
        st.switch_page("pages/2_AI와_대화하기.py")

with col2:
    # col2도 똑같이 전체 클릭 기능을 넣고 싶다면 아래처럼 <a> 태그로 감싸주면 됩니다.
    st.markdown("""
    <a href="/?page=finance" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-mint">
            <div class="card-icon">📚</div>
            <div class="card-title">금융 용어</div>
            <div class="card-description">
                CMA, ETF, 청년도약계좌,<br/>
                전세대출 등<br/>
                경제 신문에 나오는<br/> 
                어려운 용어를<br/>
                쉽게 설명해줍니다
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
            <div class="card-icon">🚀</div>
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
    st.markdown("""
    <a href="/?page=benefit" target="_self" style="text-decoration: none; color: inherit;">
        <div class="feature-card card-peach">
            <div class="card-icon">🎁</div>
            <div class="card-title">군산 맞춤 혜택 찾기</div>
            <div class="card-description">
                나이, 소득, 지역만 입력하면<br/>
                군산시에서 나에게 주는<br/>
                나에게 맞는 혜택을 자동 추천
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
        st.switch_page("pages/4_군산시민 맞춤 혜택 찾기.py")

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
                <span class="card-features-title">이런 정보를 얻을 수 있어요</span>
                <div class="feature-item">청년도약계좌, 햇살론 등</div>
                <div class="feature-item">신청 방법 및 기한</div>
                <div class="feature-item">공식 사이트 링크</div>
            </div>
        </div>
    </a>
    """, unsafe_allow_html=True)
    
    if st.button("확인해 보러 가기 →", key="btn_finances", use_container_width=True):
        st.switch_page("pages/3_정부 지원 혜택 목록.py")

with col3:
    # onclick 내부의 window.parent를 제거하여 보안 차단을 우회합니다.
    st.markdown("""
    <div class="feature-card card-blue" style="cursor: pointer;" onclick="Array.from(document.querySelectorAll('button')).find(el => el.textContent.includes('바로 확인해보기')).click();">
        <div class="card-icon">🎯</div>
        <div class="card-title">저축단계 상세 가이드</div>
        <div class="card-description">
            몇 개월 후 도달 금액을<br/>
            미리 확인할 수 있어요
        </div>
        <div class="card-features">
            <span class="card-features-title">이런 자료들을 얻을 수 있어요</span>
            <div class="feature-item">단계별 상세 가이드 및 팁</div>
            <div class="feature-item">목표 금액 시뮬레이션</div>
            <div class="feature-item">전체 단계 비교 그래프</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 이 버튼이 자바스크립트에 의해 클릭되며 데이터 초기화 없이 페이지를 이동시킵니다.
    if st.button("바로 확인해보기 →", key="btn_ai", use_container_width=True):
        st.switch_page("pages/Savings_Step_Setting_Guide.py")

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


st.markdown('<div style="height: 4px;"></div>', unsafe_allow_html=True)  # minimal spacer instead of divider

# FAQ - super tight top
st.markdown("""
<style>
.stTabs { margin-top: -12px !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 0 !important; margin-top: -12px !important; }
.stTabs [data-baseweb="tab-panel"] > div { margin-top: 0 !important; padding-top: 0 !important; }
</style>
""", unsafe_allow_html=True)
st.markdown('<div style="margin-top:-4px;"><b style="font-size:1.1em; color:#f0f0f0;">❓ 자주 묻는 질문</b></div>', unsafe_allow_html=True)

faq_tab1, faq_tab2, faq_tab3 = st.tabs(["무료인가요?", "개인정보는?", "전국 사용 가능?"])

with faq_tab1:
    st.markdown('<div style="margin-top: -12px;">', unsafe_allow_html=True)
    st.markdown("""
    **Q. FinFit은 정말 무료인가요?**
    
    A. 네, 완전히 무료입니다. 정부 지원금 조회, AI 상담, 금융 용어 설명 모두 무료로 이용할 수 있습니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

with faq_tab2:
    st.markdown('<div style="margin-top: -12px;">', unsafe_allow_html=True)
    st.markdown("""
    **Q. 내 개인정보가 저장되나요?**
    
    A. 아니요. 입력하신 정보는 조회 순간에만 사용되고 저장되지 않습니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)

with faq_tab3:
    st.markdown('<div style="margin-top: -12px;">', unsafe_allow_html=True)
    st.markdown("""
    **Q. 군산시에 살지 않아도 쓸 수 있나요?**
    
    A. 네, 가능합니다! 국가 청년 정책은 전국 어디서나, 지역 정책은 해당 지역에서 사용할 수 있습니다.
    """)
    st.markdown('</div>', unsafe_allow_html=True)




st.divider()


render_feedback_form(key_prefix="home")

# 개발용: 온보딩 다시 보기 (프로토타입 스타일)
st.divider()
if st.button("🔄 온보딩 다시 보기 (개발용)", use_container_width=True):
    st.session_state.onboarding_completed = False
    st.switch_page("pages/Onboarding.py")



