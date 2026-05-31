import streamlit as st
import gspread
import json
from datetime import datetime

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
    st.divider()

    
    
# 1. ⚠️ 핵심 개선점: 캐싱 추가 (55분마다 한 번만 구글 인증 수행)
@st.cache_resource(ttl=3300)
def get_gspread_client():
    # Secrets에서 통째로 저장된 JSON 문자열을 가져옴
    json_string = st.secrets["gspread_json"]
    
    # 문자열을 파이썬 딕셔너리로 변환
    credentials = json.loads(json_string)
    
    # 구글 서비스 계정 인증 수행
    gc = gspread.service_account_from_dict(credentials)
    return gc
    
# UI 안내 문구 출력
st.title("💌 서비스 의견 공유")
st.markdown("""
**저희는 더 나은 경험을 드리기 위해   
꾸준히 준비 중입니다.**  

소중한 의견을 들려주시면,  
서비스 개선에 큰 도움이 됩니다!  

🔒 개인정보 보호 | 📧 : choiseongbin45@gmail.com
""")

# 의견 입력 창
user_feedback = st.text_area(
    "의견을 자유롭게 적어주세요 👇", 
    placeholder="예: 이런 기능이 추가되면 좋겠어요 / 이 부분이 사용하기 조금 불편해요"
)

# 의견 남기기 버튼 (CTA)
if st.button("피드백 남기기", use_container_width=True):
    if user_feedback.strip() == "":
        st.warning("내용을 입력한 후 버튼을 눌러주세요! ⚠️")
    else:
        try:
            # 2. 구글 인증 및 시트 열기 (이제 캐시된 클라이언트를 빠르게 불러옴)
            gc = get_gspread_client()
            sh = gc.open_by_key(st.secrets["spreadsheet_id"])
            
            # 시트 이름으로 명확하게 지정하는 것을 권장하나, 인덱스(0)도 무방합니다.
            worksheet = sh.get_worksheet(0) 
            
            # 3. 데이터 추가
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            worksheet.append_row([current_time, user_feedback])
            
            # 4. 제출 성공 완료 메시지 및 시각 효과
            st.balloons()
            st.success("""
            🎉 **소중한 피드백이 성공적으로 전달되었어요!**  
            보내주신 다정한 말씀과 조언은  
            서비스 개선에 적극 반영하겠습니다.  
            앞으로도 많은 기대 부탁드려요! 🙏
            """)
            
        except Exception as e:
            st.error(f"데이터 저장 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요: {e}")



