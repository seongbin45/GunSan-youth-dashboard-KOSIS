import streamlit as st

st.set_page_config(page_title="FinFit 온보딩", page_icon="🚀", layout="wide")

# Original code structure imported from C:\Users\seong\Desktop\new\src\app\pages\Onboarding.tsx
BG1 = "linear-gradient(160deg,#0F0C29 0%,#1E1B4B 40%,#312E81 75%,#4338CA 100%)"
BG2 = "linear-gradient(160deg,#0F0C29 0%,#1a1250 40%,#2D1F6B 75%,#3730A3 100%)"

INCOMES = [
  { "id": "under50",  "label": "50만원 미만",  "sub": "소액 용돈" },
  { "id": "50to100",  "label": "50~100만원",   "sub": "일반 용돈·알바" },
  { "id": "100to150", "label": "100~150만원",  "sub": "알바·장학금" },
  { "id": "150to200", "label": "150~200만원",  "sub": "인턴·계약직" },
  { "id": "over200",  "label": "200만원 이상", "sub": "정규직·사회초년생" },
]

GOALS = [
  { "id": "travel",    "e": "✈️", "label": "여행 자금",      "sub": "국내외 여행" },
  { "id": "laptop",    "e": "💻", "label": "노트북·전자기기", "sub": "원하는 기기" },
  { "id": "emergency", "e": "🛡️", "label": "비상금 마련",    "sub": "예상치 못한 지출" },
  { "id": "study",     "e": "📚", "label": "자격증·공부",    "sub": "인강, 교재" },
  { "id": "saving",    "e": "🏦", "label": "그냥 모으기",    "sub": "특별한 목표 없이" },
]

BEGINNER_STEPS = [
  {
    "emoji": "😮‍💨",
    "title": "용돈 받으면\n어느새 사라지죠?",
    "desc": '"분명히 조금 썼는데 왜 바닥이지?"\n대학생 10명 중 7명이 이런 경험을 해요.',
  },
  {
    "emoji": "📊",
    "title": "대부분의 대학생이\n이걸 모르고 있어요",
    "desc": "29명의 대학생 인터뷰에서 나온 사실이에요",
  },
  {
    "emoji": "🚀",
    "title": "핀핏의 3가지\n핵심 기능",
    "desc": "금융을 시작하는 데 딱 필요한 것들이에요",
  },
  {
    "emoji": "💡",
    "title": "이런 혜택들이\n기다리고 있어요",
    "desc": "청년이라면 지금 신청할 수 있어요",
  },
  {
    "emoji": "🎯",
    "title": "첫 목표를\n세워볼까요?",
    "desc": "나중에 언제든 바꿀 수 있어요",
  },
]

EXP_FEATURES = [
  { "e": "🎁", "label": "청년 혜택", "sub": "놓치는 지원금·적금" },
  { "e": "📊", "label": "소비 분석", "sub": "어디에 얼마 쓰는지" },
  { "e": "🎯", "label": "저축 목표", "sub": "목표 세우고 계획" },
  { "e": "📚", "label": "금융 학습", "sub": "기초부터 투자까지" },
]

EXP_STEPS = [
  { "emoji": "⚡", "title": "어떤 기능이\n가장 필요하세요?", "desc": "관심 있는 기능을 선택해주세요" },
  { "emoji": "💰", "title": "월 소득 범위를\n알려주세요",    "desc": "맞춤 예산과 저축 계획을 잡아드려요" },
]

# ── Prototype-exact immersive dark theme (BG1/BG2 + card styles + hidden chrome) ──
st.markdown("""
<style>
.stApp {
    background: linear-gradient(160deg,#0F0C29 0%,#1E1B4B 40%,#312E81 75%,#4338CA 100%) !important;
    color: white !important;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
}
.stApp > header, .stApp > div[data-testid="stToolbar"], .stApp > div[data-testid="stDecoration"], .stSidebar,
div[data-testid="stHeader"], div[data-testid="stToolbar"] {
    display: none !important;
}

/* Primary gradient CTA (bottom main button) */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important;
    border: none !important;
    color: white !important;
    font-weight: 700 !important;
    text-align: center !important;
    padding: 15px 16px !important;
    font-size: 15px !important;
    border-radius: 14px !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}

/* Text-style links for prev/skip */
.stButton > button.onboarding-text-btn {
    background: transparent !important;
    border: none !important;
    color: #818CF8 !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 4px 8px !important;
    width: auto !important;
}

/* Level choice buttons as full cards - match TSX */
.level-card-btn .stButton > button {
    width: 100% !important;
    background: rgba(255,255,255,0.08) !important;
    border-radius: 20px !important;
    padding: 0 !important;
    overflow: hidden !important;
    text-align: left !important;
    font-size: 13px !important;
    line-height: 1.4 !important;
    white-space: pre-line !important;
    font-family: system-ui, -apple-system, sans-serif !important;
}
.level-card-btn.beginner .stButton > button {
    border: 2px solid rgba(255,255,255,0.18) !important;
}
.level-card-btn.experienced .stButton > button {
    border: 2px solid rgba(255,255,255,0.12) !important;
}
.level-card-btn .stButton > button:hover {
    background: rgba(99,102,241,0.15) !important;
    border-color: #6366F1 !important;
}

/* Choice buttons (income rows) - match TSX */
.choice-btn .stButton > button {
    background: rgba(255,255,255,0.07) !important;
    border: 2px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    padding: 11px 14px !important;
    font-size: 13px !important;
    text-align: left !important;
    white-space: pre-line !important;
}
.choice-btn .stButton > button:hover {
    background: rgba(99,102,241,0.12) !important;
    border-color: rgba(99,102,241,0.5) !important;
}

/* Grid choice buttons (goals, exp features) - match TSX */
.choice-grid-btn .stButton > button {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 16px !important;
    padding: 14px 10px !important;
    font-size: 12px !important;
    text-align: center !important;
    min-height: 92px !important;
    white-space: pre-line !important;
}
.choice-grid-btn .stButton > button:hover {
    background: rgba(99,102,241,0.15) !important;
    border-color: #6366F1 !important;
}

/* Level card cover for pixel-perfect TSX cards (visual HTML + transparent absolute button overlay) */
.level-card-cover { position: relative; min-height: 148px; margin-bottom: 14px; }
.level-card-cover .visual { border-radius: 20px; overflow: hidden; border: 2px solid rgba(255,255,255,0.18); background: rgba(255,255,255,0.08); }
.level-card-cover .stButton { position: absolute; top: 0; left: 0; right: 0; bottom: 0; z-index: 10; }
.level-card-cover .stButton > button {
    width: 100% !important; height: 100% !important;
    background: transparent !important; border: none !important; box-shadow: none !important;
    color: transparent !important; padding: 0 !important; margin: 0; cursor: pointer;
}
.level-card-cover .stButton > button:hover { background: rgba(99,102,241,0.08) !important; }
</style>
""", unsafe_allow_html=True)

# Session state init (include exp paths for fidelity to prototype)
if "onboarding_step" not in st.session_state:
    st.session_state.onboarding_step = 0
if "onboarding_level" not in st.session_state:
    st.session_state.onboarding_level = None
if "onboarding_income" not in st.session_state:
    st.session_state.onboarding_income = None
if "onboarding_goal" not in st.session_state:
    st.session_state.onboarding_goal = None
if "onboarding_exp_feature" not in st.session_state:
    st.session_state.onboarding_exp_feature = None

def go_next():
    st.session_state.onboarding_step += 1

def go_prev():
    st.session_state.onboarding_step = max(0, st.session_state.onboarding_step - 1)

def complete_onboarding():
    st.session_state.onboarding_completed = True
    st.session_state.onboarding_step = 0
    st.session_state.user_level = st.session_state.onboarding_level
    # income may come from beginner or experienced path
    inc = st.session_state.onboarding_income
    st.session_state.monthly_income_range = inc
    st.session_state.first_goal = st.session_state.onboarding_goal
    if st.session_state.onboarding_level == "experienced" and st.session_state.onboarding_exp_feature:
        st.session_state.exp_feature = st.session_state.onboarding_exp_feature
    st.switch_page("pages/0_Home.py")

if st.session_state.onboarding_step == 0:
    # Exact structure from Onboarding.tsx - header
    st.markdown("""
    <div style="max-width:680px; margin:0 auto; padding:52px 20px 20px; color:white; font-family:system-ui,-apple-system,sans-serif;">
        <div style="text-align:center; margin-bottom:28px;">
            <div style="font-size:52px; margin-bottom:14px;">🤔</div>
            <h1 style="color:white; font-size:22px; font-weight:800; line-height:1.4; margin-bottom:10px;">
                경제 관념이 없어도<br/>괜찮아요
            </h1>
            <p style="color:#A5B4FC; font-size:13px; line-height:1.6;">
                금융을 처음 시작하는 분들을 위해 만들었어요
            </p>
        </div>
    """, unsafe_allow_html=True)

    # Beginner card - pixel match to TSX button (visual + absolute transparent cover button)
    st.markdown('<div class="level-card-cover">', unsafe_allow_html=True)
    st.markdown("""
    <div class="visual" style="border:2px solid rgba(255,255,255,0.18); background:rgba(255,255,255,0.08); border-radius:20px; overflow:hidden;">
      <div style="padding:18px 18px 14px;">
        <div style="display:flex; align-items:flex-start; gap:14px;">
          <div style="width:48px; height:48px; border-radius:13px; background:linear-gradient(135deg,#6366F1,#818CF8); display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:22px;">📘</div>
          <div style="flex:1;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:5px;">
              <span style="color:white; font-size:15px; font-weight:700;">처음이에요 🙋</span>
              <span style="font-size:10px; padding:2px 7px; border-radius:99px; background:rgba(99,102,241,0.45); color:#C7D2FE;">추천</span>
            </div>
            <p style="color:#A5B4FC; font-size:12px; line-height:1.55; margin:0;">
              경제 관념이 없어도 괜찮아요.<br/>내가 받을 수 있는 혜택부터 알려드릴게요.
            </p>
          </div>
        </div>
        <div style="margin-top:12px; display:grid; grid-template-columns:1fr 1fr; gap:6px;">
          <div style="display:flex; align-items:center; gap:5px; color:#A5B4FC; font-size:11px;"><span style="font-size:11px;">✓</span> 청년 혜택 발견</div>
          <div style="display:flex; align-items:center; gap:5px; color:#A5B4FC; font-size:11px;"><span style="font-size:11px;">✓</span> AI 용어 해설</div>
          <div style="display:flex; align-items:center; gap:5px; color:#A5B4FC; font-size:11px;"><span style="font-size:11px;">✓</span> 금융 기초 교육</div>
          <div style="display:flex; align-items:center; gap:5px; color:#A5B4FC; font-size:11px;"><span style="font-size:11px;">✓</span> 맞춤 목표 설정</div>
        </div>
      </div>
      <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 18px; border-top:1px solid rgba(255,255,255,0.1); background:rgba(99,102,241,0.15);">
        <span style="color:#C7D2FE; font-size:11px;">5단계 맞춤 가이드</span>
        <span style="color:#818CF8; font-size:15px;">→</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(" ", key="beg", use_container_width=True):
        st.session_state.onboarding_level = "beginner"
        st.session_state.onboarding_step = 1
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # Experienced card - exact TSX
    st.markdown('<div class="level-card-cover">', unsafe_allow_html=True)
    st.markdown("""
    <div class="visual" style="border:2px solid rgba(255,255,255,0.12); background:rgba(255,255,255,0.08); border-radius:20px; overflow:hidden;">
      <div style="padding:18px 18px 14px;">
        <div style="display:flex; align-items:flex-start; gap:14px;">
          <div style="width:48px; height:48px; border-radius:13px; background:linear-gradient(135deg,#8B5CF6,#A78BFA); display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:22px;">⚡</div>
          <div style="flex:1;">
            <span style="color:white; font-size:15px; font-weight:700; display:block; margin-bottom:5px;">어느 정도 알아요 ✌️</span>
            <p style="color:#A5B4FC; font-size:12px; line-height:1.55; margin:0;">
              예산·저축 관리를 해봤고<br/>빠르게 혜택 알림을 설정하고 싶어요.
            </p>
          </div>
        </div>
        <div style="margin-top:12px; display:flex; gap:10px; flex-wrap:wrap;">
          <div style="display:flex; align-items:center; gap:5px; color:#A5B4FC; font-size:11px;"><span style="font-size:11px;">✓</span> 관심 기능 선택</div>
          <div style="display:flex; align-items:center; gap:5px; color:#A5B4FC; font-size:11px;"><span style="font-size:11px;">✓</span> 소득 범위 설정</div>
          <div style="display:flex; align-items:center; gap:5px; color:#A5B4FC; font-size:11px;"><span style="font-size:11px;">✓</span> 바로 시작</div>
        </div>
      </div>
      <div style="display:flex; align-items:center; justify-content:space-between; padding:8px 18px; border-top:1px solid rgba(255,255,255,0.1); background:rgba(139,92,246,0.15);">
        <span style="color:#C7D2FE; font-size:11px;">2단계 빠른 셋업</span>
        <span style="color:#A78BFA; font-size:15px;">→</span>
      </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button(" ", key="exp", use_container_width=True):
        st.session_state.onboarding_level = "experienced"
        st.session_state.onboarding_step = 1
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
        <p style="color:#818CF8; font-size:11px; text-align:center; margin-top:20px;">
            "토스는 금융을 관리하는 앱, 핀핏은 금융을 시작하는 앱"
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── BEGINNER 5-STEP FLOW (exact layouts, stats, cards, selectors from TSX) ─────
elif st.session_state.onboarding_level == "beginner" and st.session_state.onboarding_step > 0:
    step = st.session_state.onboarding_step
    is_last = step == 5

    # === TOP PROGRESS (bars + prev + skip + count) matching TSX exactly ===
    bars = "".join(
        f'<div style="flex:1; height:3px; border-radius:99px; background:{"#8B5CF6" if i < step else "rgba(255,255,255,0.2)"}"></div>'
        for i in range(5)
    )

    # Layout: [이전] | bars | [건너뛰기]   + count line
    top_left, top_mid, top_right = st.columns([1.1, 4.2, 1.1])
    with top_left:
        if step > 1:
            if st.button("← 이전", key=f"prev_b_{step}"):
                go_prev()
                st.rerun()
    with top_mid:
        st.markdown(f"""
        <div style="padding-top:6px;">
            <div style="display:flex; gap:5px; align-items:center;">{bars}</div>
            <p style="color:#818CF8; font-size:11px; margin:6px 0 0 0;">{step} / 5</p>
        </div>
        """, unsafe_allow_html=True)
    with top_right:
        if st.button("건너뛰기", key=f"skip_beg_{step}"):
            complete_onboarding()

    # === MAIN CONTENT AREA - structure from original TSX BEGINNER_STEPS ===
    cur = BEGINNER_STEPS[step - 1]
    st.markdown(f"""
    <div style="text-align:center; margin:12px 0 18px;">
        <div style="font-size:48px; margin-bottom:12px;">{cur["emoji"]}</div>
        <h2 style="color:white; font-size:21px; font-weight:800; line-height:1.4; margin-bottom:8px; white-space:pre-line;">{cur["title"]}</h2>
        <p style="color:#A5B4FC; font-size:13px; line-height:1.6; white-space:pre-line;">
            {cur["desc"]}
        </p>
    </div>
    """, unsafe_allow_html=True)

    if step == 1:
        # Spending example rows (exact)
        for e, t, a in [
            ("☕", "카페 2번", "−12,000원"),
            ("🍕", "배달 시킴", "−18,000원"),
            ("🚕", "늦어서 택시", "−9,000원"),
            ("🛒", "편의점 들름", "−7,500원"),
        ]:
            st.markdown(f"""
            <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border-radius:12px; margin-bottom:8px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.1); color:#E0E7FF; font-size:13px;">
                <div style="display:flex; align-items:center; gap:10px;"><span style="font-size:20px;">{e}</span> <span>{t}</span></div>
                <span style="color:#FDA4AF; font-weight:600;">{a}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="display:flex; align-items:center; justify-content:space-between; padding:10px 14px; border-radius:12px; background:rgba(239,68,68,0.18); border:1px solid rgba(239,68,68,0.3); color:#FCA5A5; font-weight:700; font-size:13px; margin-top:4px;">
            <span>합계</span>
            <span style="font-size:14px; font-weight:700;">−46,500원</span>
        </div>
        """, unsafe_allow_html=True)

    elif step == 2:
        # Stat cards (exact big %)
        st.markdown("""
        <div style="border-radius:16px; padding:20px 18px; margin-bottom:12px; background:rgba(99,102,241,0.2); border:1px solid rgba(99,102,241,0.4);">
            <p style="color:#C7D2FE; font-size:40px; font-weight:900; margin-bottom:4px;">82.8%</p>
            <p style="color:white; font-size:14px; font-weight:700; margin-bottom:6px;">청년 혜택 어디서 찾는지 모름</p>
            <p style="color:#A5B4FC; font-size:12px; line-height:1.6;">
                "어디서 찾아야 할지 몰라요"<br/>"카드사마다 흩어져 한 번에 못 봐요"
            </p>
        </div>
        <div style="border-radius:16px; padding:20px 18px; background:rgba(139,92,246,0.2); border:1px solid rgba(139,92,246,0.4);">
            <p style="color:#DDD6FE; font-size:40px; font-weight:900; margin-bottom:4px;">58.6%</p>
            <p style="color:white; font-size:14px; font-weight:700; margin-bottom:6px;">자동 알림 기능이 필요해요</p>
            <p style="color:#A5B4FC; font-size:12px; line-height:1.6;">
                조건에 맞는 혜택이 생기면 바로 알려줬으면 좋겠어요
            </p>
        </div>
        """, unsafe_allow_html=True)

    elif step == 3:
        for e, title, desc, tag in [
            ("🔔", "청년 혜택 자동 알림", "흩어진 청년 혜택을 조건에 맞게 취합해 바로 알림", "관심 유발"),
            ("🤖", "AI 금융 용어 해설", "어려운 금융 용어를 AI가 실시간 쉽게 풀어드려요", "장벽 해소"),
            ("📚", "실생활 밀착형 금융 교육", "일상 사례로 금융 핵심 개념을 스토리텔링", "개념 이해"),
        ]:
            st.markdown(f"""
            <div style="display:flex; align-items:flex-start; gap:14px; padding:14px; border-radius:16px; margin-bottom:10px; background:rgba(99,102,241,0.15); border:1px solid rgba(99,102,241,0.4);">
                <div style="width:44px; height:44px; border-radius:12px; background:#6366F1; display:flex; align-items:center; justify-content:center; flex-shrink:0; font-size:20px;">{e}</div>
                <div style="flex:1;">
                    <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                        <span style="color:white; font-size:13px; font-weight:700;">{title}</span>
                        <span style="font-size:10px; padding:2px 6px; border-radius:99px; background:rgba(255,255,255,0.12); color:#C7D2FE;">{tag}</span>
                    </div>
                    <p style="color:#A5B4FC; font-size:11px; line-height:1.5; margin:0;">{desc}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    elif step == 4:
        for e, t, d, b in [
            ("🏦", "청년 우대형 청약통장", "연 최대 3.6% 금리 + 소득공제", "연간 최대 96만원"),
            ("💳", "청년 전용 적금", "일반 적금 대비 1~2% 높은 금리", "은행별 상이"),
            ("🎓", "국가·근로장학금", "성적·소득 기준 충족 시 신청", "연 최대 700만원"),
            ("🏠", "청년 주거급여", "만 30세 미만 독립 거주자 지원", "월 최대 33만원"),
        ]:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:12px; padding:11px 13px; border-radius:12px; margin-bottom:9px; background:rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.1);">
                <span style="font-size:22px; flex-shrink:0;">{e}</span>
                <div style="flex:1; min-width:0;">
                    <p style="color:white; font-size:13px; font-weight:600; margin:0 0 1px;">{t}</p>
                    <p style="color:#818CF8; font-size:11px; margin:0;">{d}</p>
                </div>
                <span style="font-size:10px; padding:3px 7px; border-radius:8px; flex-shrink:0; background:rgba(34,197,94,0.2); color:#86EFAC; white-space:nowrap;">{b}</span>
            </div>
            """, unsafe_allow_html=True)

    elif step == 5:
        pass  # selectors below use INCOMES/GOALS from original structure

        # INCOME LIST (exact selectable rows from prototype - using HTML + overlay cover button for pixel match)
        st.markdown('<p style="color:#C7D2FE; font-size:13px; font-weight:600; margin:0 0 8px 2px;">월 소득 · 용돈 범위</p>', unsafe_allow_html=True)

        current_income = st.session_state.onboarding_income
        for item in INCOMES:
            iid = item["id"]
            label = item["label"]
            sub = item["sub"]
            if current_income == iid:
                # exact selected HTML (matches TSX selected button style)
                st.markdown(f"""
                <div style="display:flex; align-items:center; justify-content:space-between; padding:11px 14px; border-radius:12px; margin-bottom:8px; background:rgba(99,102,241,0.28); border:2px solid #6366F1; color:white; font-size:13px;">
                    <span style="font-weight:700;">{label}</span>
                    <div style="display:flex; align-items:center; gap:7px;">
                        <span style="color:#818CF8; font-size:11px;">{sub}</span>
                        <span style="font-size:14px;">✓</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # button design - styled via .choice-btn CSS to match TSX unselected
                st.markdown('<div class="choice-btn">', unsafe_allow_html=True)
                if st.button(f"{label}\n{sub}", key=f"income_{iid}", use_container_width=True):
                    st.session_state.onboarding_income = iid
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # GOAL GRID (2-col exact from TSX - HTML cards + overlay for perfect unselected/selected look)
        st.markdown('<p style="color:#C7D2FE; font-size:13px; font-weight:600; margin:16px 0 8px 2px;">첫 번째 저축 목표</p>', unsafe_allow_html=True)

        current_goal = st.session_state.onboarding_goal

        # 2x2 + last row using columns, each item a choice - structure from original TSX GOALS
        for row_start in range(0, 5, 2):
            c1, c2 = st.columns(2)
            for col_idx, col in enumerate([c1, c2]):
                idx = row_start + col_idx
                if idx >= len(GOALS):
                    break
                item = GOALS[idx]
                gid = item["id"]
                emoji = item["e"]
                label = item["label"]
                sub = item["sub"]
                with col:
                    if current_goal == gid:
                        # exact selected from TSX (bg + border only, no extra check circle for goals)
                        st.markdown(f"""
                        <div style="display:flex; flex-direction:column; align-items:center; padding:14px 8px; border-radius:14px; background:rgba(99,102,241,0.28); border:2px solid #6366F1; margin-bottom:8px;">
                            <span style="font-size:26px; margin-bottom:5px;">{emoji}</span>
                            <span style="color:white; font-size:12px; font-weight:600; text-align:center;">{label}</span>
                            <span style="color:#818CF8; font-size:10px; text-align:center; margin-top:3px;">{sub}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # button design - styled via .choice-grid-btn CSS to match TSX grid card
                        st.markdown('<div class="choice-grid-btn">', unsafe_allow_html=True)
                        if st.button(f"{emoji}\n{label}\n{sub}", key=f"goal_{gid}", use_container_width=True):
                            st.session_state.onboarding_goal = gid
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<p style="color:#818CF8; font-size:11px; text-align:center; margin-top:8px;">나중에 언제든 바꿀 수 있어요</p>', unsafe_allow_html=True)

    # === BOTTOM CTA (exact gradient + conditional + skip below) ===
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    can_proceed = True
    if is_last and not st.session_state.onboarding_income:
        can_proceed = False

    cta_label = "시작하기 ✨" if is_last else "다음 →"
    if st.button(cta_label, key=f"cta_beg_{step}", disabled=not can_proceed, type="primary", use_container_width=True):
        if is_last:
            complete_onboarding()
        else:
            go_next()
            st.rerun()

    # Secondary skip under CTA (matches some flows)
    if st.button("건너뛰기", key=f"skip_under_{step}"):
        complete_onboarding()

# ── EXPERIENCED 2-STEP QUICK PATH (exact from prototype) ──────────────────────
elif st.session_state.onboarding_level == "experienced" and st.session_state.onboarding_step > 0:
    step = st.session_state.onboarding_step
    is_last = step == 2

    # Slightly different background tint for experienced (BG2)
    st.markdown("""
    <style>
    .stApp { background: linear-gradient(160deg,#0F0C29 0%,#1a1250 40%,#2D1F6B 75%,#3730A3 100%) !important; }
    </style>
    """, unsafe_allow_html=True)

    # TOP PROGRESS (2 steps)
    bars = "".join(
        f'<div style="flex:1;height:3px;border-radius:99px;background:{"#8B5CF6" if i < step else "rgba(255,255,255,0.2)"}"></div>'
        for i in range(2)
    )
    p1, p2, p3 = st.columns([1.1, 4.2, 1.1])
    with p1:
        if step > 1:
            if st.button("← 이전", key=f"prev_e_{step}"):
                go_prev()
                st.rerun()
    with p2:
        st.markdown(f"""
        <div style="padding-top:6px;">
            <div style="display:flex; gap:5px;">{bars}</div>
            <p style="color:#818CF8; font-size:11px; margin:6px 0 0;">{step} / 2</p>
        </div>
        """, unsafe_allow_html=True)
    with p3:
        if st.button("건너뛰기", key=f"skip_exp_{step}"):
            complete_onboarding()

    if step == 1:
        cur = EXP_STEPS[step - 1]
        st.markdown(f"""
        <div style="text-align:center; margin:10px 0 18px;">
            <div style="font-size:48px; margin-bottom:12px;">{cur["emoji"]}</div>
            <h2 style="color:white; font-size:21px; font-weight:800; line-height:1.4; margin-bottom:6px; white-space:pre-line;">{cur["title"]}</h2>
            <p style="color:#A5B4FC; font-size:13px;">{cur["desc"]}</p>
        </div>
        """, unsafe_allow_html=True)

        # 2x2 GRID exactly like prototype (big emoji top, label, sub, selected overlay) - from original
        cur_feat = st.session_state.onboarding_exp_feature

        for r in range(0, 4, 2):
            c1, c2 = st.columns(2, gap="medium")
            for ci, c in enumerate([c1, c2]):
                fi = r + ci
                if fi >= 4: break
                item = EXP_FEATURES[fi]
                emoji = item["e"]
                label = item["label"]
                sub = item["sub"]
                with c:
                    if cur_feat == label:
                        # exact selected from TSX
                        st.markdown(f"""
                        <div style="display:flex; flex-direction:column; align-items:flex-start; padding:15px; border-radius:16px; background:rgba(99,102,241,0.25); border:2px solid #6366F1; margin-bottom:10px; min-height:92px;">
                            <div style="font-size:28px; margin-bottom:8px;">{emoji}</div>
                            <p style="color:white; font-size:13px; font-weight:700; margin:0 0 2px;">{label}</p>
                            <p style="color:#818CF8; font-size:11px; line-height:1.4; margin:0;">{sub}</p>
                            <div style="margin-top:8px; align-self:flex-end; width:22px; height:22px; border-radius:50%; background:rgba(99,102,241,0.2); display:flex; align-items:center; justify-content:center;">
                                <span style="font-size:14px;">✓</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # button design - .choice-grid-btn CSS for TSX match
                        st.markdown('<div class="choice-grid-btn">', unsafe_allow_html=True)
                        if st.button(f"{emoji}\n{label}\n{sub}", key=f"expf_{label}", use_container_width=True):
                            st.session_state.onboarding_exp_feature = label
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

    elif step == 2:
        cur = EXP_STEPS[step - 1]
        st.markdown(f"""
        <div style="text-align:center; margin:8px 0 16px;">
            <div style="font-size:48px; margin-bottom:12px;">{cur["emoji"]}</div>
            <h2 style="color:white; font-size:21px; font-weight:800; line-height:1.4; margin-bottom:6px; white-space:pre-line;">{cur["title"]}</h2>
            <p style="color:#A5B4FC; font-size:13px;">{cur["desc"]}</p>
        </div>
        """, unsafe_allow_html=True)

        cur_inc = st.session_state.onboarding_income
        for item in INCOMES:
            iid = item["id"]
            label = item["label"]
            sub = item["sub"]
            if cur_inc == iid:
                st.markdown(f"""
                <div style="display:flex; align-items:center; justify-content:space-between; padding:12px 16px; border-radius:12px; margin-bottom:9px; background:rgba(99,102,241,0.25); border:2px solid #6366F1; color:white; font-size:13px;">
                    <span style="font-weight:700;">{label}</span>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="color:#818CF8; font-size:11px;">{sub}</span>
                        <span>✓</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown('<div class="choice-btn">', unsafe_allow_html=True)
                if st.button(f"{label}\n{sub}", key=f"expinc_{iid}", use_container_width=True):
                    st.session_state.onboarding_income = iid
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    # BOTTOM CTA + secondary text
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    can_proceed = True
    if is_last and not st.session_state.onboarding_income:
        can_proceed = False

    cta = "핀핏 시작하기 ✨" if is_last else "다음 →"
    if st.button(cta, key=f"cta_exp_{step}", disabled=not can_proceed, type="primary", use_container_width=True):
        if is_last:
            complete_onboarding()
        else:
            go_next()
            st.rerun()

    skip_label = "나중에 설정할게요" if is_last else "건너뛰기"
    if st.button(skip_label, key=f"skip_exp_under_{step}"):
        complete_onboarding()

# Fallback
else:
    st.warning("온보딩을 다시 시작합니다.")
    st.session_state.onboarding_step = 0
    st.rerun()
