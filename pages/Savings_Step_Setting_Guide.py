import streamlit as st
import textwrap
import plotly.graph_objects as go
from finfit_youth.config import inject_finfit_theme, LEVELS, calculate_budget, render_feedback_form

st.set_page_config(page_title="저축단계 상세", page_icon="🎯", layout="wide")
inject_finfit_theme()

st.markdown("""
<style>
.stApp { background: #111111 !important; }
</style>
""", unsafe_allow_html=True)

# Header TSX Savings style (dark)
st.markdown(textwrap.dedent("""
<div style="background:#1a1a1a; padding:12px 16px; margin:-8px -8px 8px; border-bottom:1px solid #333;">
  <div style="display:flex; align-items:center; gap:12px;">
    <div style="font-size:20px; font-weight:700; color:#f0f0f0;">💎 저축 목표 & 단계 가이드</div>
  </div>
</div>
"""), unsafe_allow_html=True)

# Step progress - TSX like
current_level = st.session_state.get("level", 5)
steps_html = ""
for i in range(1, 11):
    active = "background:#6366F1; color:white;" if i == current_level else "background:#222; color:#888;"
    steps_html += f'<div style="flex:1; text-align:center; {active} padding:4px 2px; border-radius:4px; font-size:10px; font-weight:600;">{i}</div>'

st.markdown(textwrap.dedent(f"""
<div style="margin:8px 0;">
  <div style="display:flex; gap:3px; height:22px;">{steps_html}</div>
  <div style="height:4px; background:#333; border-radius:999px; margin-top:4px;">
    <div style="width:{current_level*10}%; height:100%; background:#6366F1; border-radius:999px;"></div>
  </div>
  <p style="color:#888; font-size:10px; margin-top:2px;">저축 강도 1(여가 우선) → 10(생존형) | 현재 {current_level}단계</p>
</div>
"""), unsafe_allow_html=True)

if "income" not in st.session_state:
    st.session_state.income = 2000000
    st.session_state.income_touched = False
if "level" not in st.session_state:
    st.session_state.level = 5

income = st.session_state.income
level  = st.session_state.level

st.markdown(f"**✅ 현재 선택: {level}단계 — {LEVELS[level]['name']}**")

budget = calculate_budget(income, level)
lv = budget["level_info"]

# Goal cards - TSX style
c1, c2, c3 = st.columns(3)
for col, (label, ratio, color) in zip([c1, c2, c3], [("💎 저축", lv["save"], lv["color"]), ("🏠 고정비", lv["fix"], "#2196F3"), ("🎉 여가·식비", lv["leisure"], "#4CAF50")]):
    amt = int(income * ratio)
    col.markdown(textwrap.dedent(f"""
    <div style="text-align:center; background:#1a1a1a; border:1px solid #333; border-radius:12px; padding:12px; margin-bottom:8px;">
      <div style="font-size:11px; color:#888;">{label}</div>
      <div style="font-size:22px; font-weight:700; color:#f0f0f0; margin:4px 0;">{int(ratio*100)}%</div>
      <div style="font-size:12px; color:#aaa;">{amt:,}원</div>
    </div>
    """), unsafe_allow_html=True)

st.markdown("**💡 이 단계 실천 팁**")
for tip in lv["tips"]:
    st.markdown(f"- {tip}")

st.divider()

# Savings goals simulation - closer to TSX Savings.tsx list + add
st.markdown("**저축 목표 목록 (TSX 스타일)**")

if "savings_goals" not in st.session_state:
    st.session_state.savings_goals = [
        {"title": "비상금", "icon": "🛡️", "target": 3000000, "current": 1200000, "monthly": 200000, "color": "#6366F1"}
    ]

for g in st.session_state.savings_goals:
    progress = min(100, int(g["current"] / g["target"] * 100)) if g["target"] > 0 else 0
    st.markdown(textwrap.dedent(f"""
    <div style="background:#1a1a1a; border:1px solid #333; border-radius:12px; padding:10px; margin-bottom:6px; display:flex; align-items:center; gap:10px;">
      <div style="font-size:22px;">{g['icon']}</div>
      <div style="flex:1;">
        <div style="font-weight:600; color:#f0f0f0;">{g['title']}</div>
        <div style="background:#222; height:6px; border-radius:3px; margin:4px 0;">
          <div style="width:{progress}%; height:100%; background:{g['color']}; border-radius:3px;"></div>
        </div>
        <div style="font-size:10px; color:#888;">{g['current']:,} / {g['target']:,}원 ({progress}%)</div>
      </div>
      <div style="text-align:right; font-size:11px;">
        <div style="color:#10B981;">+{g['monthly']:,}원/월</div>
        <div style="color:#888;">{g.get('dueMonths', '?')}개월</div>
      </div>
    </div>
    """), unsafe_allow_html=True)

with st.expander("➕ 목표 추가 / 수정 (TSX 모달 스타일)"):
    title = st.text_input("목표명", "비상금")
    icon = st.selectbox("아이콘", ["🛡️", "✈️", "📱", "🏠", "🚗", "🎓", "💍", "🎮", "💻", "🌏"])
    target = st.number_input("목표 금액", value=3000000, step=100000)
    current = st.number_input("현재 금액", value=1200000, step=100000)
    monthly = st.number_input("매월 저축", value=200000, step=10000)
    if st.button("저장"):
        st.session_state.savings_goals.append({"title": title, "icon": icon, "target": target, "current": current, "monthly": monthly, "color": "#6366F1"})
        st.rerun()

st.divider()
st.subheader("📈 저축 목표 시뮬레이션")
months = st.slider("몇 개월 후 목표 확인?", 1, 36, 12)
monthly_save = budget["save"]
total_save = monthly_save * months
st.success(f"**{months}개월 후 예상 저축액: {total_save:,}원** (월 {monthly_save:,}원 × {months}개월)")

st.write("---")

# (removed duplicate set_page_config and local LEVELS redefinition - using centralized from finfit_youth.config)
st.session_state.LEVELS = LEVELS  # ensure shared reference
    

# 전체 단계 비교표
st.subheader("📊 전체 단계 비교")
levels_list = list(LEVELS.items())
fig = go.Figure()
fig.add_bar(name="저축", x=[f"{k}단계" for k,_ in levels_list],
            y=[v["save"]*100 for _,v in levels_list], marker_color="#9C27B0")
fig.add_bar(name="고정비", x=[f"{k}단계" for k,_ in levels_list],
            y=[v["fix"]*100 for _,v in levels_list], marker_color="#2196F3")
fig.add_bar(name="여가·식비", x=[f"{k}단계" for k,_ in levels_list],
            y=[v["leisure"]*100 for _,v in levels_list], marker_color="#4CAF50")
fig.update_layout(barmode="stack", height=350,
                  yaxis_title="비율 (%)", margin=dict(l=10,r=10,t=10,b=10))
st.plotly_chart(fig, use_container_width=True)

st.write("---")

# ── 메인 화면 ─────────────────────────────────────────────────────────────────

col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📋 본인의 정보가 맞는지 확인")
    income = st.number_input(
        "월 소득 / 용돈 (원)",
        min_value=10000, max_value=10000000,
        value=int(st.session_state.income), step=10000,
        format="%d",
    )
    if int(income) != int(st.session_state.get("income") or 0):
        st.session_state.income_touched = True
    st.session_state.income = int(income)

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

    

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
### github.com 주소 뒤에 ?raw=true 추가
github_image_url = "https://github.com/seongbin45/GunSan-youth-dashboard-KOSIS/blob/9a0bf10dfd74407e81691b274a1b8e9f690e7104/tests/Image/%EC%A0%9C%EB%AA%A9%EC%9D%84%20%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94.%20(7).png?raw=true"

### 스트림릿에 이미지 출력
st.image(github_image_url, use_container_width=True)

# 공통 피드백 폼만 사용 (동일 text_area 중복 시 StreamlitDuplicateElementId 발생)
render_feedback_form(key_prefix="savings_guide")


