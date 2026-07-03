🚀 군산시 청년 정책 매칭 대시보드 개발 히스토리 및 전체 코드
본 문서는 Streamlit을 활용한 군산시 청년 정책 맞춤형 매칭 대시보드의 개발 과정과 모든 오류가 해결된 최종 완성본 코드를 기록한 문서입니다.
🛠️ 1. 주요 해결 이슈 및 디버깅 히스토리
① 파이썬 문법 파괴자, 유령 공백(U+00A0) 제거
증상: 코드를 복사/붙여넣기 하는 과정에서 웹 특수 공백 문자인 U+00A0가 코드 들여쓰기와 빈 줄에 대거 섞여 들어옴.
결과: 파이썬이 이를 정상적인 공백(Space)으로 인식하지 못해 끊임없이 SyntaxError를 발생시킴.
해결: 1번부터 5번 섹션까지 모든 구역의 유령 문자를 표준 공백으로 치환하고 들여쓰기를 완벽히 재정렬함.
② 변수 이름 불일치 및 미정의 변수(NameError) 해결
증상: life_match vs asset_match_count, trial_match_count 등 각 섹션의 카운트 변수 이름이 엇갈리거나, 상단에 선언되지 않은 나이 변수(is_transition_35_39, is_mid_40_69)를 하단 조건문에서 사용함.
해결: 각 섹션의 카운트 변수명을 일치시키고, 누락된 조건 변수들을 안전하게 선언 및 할당함.
③ 논리 오류(Bug) 해결: 소득 기준 초과자 필터링
증상: 소득 기준을 "해당 없음 (소득 기준 초과)"으로 선택했음에도 저소득층 전용 사업인 '국민취업지원제도 1유형'이 화면에 노출됨.
해결: is_under_120 등의 소득 매칭 로직이 엉켜있던 것을 파악하고, is_over_limit 변수를 최우선으로 검사하여 소득 기준 초과 시 하위 모든 소득 조건(60%, 100%, 120% 등)이 일괄 False 처리되도록 로직을 견고하게 재구축함.
🎨 2. UI/UX 개선 사항
① 조건 입력창 가독성 극대화 (st.multiselect)
기존에 세로로 길게 늘어지던 라디오 버튼 형태의 직업/상태 입력 방식을 다중 키워드 선택창(st.multiselect)으로 변경.
이에 맞춰 job_status라는 단일 변수 대신 is_unemployed, is_worker, is_founder 등의 다중 논리 변수(Boolean) 시스템으로 코드 전체를 리팩토링함.
② 항목별 아코디언 메뉴 도입 (st.expander)
조건에 맞는 정책이 많을 경우 스크롤이 무한정 길어지는 문제를 해결하기 위해, 1번~5번 섹션의 모든 개별 정책을 접이식 메뉴(st.expander)로 감싸 화면을 깔끔하게 콤팩트화함.
③ CSS 주입을 통한 커스텀 아웃라인 버튼
Streamlit의 기본 꽉 찬 버튼 대신, 커스텀 CSS(st.markdown(unsafe_allow_html=True))를 주입하여 테두리만 있는 세련된 트랜지션 버튼(Outline Button)을 구현함.
💻 3. 최종 통합 완성 코드 (에러 제로 보장)
아래 코드를 복사하여 app.py 등의 파일에 그대로 붙여넣고 실행하시면 됩니다.
import streamlit as st

# ---------------------------------------------------------
# 🎨 UI 커스텀: 테두리 아웃라인 버튼 CSS 주입
# ---------------------------------------------------------
st.markdown("""
    <style>
    div.stButton > button {
        background-color: transparent !important;
        color: #FF4B4B !important; 
        border: 2px solid #FF4B4B !important;
        border-radius: 8px !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 📋 조건 입력 구역 (Expander & Multiselect 활용)
# ---------------------------------------------------------
with st.expander("📋 나의 맞춤 조건 설정하기 (클릭하여 열기/닫기)", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("만 나이", min_value=15, max_value=69, value=25)
    with col2:
        income_level = st.selectbox("가구 소득 수준", [
            "60% 이하 (저소득층 및 집중 주거지원 대상)",
            "100% 이하",
            "140% 이하",
            "150% 이하",
            "180% 이하",
            "해당 없음 (소득 기준 초과)"
        ])
    with col3:
        has_house = st.radio("주택 소유 여부", ["무주택", "유주택"], horizontal=True)

    st.write("")
    st.markdown("**💡 나에게 해당하는 키워드를 모두 선택하세요 (복수 선택 가능)**")
    
    keyword_options = [
        "미취업 (구직 중)", "취업자 (군산 소재 기업)", "창업자 (7년 미만)",
        "농업 종사 (청년창업농 등)", "신혼부부", "다자녀 가구"
    ]
    
    selected_keywords = st.multiselect(
        "해당하는 조건을 클릭하거나 검색하여 추가하세요.",
        options=keyword_options,
        default=["미취업 (구직 중)"]
    )

st.write("---")

# ---------------------------------------------------------
# 🚀 알고리즘 구동 및 조건 변수 생성
# ---------------------------------------------------------
if st.button("내 맞춤 혜택 결과 보기 🚀"):
    st.success("🎉 입력하신 조건에 부합하는 군산시 청년 정책 매칭 결과입니다.")
    
    # 1. 나이 조건 변수
    is_youth_18_34 = 18 <= age <= 34
    is_youth_19_34 = 19 <= age <= 34
    is_youth_18_39 = 18 <= age <= 39
    is_youth_19_39 = 19 <= age <= 39
    is_transition_35_39 = 35 <= age <= 39
    is_mid_40_69 = 40 <= age <= 69

    # 2. 키워드 체크용 변수
    is_unemployed = "미취업 (구직 중)" in selected_keywords
    is_worker = "취업자 (군산 소재 기업)" in selected_keywords
    is_founder = "창업자 (7년 미만)" in selected_keywords
    is_farmer = "농업 종사 (청년창업농 등)" in selected_keywords
    is_newlywed = "신혼부부" in selected_keywords
    is_multichild = "다자녀 가구" in selected_keywords

    # 3. 특수 조건 변수 결합
    is_stay_eligible = (19 <= age <= 49 and is_founder) or (19 <= age <= 39 and is_worker)
    is_farmer_18_45 = 18 <= age <= 45 and is_farmer
    
    # 4. 소득 조건 변수 (초과자 원천 차단 방식)
    is_over_limit = income_level == "해당 없음 (소득 기준 초과)"

    if is_over_limit:
        is_under_60 = is_under_100 = is_under_120 = is_under_140 = is_under_150 = is_under_180 = False
    else:
        is_under_60 = income_level == "60% 이하 (저소득층 및 집중 주거지원 대상)"
        is_under_100 = is_under_60 or income_level == "100% 이하"
        is_under_120 = is_under_100
        is_under_140 = is_under_100 or income_level == "140% 이하"
        is_under_150 = is_under_140 or income_level == "150% 이하"
        is_under_180 = is_under_150 or income_level == "180% 이하"

    # =========================================================
    # 💰 1. 청년 자산 형성 지원 상품
    # =========================================================
    st.subheader("💰 1. 청년 자산 형성 지원 상품")
    asset_match_count = 0 
    
    if is_youth_19_34 and not is_over_limit:
        asset_match_count += 1
        with st.expander("📌 청년미래적금 (중앙정부 - 2026년 신설)"):
            st.markdown("""
            * **지원 내용**: 월 최대 50만 원씩 3년간 저축 시, 정부 기여금과 비과세 혜택을 합쳐 최대 2,200만 원(우대형 기준)의 목돈을 마련할 수 있습니다.
            * **안내**: 만 19~34세 청년 중 개인 소득 6,000만 원 이하, 가구 소득 중위 200% 이하가 대상입니다. 입사 6개월 이내 중소기업 신규 취업자는 '우대형'으로 분류되어 더 높은 기여금을 받습니다.
            """)

    if is_youth_19_34 and is_under_180:
        asset_match_count += 1
        with st.expander("📌 청년도약계좌 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 5년(60개월) 동안 매월 최대 70만 원을 납입하면 정부 기여금과 이자 비과세 혜택을 통해 최대 5,000만 원 수준의 자산을 형성합니다.
            * **안내**: 만 19~34세 청년 중 개인 소득 7,500만 원 이하, 가구 소득 중위 250% 이하 조건을 충족해야 합니다. 2년 이상 유지 시 납입 원금의 40% 이내에서 부분 인출이 가능합니다.
            """)

    if is_youth_18_39 and (is_under_60 or is_under_100 or is_under_140) and not is_unemployed:
        asset_match_count += 1
        with st.expander("📌 전북청년 함께 두배적금 (전북특별자치도/군산시)"):
            st.markdown("""
            * **지원 내용**: 월 10만 원을 저축하면 지자체에서 동일 금액(10만 원)을 1:1로 매칭 지원하여 2년 후 두 배의 자산을 형성합니다.
            * **안내**: 도내 거주 및 근로(창업) 중인 청년을 대상으로 합니다.
            """)

    if is_transition_35_39:
        asset_match_count += 1 
        with st.expander("📌 안정·전환기(35~39세) 청년 특화 혜택"):
            st.markdown("""
            * **다자녀 패밀리카 지원**: 다자녀 가정을 위한 차량 관련 지원 (해당 시)
            * **사회적경제 청년혁신가 육성 & 청년기업 인증**: 새로운 도전을 앞둔 30대 후반 창업/혁신가 집중 지원
            """)

    if asset_match_count == 0:
        st.info("ℹ️ 현재 입력하신 조건(나이, 소득 등)에 맞는 자산 형성 지원 상품이 없습니다.")

    # =========================================================
    # 🏠 2. 청년 주거 안정 지원 사업
    # =========================================================
    st.subheader("🏠 2. 청년 주거 안정 지원 사업")
    housing_match_count = 0
    
    if has_house == "무주택":
        if is_youth_19_34 and is_under_60:
            housing_match_count += 1
            with st.expander("📌 청년월세 한시 특별지원 (중앙정부)"):
                st.markdown("""
                * **지원 내용**: 실제 납부하는 임대료를 월 최대 20만 원씩 최장 24개월(총 480만 원) 동안 지원합니다.
                * **안내**: 무주택 청년 중 청년가구 중위소득 60% 이하 및 원가구 중위소득 100% 이하인 경우 신청 가능합니다.
                """)
            
        if is_youth_19_39 and not is_over_limit:
            housing_match_count += 1
            with st.expander("📌 전세보증금 반환보증 보증료 지원 (중앙정부)"):
                st.markdown("""
                * **지원 내용**: 전세 사기 예방을 위해 이미 납부한 전세보증금 반환보증(HUG, HF, SGI) 보증료를 최대 40만 원까지 환급해 줍니다.
                * **안내**: 무주택 임차인 중 청년(만 19~39세)은 연 소득 5,000만 원 이하, 신혼부부는 7,500만 원 이하, 보증금 3억 원 이하 주택이어야 합니다.
                """)

        if is_stay_eligible:
            housing_match_count += 1
            with st.expander("📌 군산 STAY 주거지원사업 (만 19~49세 창업자 포함)"):
                st.markdown("""
                * **지원 내용**: 최대 2년(24개월) 동안 임대주택 보증금 최대 350만 원, 월 임차료 최대 10만 원을 지원합니다.
                * **안내**: 군산시 관내 LH 소유 임대 원룸 및 아파트 등에 입주할 수 있습니다.
                """)

        if is_youth_18_39 and not is_over_limit:
            housing_match_count += 1
            with st.expander("📌 신혼부부 및 청년 전세자금 대출이자 지원"):
                st.markdown("""
                * **지원 내용**: 전세 임차보증금 대출 잔액의 최대 2% (연 최대 200만 원 한도) 내에서 이자를 지원합니다.
                * **안내**: 가구당 중위소득 180% 이하 및 전세보증금 3억 원 이하 조건을 만족해야 합니다.
                """)

        if housing_match_count == 0:
            st.info("ℹ️ 무주택자이시지만, 현재 조건에 맞는 주거 정책이 없습니다.")
    else:
        st.warning("💡 주택을 보유 중이라 무주택자 대상 주거 지원 혜택에서 제외되었습니다.")

    # =========================================================
    # 🏃‍♂️ 3. 청년 구직 및 창업·정착 지원
    # =========================================================
    st.subheader("🏃‍♂️ 3. 청년 구직 및 창업·정착 지원")
    job_match_count = 0
    
    if is_unemployed and is_youth_18_34 and is_under_120:
        job_match_count += 1
        with st.expander("📌 국민취업지원제도 1유형 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 저소득층 구직자에게 구직활동지원금(구직촉진수당)을 기존 월 50만 원에서 월 60만 원으로 인상하여 6개월간 지급합니다.
            * **안내**: 만 15~34세 청년은 가구 소득 중위 120% 이하, 재산 5억 원 이하인 경우 신청할 수 있습니다.
            """)

    if is_worker and is_youth_18_34:
        job_match_count += 1
        with st.expander("📌 청년일자리도약장려금 - 비수도권 근속 인센티브 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 군산 등 비수도권 기업에 취업하여 6개월 이상 근속한 청년에게 2년간 최대 720만 원의 인센티브를 지급합니다.
            * **안내**: 만 15~34세 취업 애로 청년이 대상이며, 기업 역시 청년 채용 시 1년간 최대 720만 원의 장려금을 지원받습니다.
            """)

    if is_unemployed and is_youth_18_39 and is_under_150:
        job_match_count += 1
        with st.expander("📌 전북형 청년활력수당 (전북특별자치도/군산시)"):
            st.markdown("""
            * **지원 내용**: 미취업 청년의 구직 활동을 위해 월 50만 원씩 6개월간 총 300만 원을 지원합니다.
            * **안내**: 군산시에 거주하는 만 18~39세 미취업 청년 중 중위소득 150% 이하가 대상입니다.
            """)

    if is_youth_18_39 and is_under_150 and (is_worker or is_farmer):
        job_match_count += 1
        with st.expander("📌 지역정착 지원사업 (전북특별자치도/군산시)"):
            st.markdown("""
            * **지원 내용**: 농·어업, 중소기업 등 특정 분야 종사 청년에게 월 30만 원씩 12개월간 정착 수당을 지급합니다.
            * **안내**: 군산 거주 만 18~39세 청년 중 해당 분야 3개월 이상 종사자, 중위소득 150% 이하 조건이 필요합니다.
            """)

    if is_founder or is_unemployed:
        job_match_count += 1
        with st.expander("📌 모두의 창업 프로젝트 (중앙정부 - 2026년 신설)"):
            st.markdown("""
            * **지원 내용**: 아이디어만 있다면 연령·학력 제한 없이 최대 10억 원의 사업화 자금과 AI 솔루션을 지원받는 대국민 창업 오디션입니다.
            * **안내**: 전체 선발 인원 5,000명 중 70% 이상을 비수도권에서 선발하며, 실패 경험이 있는 재창업자도 참여 가능합니다.
            """)

    if 18 <= age <= 34:
        job_match_count += 1
        with st.expander("📌 청년도전지원사업 (군산시 청년뜰)"):
            st.markdown("""
            * **지원 내용**: 구직 단념 청년들을 위한 맞춤형 프로그램을 제공하고, 참여 시 최대 350만 원의 참여 수당을 지급합니다.
            """)

    if is_farmer_18_45:
        job_match_count += 1
        with st.expander("📌 청년농업인 육성 및 영농정착지원사업 (만 18~45세)"):
            st.markdown("""
            * **지원 내용**: 청년창업농 영농 정착 자금 지원
            """)

    if 40 <= age <= 69 and is_unemployed:
        job_match_count += 1
        with st.expander("📌 신중년 취업 지원 정책 (만 40~69세)"):
            st.markdown("""
            * **지원 내용**: 중년층 재취업 시 장기 근속에 따라 개인에게 최대 200만 원 취업 장려금 지급
            """)

    if job_match_count == 0:
        st.info("ℹ️ 현재 직업 상태나 소득 수준에 맞는 구직/정착 지원 정책이 없습니다.")

    # =========================================================
    # 🧠 4. 생활·복지 및 문화 예술 지원
    # =========================================================
    st.subheader("🧠 4. 생활·복지 및 문화 예술 지원")
    life_match_count = 0
    
    if 20 <= age <= 34:
        life_match_count += 1
        with st.expander("📌 2026년 국가건강검진 - 청년 정신건강 확대 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 만 20~34세 청년의 정신건강 검진 주기가 기존 10년에서 2년으로 단축되며, 조현병 및 조울증 검사가 추가됩니다.
            * **안내**: 해당 연도 건강검진 대상 청년이라면 무료로 검진받을 수 있습니다.
            """)

    if is_youth_18_39:
        life_match_count += 1
        with st.expander("📌 전국민 마음투자 지원사업 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 우울·불안 등 정서적 어려움이 있는 청년에게 전문 심리상담 서비스를 총 8회 이용할 수 있는 바우처를 제공합니다.
            * **안내**: 보건소나 복지로를 통해 신청 가능하며, 소득에 따라 본인 부담금이 차등 발생할 수 있습니다.
            """)

    if is_youth_19_34:
        life_match_count += 1
        with st.expander("📌 청년 마음건강지원사업"):
            st.markdown("""
            * **지원 내용**: 정서적 어려움이 있는 청년에게 전문 심리상담 바우처를 제공합니다.
            * **안내**: 소득 및 재산 기준은 없으며, 본인 부담금은 소득 수준에 따라 일부 차등 발생할 수 있습니다.
            """)

    if is_youth_18_39:
        life_match_count += 1
        with st.expander("📌 대중교통 K-패스 무제한 정액권 (중앙정부 - 2026년 확대)"):
            st.markdown("""
            * **지원 내용**: 월 5만 5천 원으로 전국의 모든 대중교통(지하철, 버스, GTX 포함)을 월 20만 원 한도 내에서 무제한 이용할 수 있습니다.
            * **안내**: 일반 성인은 6만 2천 원이며, 청년·고령층·저소득층은 5만 5천 원 정액권 선택이 가능합니다.
            """)

    if 19 <= age <= 20:
        life_match_count += 1
        with st.expander("📌 청년문화예술패스 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 순수 예술 분야 관람을 위해 1인당 연간 최대 20만 원(비수도권 기준)의 문화 포인트를 지급합니다.
            * **안내**: 만 19~20세 청년이 대상이며, 2026년에는 사용 분야에 '영화'가 추가되었습니다.
            """)

    if is_worker:
        life_match_count += 1
        with st.expander("📌 직장인 든든한 한끼 (중앙정부 - 2026년 신설)"):
            st.markdown("""
            * **지원 내용**: 산업단지 중소기업 근로자에게 '천원의 아침밥'을 제공하고, 점심 식비의 20%(월 최대 4만 원)를 지원합니다.
            """)

    if is_youth_18_39:
        life_match_count += 1
        with st.expander("📌 K-ART 청년 창작자 지원 (중앙정부 - 2026년 신설)"):
            st.markdown("""
            * **지원 내용**: 순수 예술 분야에서 활동하는 만 39세 이하 청년 예술가에게 연 900만 원의 창작 지원금을 지급합니다.
            """)

    if life_match_count == 0:
        st.info("ℹ️ 현재 연령 조건에서는 지원 가능한 생활·문화 사업이 없습니다.")

    # =========================================================
    # 📱 5. 정책 정보 접근 및 참여
    # =========================================================
    st.subheader("📱 5. 정책 정보 접근 및 참여")

    with st.expander("📌 통합 플랫폼 '온통청년'"):
        st.markdown("""
        * **지원 내용**: 3,000여 개의 중앙·지자체 정책을 AI 챗봇 상담과 공공마이데이터 기반 자가진단으로 맞춤형 검색할 수 있습니다.
        * **안내**: 별도 회원가입 없이 간편 인증으로 이용 가능하며, 청년신문고를 통해 직접 정책 개선안을 제안할 수도 있습니다.
        """)


