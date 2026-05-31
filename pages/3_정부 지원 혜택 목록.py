import streamlit as st
import pandas as pd

from finfit_youth.scheduler import ensure_scheduler_started
from finfit_youth.service import YouthDataService

st.set_page_config(page_title="청년 혜택 정보", page_icon="🎁", layout="wide")
st.title("🎁 청년을 위한 국가 금융 지원 상품")
st.caption("2024~2025년 기준 / 자세한 내용은 각 공식 사이트에서 확인하세요")

data = [
    {"분류":"적금·저축",  "상품명":"청년도약계좌",
     "대상":"만 19~34세, 연소득 7,500만원 이하",
     "혜택":"월 최대 70만원 납입 → 정부 기여금 + 비과세 혜택, 5년 만기",
     "신청":"은행 앱 (국민·신한·하나·우리·농협 등)", "🔗":"https://www.kinfa.or.kr"},
    {"분류":"적금·저축",  "상품명":"청년희망적금 (종료)",
     "대상":"만 19~34세, 연소득 3,600만원 이하",
     "혜택":"2년 만기, 저축장려금 + 비과세 (신규 모집 종료, 참고용)",
     "신청":"—", "🔗":""},
    {"분류":"주거",       "상품명":"청년월세 한시 특별지원",
     "대상":"만 19~34세 독립거주 청년, 소득 기준 충족",
     "혜택":"월 최대 20만원 × 12개월 (240만원) 현금 지원",
     "신청":"복지로 (bokjiro.go.kr)", "🔗":"https://www.bokjiro.go.kr"},
    {"분류":"주거",       "상품명":"청년 전세임대주택",
     "대상":"대학생·취준생·만 19~39세 사회초년생",
     "혜택":"기존 주택 전세계약 후 저렴하게 재임대, 최장 6년 거주",
     "신청":"LH 청약센터", "🔗":"https://apply.lh.or.kr"},
    {"분류":"취업·소득",  "상품명":"국민취업지원제도",
     "대상":"만 15~69세 취업취약계층 (청년 우선)",
     "혜택":"구직촉진수당 월 50만원 × 6개월 + 취업지원 서비스",
     "신청":"워크넷 (work.go.kr)", "🔗":"https://www.work.go.kr"},
    {"분류":"취업·소득",  "상품명":"청년내일채움공제 (청년형)",
     "대상":"중소·중견기업 취업 청년 (만 15~34세)",
     "혜택":"2년간 청년 400만원 + 기업·정부 지원 → 총 1,200만원",
     "신청":"청년내일채움공제 포털", "🔗":"https://www.work.go.kr/youngtomorrow"},
    {"분류":"신용·금융",  "상품명":"햇살론유스",
     "대상":"만 19~34세, 연소득 3,500만원 이하 또는 신용점수 하위 20%",
     "혜택":"최대 1,200만원 저금리 대출 (연 3.5~4.5%)",
     "신청":"서민금융진흥원, 농협·신협 등", "🔗":"https://www.kinfa.or.kr"},
    {"분류":"신용·금융",  "상품명":"청년 신용회복 지원",
     "대상":"소액 연체 청년",
     "혜택":"채무조정, 신용상담, 금융교육 지원",
     "신청":"신용회복위원회", "🔗":"https://www.ccrs.or.kr"},
    {"분류":"교육·자기계발","상품명":"국민내일배움카드",
     "대상":"만 15세 이상 취업·재직·자영업자",
     "혜택":"5년간 300~500만원 직업훈련비 지원",
     "신청":"HRD-Net (hrd.go.kr)", "🔗":"https://www.hrd.go.kr"},
]

df = pd.DataFrame(data)

categories = ["전체"] + sorted(df["분류"].unique().tolist())
selected   = st.selectbox("분류 필터", categories)
keyword    = st.text_input("🔍 검색 (상품명·혜택 키워드)")

filtered = df.copy()
if selected != "전체":
    filtered = filtered[filtered["분류"] == selected]
if keyword:
    mask = (filtered["상품명"].str.contains(keyword, case=False) |
            filtered["혜택"].str.contains(keyword, case=False))
    filtered = filtered[mask]

st.divider()
for _, row in filtered.iterrows():
    with st.expander(f"**{row['상품명']}** — {row['분류']}"):
        st.markdown(f"**대상:** {row['대상']}")
        st.markdown(f"**혜택:** {row['혜택']}")
        st.markdown(f"**신청:** {row['신청']}")
        if row["🔗"]:
            st.markdown(f"[🌐 공식 사이트 바로가기]({row['🔗']})")

st.divider()
st.caption("📌 지원 내용은 정부 정책 변경에 따라 달라질 수 있습니다. 반드시 공식 사이트에서 최신 정보를 확인하세요.")
st.divider()


st.set_page_config(page_title="청년 혜택", page_icon="🎁", layout="wide")

st.title("🎁 온통청년 실시간 정책/청년센터/콘텐츠")
st.caption("목록/검색은 캐시 데이터, 상세는 실시간 조회(단기 캐시) 방식으로 동작합니다.")

service = YouthDataService()
if "youth_scheduler" not in st.session_state:
    st.session_state.youth_scheduler = ensure_scheduler_started(service, interval_seconds=30 * 60)

left, right = st.columns([2, 1])

with left:
    source_label = st.selectbox("데이터 구분", ["정책", "청년센터", "콘텐츠"], index=0)
    source_map = {"정책": "policy", "청년센터": "center", "콘텐츠": "content"}
    source = source_map[source_label]

    query = st.text_input("검색어", placeholder="예: 취업, 주거, 금융")

    size_label = st.selectbox("한 화면에 표시할 목록 개수", [10, 20, 30, 50, 100, "Max"], index=2)
    size = 9999 if size_label == "Max" else int(size_label)

    if size_label == "Max":
        page = 1
        st.caption("Max 선택 시 페이지는 1개로 고정됩니다.")
    else:
        page = st.number_input("페이지 번호", min_value=1, value=1, step=1)

    refresh_clicked = st.button("지금 동기화")
    if refresh_clicked:
        with st.spinner("동기화 중..."):
            try:
                result = service.sync_source(source)
                st.success(f"{source_label} 동기화 완료: {result['count']}건")
            except Exception as e:
                msg = str(e)
                if source == "content" and ("403" in msg or "400" in msg):
                    st.error("동기화 실패: 콘텐츠 API 키 권한 또는 파라미터(apiKeyNm/pageType/pstSn/rtnType)를 확인해주세요.")
                elif source == "center" and ("403" in msg or "400" in msg):
                    st.error("동기화 실패: 청년센터 API 키 권한 또는 파라미터(apiKeyNm/pageType/plcSn/rtnType)를 확인해주세요.")
                else:
                    st.error(f"동기화 실패: {e}")
                st.stop()

with right:
    st.info(
        "운영 안내\n\n"
        "- 정책/청년센터/콘텐츠 API 키를 각각 설정하세요(`YOUTH_API_KEY`, `YOUTH_CENTER_API_KEY`, `YOUTH_CONTENT_API_KEY`)\n"
        "- 30분 주기 자동 동기화\n"
        "- 외부 API 오류 시 직전 스냅샷 폴백"
    )

try:
    result = service.get_list(source=source, query=query, page=int(page), size=int(size))
except Exception as e:
    st.error(f"목록 조회 실패: {e}")
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
    raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}

    with st.expander(f"{title} ({region})"):
        st.write(summary)

        if source == "center":
            tel = raw.get("cntrTelno") or "전화번호 정보 없음"
            addr = " ".join(
                x for x in [str(raw.get("cntrAddr") or "").strip(), str(raw.get("cntrDaddr") or "").strip()] if x
            ) or "주소 정보 없음"
            url = raw.get("cntrUrlAddr")

            st.caption(f"전화: {tel}")
            st.caption(f"주소: {addr}")
            if url:
                st.markdown(f"센터 URL: [{url}]({url})")

        if item_id:
            if st.button("상세 실시간 조회", key=f"detail-{source}-{item_id}"):
                try:
                    detail = service.get_detail(source=source, item_id=item_id)
                    st.json(detail)
                except Exception as e:
                    msg = str(e)
                    if source == "content" and ("403" in msg or "400" in msg):
                        st.error("상세 조회 실패: 콘텐츠 API 권한 또는 상세 파라미터(pstSn/pageType/rtnType)를 확인해주세요.")
                    elif source == "center" and ("403" in msg or "400" in msg):
                        st.error("상세 조회 실패: 청년센터 API 권한 또는 상세 파라미터(plcSn/pageType/rtnType)를 확인해주세요.")
                    else:
                        st.error(f"상세 조회 실패: {e}")
        else:
            st.caption("상세 조회를 위한 식별자가 없어 목록 데이터만 표시합니다.")

st.divider()
st.caption("📌 정부 지원 사이트 목록은 온통청년 API를 사용하여, 30분 주기로 자동 동기화 됩니다.")
st.divider()
