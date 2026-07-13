import streamlit as st

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 푸터
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
### github.com 주소 뒤에 ?raw=true 추가
github_image_url = "https://github.com/seongbin45/GunSan-youth-dashboard-KOSIS/blob/9a0bf10dfd74407e81691b274a1b8e9f690e7104/tests/Image/%EC%A0%9C%EB%AA%A9%EC%9D%84%20%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94.%20(7).png?raw=true"

### 스트림릿에 이미지 출력
st.image(github_image_url, use_container_width=True)

# 1. ⚠️ 핵심 개선점: 캐싱 추가 (55분마다 한 번만 구글 인증 수행)
@st.cache_resourc(ttl=3300)
def get_gspread_client():
    # Secrets에서 통째로 저장된 JSON 문자열을 가져옴
    json_string = st.secrets["gspread_json"]
    
    # 문자열을 파이썬 딕셔너리로 변환
    credentials = json.loads(json_string)
    
    # 구글 서비스 계정 인증 수행
    gc = gspread.service_account_from_dict(credentials)
    return gc

# UI 안내 문구 출력
st.markdown("### 서비스 의견 남기기")
st.markdown("""
**저희는 더 나은 경험을 드리기 위해   
꾸준히 준비 중입니다.**  

소중한 의견을 들려주시면,  
서비스 개선에 큰 도움이 됩니다!  

🔒 개인정보 보호 |
"""
    '<a href="https://docs.google.com/forms/d/e/1FAIpQLSco-O4cGhbt1iMOwrEkqX5Vt0-8ctAtCxM5Z6JjmFlP-Uqq-Q/viewform?usp=header" target="_blank"><button style="color: peach;">💌 설문 링크로 이동</button></a>', 
    unsafe_allow_html=True 
           )

# 의견 입력 창
user_feedback = st.text_area(
    "자유롭게 적어주세요 👇", 
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


