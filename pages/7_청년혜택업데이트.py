from __future__ import annotations
import time  # 1. 시간 제어 모듈 추가
from datetime import UTC, datetime, timezone, timedelta

import streamlit as st

from finfit_youth.scheduler import ensure_scheduler_started
from finfit_youth.service import YouthDataService


st.set_page_config(page_title="청년 혜택 업데이트", page_icon="🎁", layout="wide")


def _format_age(seconds: int | None) -> str:
    if seconds is None:
        return "데이터 없음"
    if seconds < 60:
        return f"{seconds}초 전"
    if seconds < 3600:
        return f"{seconds // 60}분 전"
    if seconds < 86400:
        return f"{seconds // 3600}시간 전"
    return f"{seconds // 86400}일 전"


def _format_sync(value: str | None) -> str:
    if not value:
        return "동기화 기록 없음"
    try:
        # 1. ISO 포맷(UTC)을 한국 시간(KST)으로 변환
        dt = datetime.fromisoformat(value)
        korea_tz = timezone(timedelta(hours=9))
        korea_dt = dt.astimezone(korea_tz)
        
        # 2. 현재 한국 시간 가져오기
        now = datetime.now(korea_tz)
        
        # 3. 날짜 차이 계산
        days_diff = (now.date() - korea_dt.date()).days
        
        # 4. 오전/오후 및 12시간제 변환 (예: 오후 2시 30분)
        ampm = "오후" if korea_dt.hour >= 12 else "오전"
        hour12 = korea_dt.hour % 12
        if hour12 == 0:
            hour12 = 12
        time_str = f"{ampm} {hour12}시 {korea_dt.minute:02d}분"
        
        # 5. 차이에 따라 완벽하게 일상적인 말로 반환
        if days_diff == 0:
            return f"{time_str}"
        elif days_diff == 1:
            return f"어제 {time_str}"
        elif days_diff == 2:
            return f"그저께 {time_str}"
        else:
            # 3일 이상 지났으면 자연스러운 날짜와 시간 표시
            return f"{korea_dt.year}년 {korea_dt.month}월 {korea_dt.day}일 {time_str}"
            
    except ValueError:
        return value.replace("T", " ").replace("+00:00", " UTC")


# --- 메인 실행부 ---
st.title("청년 혜택 업데이트")
t.caption(
    "현재는 공공 API 기반 동기화 구조와 캐시 시스템을 구현했고, "
    "주기적 자동화는 차기 단계에서 확장 가능합니다."
)

service = YouthDataService()
if "youth_scheduler" not in st.session_state:
    st.session_state.youth_scheduler = ensure_scheduler_started(service, interval_seconds=30 * 60)

# 세션 상태 초기화 (검색어 유지)
if "query" not in st.session_state: st.session_state.query = ""

source_label = st.selectbox("데이터 구분", ["정책", "청년센터", "콘텐츠"], index=0)
source_map = {"정책": "policy", "청년센터": "center", "콘텐츠": "content"}
source = source_map[source_label]

status = service.get_source_status(source)

# --- 📊 사용자 친화적으로 개선된 운영 상태 대시보드 ---
# st.info 대신 테두리가 있는 컨테이너를 사용하여 요소들을 깔끔하게 그룹화합니다.
with st.container(border=True):
    st.subheader("📊 운영 상태 대시보드")
    st.caption("현재 데이터의 수집 상태와 시스템 연결 상황을 실시간으로 확인합니다.")
    
    # 상태에 따른 시각적 단서(이모지) 배정
    api_status_display = "🟢 원활" if status["api_status"] == "정상" else f"🔴 {status['api_status']}"
    cache_status_display = "🟢 작동 중" if status["cache_status"] == "정상" else f"🟡 {status['cache_status']}"
    fallback_display = "⚠️ 백업 데이터 표시" if status["fallback_used"] else "🟢 실시간 연결"
    
    cols1 = st.columns(3)
    cols1[0].metric(
        label="마지막 업데이트", 
        value=_format_sync(status["last_synced_at"]),
        help="정부 공공 데이터가 마지막으로 당겨져 온 시간입니다."
    )
    cols1[1].metric(
        label="데이터 신뢰도", 
        value=_format_age(status["cache_age_seconds"]),
        help="현재 보고 계신 혜택 정보가 얼마 전 기준으로 작성되었는지 나타냅니다."
    )
    cols1[2].metric(
        label="제공 중인 혜택", 
        value=f"{status['item_count']}개",
        help="현재 시스템에서 조회 가능한 전체 청년 혜택의 개수입니다."
    )
    
    st.markdown("<br>", unsafe_allow_html=True) # 위아래 줄 여백
    
    cols2 = st.columns(3)
    cols2[0].metric(
        label="공공 서버 통신", 
        value=api_status_display,
        help="국가 공공 데이터 포털과의 현재 통신 상태입니다."
    )
    cols2[1].metric(
        label="동기화 시스템", 
        value=cache_status_display,
        help="속도를 높이기 위한 내부 임시 저장소(캐시) 상태입니다."
    )
    cols2[2].metric(
        label="데이터 제공 방식", 
        value=fallback_display,
        help=  
           "🟢 **실시간 연결**: 가장 최신 데이터를 보여줍니다.  \n"
        "⚠️ **백업 데이터 표시**: 공공 서버 지연 시 임시로 저장된 데이터를 보여줍니다."
    )
# --------------------------------------------------------

if st.button("지금 동기화", use_container_width=True):
    with st.spinner("공공 API 동기화 중..."):
        try:
            result = service.sync_source(source)
            st.success(f"{source_label} 동기화 완료: {result['count']}건")
        except Exception as exc:
            service.record_source_error(source, str(exc))
            st.error(f"동기화 실패: {exc}")

st.divider()

query = st.text_input("검색어", placeholder="예: 취업, 주거, 금융")
st.session_state.query = query # 상태 업데이트
size = st.selectbox("표시 개수", [10, 20, 30, 50, 100], index=1)

st.divider()

# 데이터 목록 조회
result = service.get_list(source=source, query=query, page=1, size=int(size))
st.write(f"총 {result['total']}건")
if result.get("fallback_used"):
    st.warning("외부 API 조회가 실패해 저장된 캐시 데이터를 표시하고 있습니다.")

# 데이터 표시 (중복 루프 제거)
for idx, item in enumerate(result["items"]):
    title = item.get("title") or "제목 없음"
    summary = item.get("summary") or "요약 정보 없음"
    region = item.get("region") or "지역 정보 없음"
    item_id = item.get("id") or ""

    with st.expander(f"{title} ({region})"):
        st.write(summary)
        if item_id and st.button("상세 실시간 조회", key=f"detail-{source}-{item_id}-{idx}"):
            try:
                detail = service.get_detail(source=source, item_id=item_id)
                st.json(detail)
            except Exception as exc:
                st.error(f"상세 조회 실패: {exc}")

st.caption(f"화면 확인 시각: {datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%d %H:%M:%S')}")

# 30초 대기 후 자동 새로고침
time.sleep(30)
st.rerun()
