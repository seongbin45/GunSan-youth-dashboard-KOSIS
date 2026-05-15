import streamlit as st

from finfit_youth.service import YouthDataService
from finfit_youth.scheduler import ensure_scheduler_started

st.set_page_config(page_title="청년 혜택", page_icon="🎁", layout="wide")
st.title("🎁 온통청년 실시간 정책/공간/콘텐츠")
st.caption("목록/검색은 캐시 데이터, 상세는 실시간 조회(단기 캐시) 방식으로 동작합니다.")

service = YouthDataService()
if "youth_scheduler" not in st.session_state:
    st.session_state.youth_scheduler = ensure_scheduler_started(service, interval_seconds=30 * 60)

left, right = st.columns([2, 1])
with left:
    source_label = st.selectbox("데이터 구분", ["정책", "공간", "콘텐츠"], index=0)
    source_map = {"정책": "policy", "공간": "space", "콘텐츠": "content"}
    source = source_map[source_label]

    query = st.text_input("검색어", placeholder="예: 취업, 주거, 금융")
    page = st.number_input("페이지", min_value=1, value=1, step=1)
    size = st.selectbox("페이지 크기", [10, 20, 30], index=0)

    refresh_clicked = st.button("지금 동기화")
    if refresh_clicked:
    with st.spinner("동기화 중..."):
        try:
            result = service.sync_source(source)
            st.success(f"{source_label} 동기화 완료: {result['count']}건")
        except Exception as e:
            st.error(f"동기화 실패: {e}")
            st.stop()


with right:
    st.info(
        "운영 안내\n\n"
        "- API 키는 환경변수로 설정하세요(`YOUTH_API_KEY`)\n"
        "- 30분 주기 자동 동기화\n"
        "- 외부 API 오류 시 직전 스냅샷 폴백"
    )

try:
    result = service.get_list(source=source, query=query, page=int(page), size=int(size))
except Exception as exc:
    st.error(f"목록 조회 실패: {exc}")
    st.stop()

st.divider()
st.write(f"총 {result['total']}건")

items = result["items"]
if not items:
    st.warning("표시할 데이터가 없습니다. API 키/엔드포인트 설정을 확인해주세요.")

for item in items:
    title = item.get("title") or "제목 없음"
    summary = item.get("summary") or "요약 정보 없음"
    region = item.get("region") or "지역 정보 없음"
    item_id = item.get("id") or ""

    with st.expander(f"{title} ({region})"):
        st.write(summary)
        if item_id:
            if st.button("상세 실시간 조회", key=f"detail-{source}-{item_id}"):
                try:
                    detail = service.get_detail(source=source, item_id=item_id)
                    st.json(detail)
                except Exception as exc:
                    st.error(f"상세 조회 실패: {exc}")
        else:
            st.caption("상세 조회를 위한 식별자가 없어 목록 데이터만 표시합니다.")
