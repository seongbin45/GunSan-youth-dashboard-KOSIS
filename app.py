import streamlit as st
import pandas as pd
import sqlite3  # 👈 이 녀석이 빠져 있어서 에러가 났던 겁니다!
import plotly.express as px

st.set_page_config(page_title="군산시 청년 맞춤 혜택 찾기", layout="wide")

st.title("""📢 군산시 청년 맞춤 혜택 찾기(어울리는 제목을 추천해주세요ㅠ)""")
st.markdown("""**직접 KOSIS에서 수집한 데이터로 만든 서비스입니다.**  
사회초년생을 위한 금융 서비스의 기초가 됩니다""")
st.write("---")

# 📌 청소년과 대학생을 위해 친절하게 수정한 안내판!
with st.expander("✅ **[청소년과 대학생을 위한 위한 용어 사전]**"):
    st.markdown("""
✅ **[청소년과 대학생을 위한 위한 용어 사전]**
* **기준 중위소득 (나의 소득 등수)**  
  👉 우리나라 사람들을 소득 순으로 1등부터 100등까지 줄을 세웠을 때, 딱 중간인 **50등 사람의 소득**이에요. '중위소득 60%'는 그 중간 사람보다 소득이 적은 친구들을 정부가 먼저 집중해서 도와주겠다는 뜻입니다!
* **바우처 (지정 이용권)**  
  👉 현금 대신 주는 것으로, 정해진 곳 에서만 현금처럼 쓸 수 있는 특별한 쿠폰이에요. (예: 심리상담 바우처 등)
* **비과세 (세금 안 뗌!)**  
  👉 원래 은행 이자를 받으면 세금을 내야 하지만, 이건 **세금을 한 푼도 떼지 않고 이자를 통째로 다 주는** 엄청난 혜택이에요.
* **매칭 지원 (1+1 저축)**  
  👉 내가 10만 원을 저축하면, 나라 or 군산시가 똑같이 **10만 원을 공짜로 더 얹어주는** 꿀이득 시스템이에요!
""")

with st.expander("🙀 **[용어 쉽게 설명해 드릴게요!]**"):
    st.markdown("""
    정보 취약 계층이나 사회 초년생과 청소년들도 2026년 청년 정책을 한눈에 이해할 수 있도록 어려운 용어는 쉽게 풀고, 핵심 내용은 빠짐없이 정리해 드릴게요.

### 🏢 1. 우리 가족과 소득 관련 용어 정복
*   **청년가구**: 부모님과 떨어져 혼자 살거나 친구와 같이 사는 등, 청년이 중심이 되어 꾸준히 살아가는 집을 말해요.  
*   **원가구**: 청년이 독립하기 전까지 부모님과 함께 살았던 원래의 가족을 뜻해요.  
*   **저소득층**: 소득이 적어 나라의 도움이 더 많이 필요한 분들이에요.  
*   **중위소득 %**: 정부가 정한 지원 기준선이에요. 예를 들어 중위소득 100%는 대한민국 가구를 소득 순으로 세웠을 때 딱 중간에 있는 집의 소득을 말해요.

### 🏠 2. 집 빌릴 때 쓰는 '어려운 말' 정복
*   **전세보증금 (임차보증금)**: 집을 빌릴 때 "나중에 나갈 때 돌려받을게요!" 하고 주인에게 잠시 맡겨두는 아주 큰 거스름돈이에요.
*   **반환보증**: "나중에 보증금을 안전하게 돌려받을 수 있게 나라나 보험사가 약속해 줄게!" 하는 전세금 안전장치예요.
*   **보증료**: 이 안전장치(보험)를 이용하기 위해 내는 일종의 수수료나 서비스 이용료예요.

### 💰 3. 돈이 복사되는 금융 마법 (자산 형성)
*   **바우처**: 현금 대신 정해진 곳에서만 쓸 수 있는 '전용 쿠폰'이에요. 상담소나 공연장 등에서 쓸 수 있죠.
*   **매칭 지원**: 내가 10만 원을 저축하면 나라가 10만 원을 더 얹어주는 '1+1 저축' 방식이에요.
*   **비과세**: 원래 이자를 받으면 세금을 내야 하지만, 세금을 0원으로 만들어 이자를 전부 내 주머니에 넣게 해주는 혜택이에요.

### 🏃 4. 일자리와 취업 지원 '쉬운 풀이'
*   **중소기업**: 규모가 아주 크지는 않지만 내실 있고 탄탄한 회사들을 말해요.
*   **농·어업**: 땅에서 농사짓는 일(농업)과 바다에서 물고기 잡는 일(어업)을 합쳐서 부르는 말이에요.

### 🧠 5. 마음과 생활을 돌보는 '따뜻한 지원'
*   **고령층**: 나이가 많으신 할아버지, 할머니들을 뜻해요.
*   **중앙·지자체**: 나라(중앙정부)와 내가 살고 있는 군산시(지방자치단체)를 함께 부르는 말이에요.

### 📱 6. 정책 정보와 신청하는 방법
*   **복지로**: 나라의 모든 복지 정보를 한눈에 보고 신청하는 '인터넷 복지 백화점'이에요.
*   **온통청년**: 청년들에게 필요한 정보만 쏙쏙 모아둔 '청년 전용 포털 사이트'예요.
*   **공공마이데이터**: 복잡한 서류를 직접 떼지 않아도 나라가 알아서 정보를 확인해 주는 '데이터 심부름' 서비스예요.
*   **간편 인증**: 어려운 비밀번호 대신 카카오톡이나 네이버로 쉽고 빠르게 나를 확인하는 방법이에요.
*   **청년신문고**: "우리에게 이런 정책이 더 필요해요!"라고 청년들이 직접 의견을 올리는 온라인 게시판이에요.
    """)

with st.expander("""📢꼭 아래 내용을 먼저 확인해주세요!  
(부탁드릴게요🙇)"""):
    st.markdown("""
    ### 🏢 1. 내 소득은 어느 정도일까?
    * **개인소득:** 나 혼자 알바나 직장에서 번 돈이에요. 내 월급봉투를 확인해보거나 국세청 홈택스에서 소득 관련 정보를 확인할 수 있어요.
    * **가구소득:**	우리 가족 모두가 번 돈을 합친 것이에요. 여기에는 근로소득, 사업소득, 재산소득, 이전소득 등이 포함돼요.	​부모님께 우리 가족의 소득이 얼마인지 물어보거나, 건강보험료 납부 내역을 통해 파악할 수 있어요.
    * **중위소득 %:**	정부가 정한 지원 기준선이에요. ​예를 들어, 중위소득 100%는 대한민국 가구의 딱 중간 소득을 의미하며, 60% 이하는 중간보다 소득이 적은 가구를 뜻해요.	​우리 집 건강보험료가 얼마인지 부모님께 여쭤보면 돼요. ​직장가입자의 경우 급여명세서에서 건강보험료 본인부담금을 확인하여 중위소득 기준을 알 수 있어요.
    
    ### 🏠 2. 집 빌릴 때 쓰는 '어려운 말' 정복
    * **👤 임차인:** 집을 빌려 쓰는 손님(여러분)을 말해요. 반대로 집 주인은 '임대인'이라고 불러요.
    * **💰 임차보증금:** "집 깨끗이 쓰고 나갈 때 돌려받을게요!" 하고 잠시 맡겨두는 거대한 거스름돈이에요. ​전세금이나 월세 보증금을 말해요.
    * **💸 월세 (임차료):** 매달 집 주인에게 내는 집 이용료(구독료)예요. 이 돈은 돌려받지 못해요.
    * **🏦 전세대출:** 보증금이 너무 비싸서 은행에서 빌리는 큰돈이에요.
    * **📉 이자 지원:** 은행에서 돈을 빌리면 빌린 값(이자)을 내야 하는데, 군산시가 그 '빌린 값'을 대신 내주는 거예요!
    * **🏢 임대주택 보증금:** 나라(LH 등)가 운영하는 저렴한 빌린 집에 들어갈 때 맡기는 돈이에요. 일반 집보다 훨씬 싸요!
    * **⚠️ 월세 조건:** "보증금 5천만 원 이하, 월세 70만 원 이하인 집만 도와줄게!"와 같이 정부가 정한 규칙이에요. ​
    
    ### 💰 3. 돈이 복사되는 금융 마법
    * **🎁 바우처:**   
    현금 대신 주는 '특정 가게 전용 쿠폰'이에요. 예를 들어, 상담소에서만 쓸 수 있는 쿠폰 같은 것이죠.
    * **🤝 매칭 지원:**   
    내가 10만 원 저축하면 나라가 10만 원을 더 주는 '1+1 저축'이에요. ​전북청년 함께 두배적금이 대표적인 예시예요.
    * **🛡️ 비과세:**   
    원래 이자를 받으면 세금을 내야 하는데, 세금을 0원으로 만들어 이자를 전부 받을 수 있게 해주는 혜택이에요. ​청년도약계좌의 주요 혜택 중 하나입니다.
    * **📈 이자:**  
    **저축할 때:** 은행이 나에게 주는 보너스 선물이에요.  
    **빌릴 때:** 내가 은행에 내는 돈 빌린 값(수수료)을 말해요.
    """)

st.write("---")

import streamlit as st

# UI 가독성을 위해 접이식 메뉴(Expander)로 감싸기
with st.expander("📋 나의 맞춤 조건 설정하기 (클릭하여 열기/닫기)", expanded=True):
    
    # 첫 번째 줄: 기본 인적 사항
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

    st.write("") # 약간의 간격

    # 두 번째 줄: 키워드 다중 선택 (가독성의 핵심!)
    st.markdown("**💡 나에게 해당하는 키워드를 모두 선택하세요 (복수 선택 가능)**")
    
    # 사용자가 직관적으로 고를 수 있는 키워드 리스트
    keyword_options = [
        "미취업 (구직 중)", 
        "취업자 (군산 소재 기업)", 
        "창업자 (7년 미만)", 
        "농업 종사 (청년창업농 등)",
        "신혼부부",
        "다자녀 가구"
    ]
    
    selected_keywords = st.multiselect(
        "해당하는 조건을 클릭하거나 검색하여 추가하세요.",
        options=keyword_options,
        default=["미취업 (구직 중)"] # 기본값 설정
    )

st.write("---")

# 1. 테두리 스타일을 위한 CSS 주입
st.markdown("""
    <style>
    /* 모든 버튼을 테두리 스타일로 변경 */
    div.stButton > button {
        background-color: transparent !important; /* 배경 투명하게 */
        color: #FF4B4B !important; /* 글자 색상 (Streamlit 기본 레드 또는 원하는 색상) */
        border: 2px solid #FF4B4B !important; /* 테두리 두께와 색상 */
        border-radius: 8px !important; /* 테두리 둥글게 */
        transition: all 0.3s ease; /* 마우스 올렸을 때 부드러운 효과 */
    }
    
    /* 마우스를 올렸을 때(Hover) 효과 */
    div.stButton > button:hover {
        background-color: #FF4B4B !important; /* 배경이 꽉 참 */
        color: white !important; /* 글자가 흰색으로 */
    }
    </style>
""", unsafe_allow_html=True)

# 2. 추천 알고리즘 가동 버튼 (여기서 type="primary"는 지워주시는 게 좋습니다)
if st.button("내 맞춤 혜택 결과 보기 🚀"):
    st.success("🎉 입력하신 조건에 부합하는 군산시 청년 정책 매칭 결과입니다.")
    
    # ---------------------------------------------------------
    # 🔍 개선된 키워드 기반 매칭 변수 생성
    # ---------------------------------------------------------
    # 나이 조건 변수
    is_youth_18_34 = 18 <= age <= 34
    is_youth_19_34 = 19 <= age <= 34
    is_youth_18_39 = 18 <= age <= 39
    is_youth_19_39 = 19 <= age <= 39
    is_transition_35_39 = 35 <= age <= 39
    is_mid_40_69 = 40 <= age <= 69

    # 키워드 체크용 변수 (오류 방지)
    is_unemployed = "미취업 (구직 중)" in selected_keywords
    is_worker = "취업자 (군산 소재 기업)" in selected_keywords
    is_founder = "창업자 (7년 미만)" in selected_keywords
    is_farmer = "농업 종사 (청년창업농 등)" in selected_keywords
    is_newlywed = "신혼부부" in selected_keywords
    is_multichild = "다자녀 가구" in selected_keywords

    # 특수 조건 변수 결합
    is_stay_eligible = (is_founder and 19 <= age <= 49) or (is_worker and 19 <= age <= 39)
    is_farmer_18_45 = 18 <= age <= 45 and is_farmer
    
    # ---------------------------------------------------------
    # 🔍 [수정] 소득 조건을 완벽히 거르는 매칭 변수 생성
    # ---------------------------------------------------------
    # 1. 소득 초과자 먼저 정의 (최우선 차단)
    is_over_limit = income_level == "해당 없음 (소득 기준 초과)"

    # 2. 소득 초과자가 아닐 때만 하위 소득 조건을 연쇄적으로 True 처리
    if is_over_limit:
        is_under_60 = is_under_100 = is_under_120 = is_under_140 = is_under_150 = is_under_180 = False
    else:
        # 가장 안전하고 직관적인 직접 맵핑 방식 (중복 연산 제거)
        is_under_60 = income_level == "60% 이하 (저소득층 및 집중 주거지원 대상)"
        is_under_100 = is_under_60 or income_level == "100% 이하"
        is_under_120 = is_under_100  # 100% 이하면 당연히 120% 이하도 충족함
        is_under_140 = is_under_100 or income_level == "140% 이하"
        is_under_150 = is_under_140 or income_level == "150% 이하"
        is_under_180 = is_under_150 or income_level == "180% 이하"
    
    # ---------------------------------------------------------
    # 💰 1. 청년 자산 형성 지원 상품
    # ---------------------------------------------------------
    st.subheader("💰 1. 청년 자산 형성 지원 상품")
    asset_match_count = 0 
    
    # 35~39세 변수 안전하게 직접 나이 조건 부여
    is_transition_35_39 = 35 <= age <= 39
    
    # 청년미래적금 (중앙정부 - 2026년 신설)
    if is_youth_19_34 and not is_over_limit:
        asset_match_count += 1
        # st.expander를 사용해 클릭해야 열리도록 변경
        with st.expander("📌 청년미래적금 (중앙정부 - 2026년 신설)"):
            st.markdown("""
            * **지원 내용**: 월 최대 50만 원씩 3년간 저축 시, 정부 기여금과 비과세 혜택을 합쳐 최대 2,200만 원(우대형 기준)의 목돈을 마련할 수 있습니다.
            * **안내**: 만 19~34세 청년 중 개인 소득 6,000만 원 이하, 가구 소득 중위 200% 이하가 대상입니다. 입사 6개월 이내 중소기업 신규 취업자는 '우대형'으로 분류되어 더 높은 기여금을 받습니다.
            """)

    # 청년도약계좌 (중앙정부)
    if is_youth_19_34 and is_under_180:
        asset_match_count += 1
        with st.expander("📌 청년도약계좌 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 5년(60개월) 동안 매월 최대 70만 원을 납입하면 정부 기여금과 이자 비과세 혜택을 통해 최대 5,000만 원 수준의 자산을 형성합니다.
            * **안내**: 만 19~34세 청년 중 개인 소득 7,500만 원 이하, 가구 소득 중위 250% 이하 조건을 충족해야 합니다. 2년 이상 유지 시 납입 원금의 40% 이내에서 부분 인출이 가능합니다.
            """)

    # 전북청년 함께 두배적금
    if is_youth_18_39 and (is_under_60 or is_under_100 or is_under_140) and not is_unemployed:
        asset_match_count += 1
        with st.expander("📌 전북청년 함께 두배적금 (전북특별자치도/군산시)"):
            st.markdown("""
            * **지원 내용**: 월 10만 원을 저축하면 지자체에서 동일 금액(10만 원)을 1:1로 매칭 지원하여 2년 후 두 배의 자산을 형성합니다.
            * **안내**: 도내 거주 및 근로(창업) 중인 청년을 대상으로 합니다.
            """)

    # 안정·전환기(35~39세) 청년 특화 혜택
    if is_transition_35_39:
        asset_match_count += 1 
        with st.expander("📌 안정·전환기(35~39세) 청년 특화 혜택"):
            st.markdown("""
            * **다자녀 패밀리카 지원**: 다자녀 가정을 위한 차량 관련 지원 (해당 시)
            * **사회적경제 청년혁신가 육성 & 청년기업 인증**: 새로운 도전을 앞둔 30대 후반 창업/혁신가 집중 지원
            """)

    if asset_match_count == 0:
        st.info("ℹ️ 현재 입력하신 조건(나이, 소득 등)에 맞는 자산 형성 지원 상품이 없습니다.")
    
    # ---------------------------------------------------------
    # 🏠 2. 청년 주거 안정 지원 사업
    # ---------------------------------------------------------
    st.subheader("🏠 2. 청년 주거 안정 지원 사업")
    housing_match_count = 0
    
    # UI 개선안에 맞춘 "무주택" 조건으로 수정
    if has_house == "무주택":
        # 청년월세 한시 특별지원
        if is_youth_19_34 and is_under_60:
            housing_match_count += 1
            # st.expander를 사용해 클릭해야 열리도록 변경
            with st.expander("📌 청년월세 한시 특별지원 (중앙정부)"):
                st.markdown("""
                * **지원 내용**: 실제 납부하는 임대료를 월 최대 20만 원씩 최장 24개월(총 480만 원) 동안 지원합니다.
                * **안내**: 무주택 청년 중 청년가구 중위소득 60% 이하 및 원가구 중위소득 100% 이하인 경우 신청 가능합니다.
                """)
            
        # 전세보증금 반환보증 보증료 지원
        if is_youth_19_39 and not is_over_limit:
            housing_match_count += 1
            with st.expander("📌 전세보증금 반환보증 보증료 지원 (중앙정부)"):
                st.markdown("""
                * **지원 내용**: 전세 사기 예방을 위해 이미 납부한 전세보증금 반환보증(HUG, HF, SGI) 보증료를 최대 40만 원까지 환급해 줍니다.
                * **안내**: 무주택 임차인 중 청년(만 19~39세)은 연 소득 5,000만 원 이하, 신혼부부는 7,500만 원 이하, 보증금 3억 원 이하 주택이어야 합니다.
                """)

        # 군산 STAY 주거지원사업
        if is_stay_eligible:
            housing_match_count += 1
            with st.expander("📌 군산 STAY 주거지원사업 (만 19~49세 창업자 포함)"):
                st.markdown("""
                * **지원 내용**: 최대 2년(24개월) 동안 임대주택 보증금 최대 350만 원, 월 임차료 최대 10만 원을 지원합니다.
                * **안내**: 군산시 관내 LH 소유 임대 원룸 및 아파트 등에 입주할 수 있습니다.
                """)

        # 신혼부부 및 청년 전세자금 대출이자 지원
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
    
    # ---------------------------------------------------------
    # 🏃‍♂️ 3. 청년 구직 및 창업·정착 지원
    # ---------------------------------------------------------
    st.subheader("🏃‍♂️ 3. 청년 구직 및 창업·정착 지원")
    job_match_count = 0
    
    # 국민취업지원제도 1유형
    if is_unemployed and is_youth_18_34 and is_under_120:
        job_match_count += 1
        with st.expander("📌 국민취업지원제도 1유형 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 저소득층 구직자에게 구직활동지원금(구직촉진수당)을 기존 월 50만 원에서 월 60만 원으로 인상하여 6개월간 지급합니다.
            * **안내**: 만 15~34세 청년은 가구 소득 중위 120% 이하, 재산 5억 원 이하인 경우 신청할 수 있습니다.
            """)

    # 청년일자리도약장려금
    if is_worker and is_youth_18_34:
        job_match_count += 1
        with st.expander("📌 청년일자리도약장려금 - 비수도권 근속 인센티브 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 군산 등 비수도권 기업에 취업하여 6개월 이상 근속한 청년에게 2년간 최대 720만 원의 인센티브를 지급합니다.
            * **안내**: 만 15~34세 취업 애로 청년이 대상이며, 기업 역시 청년 채용 시 1년간 최대 720만 원의 장려금을 지원받습니다.
            """)

    # 전북형 청년활력수당
    if is_unemployed and is_youth_18_39 and is_under_150:
        job_match_count += 1
        with st.expander("📌 전북형 청년활력수당 (전북특별자치도/군산시)"):
            st.markdown("""
            * **지원 내용**: 미취업 청년의 구직 활동을 위해 월 50만 원씩 6개월간 총 300만 원을 지원합니다.
            * **안내**: 군산시에 거주하는 만 18~39세 미취업 청년 중 중위소득 150% 이하가 대상입니다.
            """)

    # 지역정착 지원사업
    if is_youth_18_39 and is_under_150 and (is_worker or is_farmer):
        job_match_count += 1
        with st.expander("📌 지역정착 지원사업 (전북특별자치도/군산시)"):
            st.markdown("""
            * **지원 내용**: 농·어업, 중소기업 등 특정 분야 종사 청년에게 월 30만 원씩 12개월간 정착 수당을 지급합니다.
            * **안내**: 군산 거주 만 18~39세 청년 중 해당 분야 3개월 이상 종사자, 중위소득 150% 이하 조건이 필요합니다.
            """)

    # 모두의 창업 프로젝트
    if is_founder or is_unemployed:
        job_match_count += 1
        with st.expander("📌 모두의 창업 프로젝트 (중앙정부 - 2026년 신설)"):
            st.markdown("""
            * **지원 내용**: 아이디어만 있다면 연령·학력 제한 없이 최대 10억 원의 사업화 자금과 AI 솔루션을 지원받는 대국민 창업 오디션입니다.
            * **안내**: 전체 선발 인원 5,000명 중 70% 이상을 비수도권에서 선발하며, 실패 경험이 있는 재창업자도 참여 가능합니다.
            """)

    # 청년도전지원사업
    if 18 <= age <= 34:
        job_match_count += 1
        with st.expander("📌 청년도전지원사업 (군산시 청년뜰)"):
            st.markdown("""
            * **지원 내용**: 구직 단념 청년들을 위한 맞춤형 프로그램을 제공하고, 참여 시 최대 350만 원의 참여 수당을 지급합니다.
            """)

    # 청년농업인 육성 및 영농정착지원사업
    if is_farmer_18_45:
        job_match_count += 1
        with st.expander("📌 청년농업인 육성 및 영농정착지원사업 (만 18~45세)"):
            st.markdown("""
            * **지원 내용**: 청년창업농 영농 정착 자금 지원
            """)

    # 신중년 취업 지원 정책
    if 40 <= age <= 69 and is_unemployed:
        job_match_count += 1
        with st.expander("📌 신중년 취업 지원 정책 (만 40~69세)"):
            st.markdown("""
            * **지원 내용**: 중년층 재취업 시 장기 근속에 따라 개인에게 최대 200만 원 취업 장려금 지급
            """)

    if job_match_count == 0:
        st.info("ℹ️ 현재 직업 상태나 소득 수준에 맞는 구직/정착 지원 정책이 없습니다.")
    
    # ---------------------------------------------------------
    # 🧠 4. 생활·복지 및 문화 예술 지원
    # ---------------------------------------------------------
    st.subheader("🧠 4. 생활·복지 및 문화 예술 지원")
    life_match_count = 0
    
    # 2026년 국가건강검진
    if 20 <= age <= 34:
        life_match_count += 1
        with st.expander("📌 2026년 국가건강검진 - 청년 정신건강 확대 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 만 20~34세 청년의 정신건강 검진 주기가 기존 10년에서 2년으로 단축되며, 조현병 및 조울증 검사가 추가됩니다.
            * **안내**: 해당 연도 건강검진 대상 청년이라면 무료로 검진받을 수 있습니다.
            """)

    # 전국민 마음투자 지원사업
    if is_youth_18_39:
        life_match_count += 1
        with st.expander("📌 전국민 마음투자 지원사업 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 우울·불안 등 정서적 어려움이 있는 청년에게 전문 심리상담 서비스를 총 8회 이용할 수 있는 바우처를 제공합니다.
            * **안내**: 보건소나 복지로를 통해 신청 가능하며, 소득에 따라 본인 부담금이 차등 발생할 수 있습니다.
            """)

    # 청년 마음건강지원사업
    if is_youth_19_34:
        life_match_count += 1
        with st.expander("📌 청년 마음건강지원사업"):
            st.markdown("""
            * **지원 내용**: 정서적 어려움이 있는 청년에게 전문 심리상담 바우처를 제공합니다.
            * **안내**: 소득 및 재산 기준은 없으며, 본인 부담금은 소득 수준에 따라 일부 차등 발생할 수 있습니다.
            """)

    # 대중교통 K-패스 무제한 정액권
    if is_youth_18_39:
        life_match_count += 1
        with st.expander("📌 대중교통 K-패스 무제한 정액권 (중앙정부 - 2026년 확대)"):
            st.markdown("""
            * **지원 내용**: 월 5만 5천 원으로 전국의 모든 대중교통(지하철, 버스, GTX 포함)을 월 20만 원 한도 내에서 무제한 이용할 수 있습니다.
            * **안내**: 일반 성인은 6만 2천 원이며, 청년·고령층·저소득층은 5만 5천 원 정액권 선택이 가능합니다.
            """)

    # 청년문화예술패스
    if 19 <= age <= 20:
        life_match_count += 1
        with st.expander("📌 청년문화예술패스 (중앙정부)"):
            st.markdown("""
            * **지원 내용**: 순수 예술 분야 관람을 위해 1인당 연간 최대 20만 원(비수도권 기준)의 문화 포인트를 지급합니다.
            * **안내**: 만 19~20세 청년이 대상이며, 2026년에는 사용 분야에 '영화'가 추가되었습니다.
            """)

    # 직장인 든든한 한끼 (job_status 대신 is_worker 변수로 수정)
    if is_worker:
        life_match_count += 1
        with st.expander("📌 직장인 든든한 한끼 (중앙정부 - 2026년 신설)"):
            st.markdown("""
            * **지원 내용**: 산업단지 중소기업 근로자에게 '천원의 아침밥'을 제공하고, 점심 식비의 20%(월 최대 4만 원)를 지원합니다.
            """)

    # K-ART 청년 창작자 지원
    if is_youth_18_39:
        life_match_count += 1
        with st.expander("📌 K-ART 청년 창작자 지원 (중앙정부 - 2026년 신설)"):
            st.markdown("""
            * **지원 내용**: 순수 예술 분야에서 활동하는 만 39세 이하 청년 예술가에게 연 900만 원의 창작 지원금을 지급합니다.
            """)

    if life_match_count == 0:
        st.info("ℹ️ 현재 연령 조건에서는 지원 가능한 생활·문화 사업이 없습니다.")
    
    # ---------------------------------------------------------
    # 📱 5. 정책 정보 접근 및 참여
    # ---------------------------------------------------------
    st.subheader("📱 5. 정책 정보 접근 및 참여")

    with st.expander("📌 통합 플랫폼 '온통청년'"):
        st.markdown("""
        * **지원 내용**: 3,000여 개의 중앙·지자체 정책을 AI 챗봇 상담과 공공마이데이터 기반 자가진단으로 맞춤형 검색할 수 있습니다.
        * **안내**: 별도 회원가입 없이 간편 인증으로 이용 가능하며, 청년신문고를 통해 직접 정책 개선안을 제안할 수도 있습니다.
        """)

# 📈 시각화 대시보드 파트 (try-except 구문을 데이터 로드 전체에 적용)
st.write("---")

st.title("📊 군산시 청년 데이터 시각화 대시보드")
st.markdown("""**직접 KOSIS에서 수집한 데이터로 만든 대시보드입니다.**  
사회초년생을 위한 금융 서비스의 기초가 됩니다""")

st.info("""
**📅 데이터 기준:** 2024년 (현재 KOSIS에 등록된 가장 최신 통계)  
**🔍 수집 일시:** 2026년 2월 13일 (KOSIS API 기준)  
**🏢 데이터 출처:** 국가통계포털(KOSIS) - 군산시 청년통계 API  
**💡 2026년에 조회했는데, 왜 2024년 데이터가 나올까요?** 통계청이나 지자체에서 전수 조사 및 가공을 거쳐 KOSIS에 데이터를 공식 등재하는 데는 보통 1~2년의 시간이 걸립니다.  
따라서 현재 시점에서 얻을 수 있는 가장 최신의 군산시 청년 데이터라고 할 수 있습니다!""")

st.write("---")

# 🔌 [개조 포인트] CSV 대신 DB에서 데이터를 긁어오는 함수!
import streamlit as st
import pandas as pd
import sqlite3 # 👈 오류 해결 1: sqlite3 모듈을 확실하게 불러옵니다.
import plotly.express as px

# 🔌 1. DB에서 데이터를 안전하게 긁어오는 함수
@st.cache_data
def load_data():
    conn = sqlite3.connect("gunsan_youth_data.db")
    
    # 🔍 DB 안에 있는 진짜 테이블 목록을 싹 긁어와 봅니다.
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    try:
        # 기존 대시보드 그래프용 데이터
        pop_df = pd.read_sql("SELECT * FROM gunsan_population_tables", conn)
        house_df = pd.read_sql("SELECT * FROM gunsan_youth_housing_data", conn)
        wage_df = pd.read_sql("SELECT * FROM gunsan_youth_wage_data", conn)
        health_df = pd.read_sql("SELECT * FROM gunsan_youth_health_data", conn)
        
        # 새로 추가된 공공데이터 포털 데이터 (취업의 어려움 & 원룸 현황)
        difficulty_df = pd.read_sql("SELECT * FROM 전북특별자치도_취업의_어려움_사회조사_20221231", conn)
        room_df = pd.read_sql("SELECT * FROM 전북특별자치도_군산시_원룸_및_오피스텔_현황_20260203", conn)
        
        # ⚠️ 여기가 문제의 구간! 일단 읽어오되, 실패하면 목록을 담아 보냅니다.
        try:
            job_df = pd.read_sql("SELECT * FROM 전북특별자치도_연령별취업자_20211231", conn)
        except:
            job_df = pd.DataFrame({"DB 내 실제 테이블 목록": tables})

        # 🆕 9. 드디어 찾은 진짜 청년도약계좌 테이블 이름!
        saving_df = pd.read_sql("SELECT * FROM 서민금융진흥원_청년도약계좌_취급은행_현황_20250731", conn)
       
    except Exception as e:
        # 오류 해결 2: 에러가 나도 tables 변수를 안전하게 사용하도록 구조를 통일했습니다.
        pop_df = pd.DataFrame()
        house_df = pd.DataFrame()
        wage_df = pd.DataFrame()
        health_df = pd.DataFrame()
        difficulty_df = None
        room_df = pd.DataFrame()
        job_df = pd.DataFrame({"DB 내 실제 테이블 목록": tables})

    conn.close() 
    # 🌟 함수가 끝날 때 총 8개의 덩어리를 밖으로 뱉어줍니다!
    return pop_df, house_df, wage_df, health_df, difficulty_df, room_df, job_df, saving_df

try:
    # 🌟 밖에서도 8개의 변수로 똑같이 쪼개서 받아줍니다!
    pop_df, house_df, wage_df, health_df, difficulty_df, room_df, job_df, saving_df = load_data()
    
    # 📌 1 & 2번 영역
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📌 1. 군산시 청년 인구 비중 (2024)")
        total_gunsan_pop = 259000  
        youth_gunsan_pop = 56117   
        other_pop = total_gunsan_pop - youth_gunsan_pop
        
        pie_data = pd.DataFrame({
            "구분": ["청년 인구(18~39세)", "그 외 인구"],
            "인구수": [youth_gunsan_pop, other_pop]
        })
        
        fig1 = px.pie(pie_data, values='인구수', names='구분', 
                      title="군산시 전체 인구 대비 청년 비율",
                      color_discrete_sequence=['#FF6B6B', '#CCD1D1'])
        st.plotly_chart(fig1, use_container_width=True, key="fig1")

    with col2:
        st.subheader("🏠 2. 청년 주택 소유 비율 (%)")
        house_ratio = house_df[house_df['C2_NM'].str.contains("비율", na=False)]
        house_ratio['DT'] = pd.to_numeric(house_ratio['DT'])
        
        latest_year = house_ratio['PRD_DE'].max()
        latest_house = house_ratio[house_ratio['PRD_DE'] == latest_year]
        
        fig2 = px.bar(latest_house, x='C1_NM', y='DT', 
                      text='DT', title=f"{latest_year}년 연령대별 주택 소유 비율",
                      labels={'C1_NM': '구분', 'DT': '소유 비율(%)'},
                      color='C1_NM', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_traces(texttemplate='%{text}%', textposition='outside')
        st.plotly_chart(fig2, use_container_width=True, key="fig2")

    st.write("---")
    
    # 📌 3 & 4번 영역
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("💰 3. 청년 소득 분포 (천 명)")
        wage_df['DT'] = pd.to_numeric(wage_df['DT'])
        latest_wage_year = wage_df['PRD_DE'].max()
        latest_wage = wage_df[wage_df['PRD_DE'] == latest_wage_year]
        
        fig3 = px.bar(latest_wage, x='C2_NM', y='DT', color='C1_NM',
                      title=f"{latest_wage_year}년 소득 구간별 인구",
                      labels={'C2_NM': '소득 구간', 'DT': '인구(천명)'},
                      barmode='group')
        st.plotly_chart(fig3, use_container_width=True, key="fig3")

    with col4:
        st.subheader("🍺 4. 청년 건강 지표 (%)")
        health_df['DT'] = pd.to_numeric(health_df['DT'])
        latest_health_year = health_df['PRD_DE'].max()
        latest_health = health_df[health_df['PRD_DE'] == latest_health_year]
        
        fig4 = px.bar(latest_health, x='C2_NM', y='DT', color='C1_NM',
                      title=f"{latest_health_year}년 생활 건강 지표 비교",
                      labels={'C2_NM': '지표 구분', 'DT': '비율(%)'},
                      barmode='group', color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig4, use_container_width=True, key="fig4")

    # 📌 5번 영역
    st.write("---")
    st.subheader("📊 5. 군산시 청년(18~39세) 생활 지표 요약")
    
    house_trend = house_df[(house_df['C1_NM'].str.contains("18~39세")) & (house_df['C2_NM'].str.contains("비율"))]
    health_trend = health_df[health_df['C1_NM'].str.contains("18~39세")]

    house_trend['지표'] = '주택 소유 비율'
    health_trend['지표'] = health_trend['C2_NM']
    
    combined_summary = pd.concat([
        house_trend[['DT', '지표']],
        health_trend[['DT', '지표']]
    ])
    combined_summary['DT'] = pd.to_numeric(combined_summary['DT'])

    fig5 = px.bar(combined_summary, x='지표', y='DT', text='DT',
                  title="2024년 군산시 청년 주요 지표 모아보기",
                  labels={'지표': '지표 종류', 'DT': '수치(%)'},
                  color='지표', color_discrete_sequence=px.colors.qualitative.Safe)
    fig5.update_traces(texttemplate='%{text}%', textposition='outside')
    st.plotly_chart(fig5, use_container_width=True, key="fig5")

    # 📌 6번 영역 (취업의 어려움)
    st.write("---")
    st.subheader("🎯 6. 군산시 청년 취업의 어려움 (2022)")
    
    if difficulty_df is not None:
        st.info("💡 공공데이터 포털에서 수집한 '전북 사회조사' 데이터 중 **군산시** 데이터만 추출했습니다.")
        
        # [핵심] 군산시 데이터만 필터링
        # 컬럼 이름이나 데이터 상황에 맞게 조금씩 수정될 수 있습니다.
        gunsan_data = difficulty_df[difficulty_df['특성별2'] == '군산시']
        
        if not gunsan_data.empty:
            # 1. 시각화에 불필요한 '특성별1', '특성별2', '소계' 컬럼 제외하기
            exclude_cols = ['특성별1', '특성별2', '소계', '계']
            valid_cols = [col for col in gunsan_data.columns if col not in exclude_cols]
            
            # 2. 데이터를 그래프용으로 길게 재정렬 (Melt)
            melted_gunsan = pd.melt(
                gunsan_data, 
                id_vars=[], 
                value_vars=valid_cols,
                var_name='어려움 요인', 
                value_name='비율(%)'
            )
            
            # 3. 데이터 타입을 숫자로 변환 (에러 방지)
            melted_gunsan['비율(%)'] = pd.to_numeric(melted_gunsan['비율(%)'], errors='coerce')
            
            # 4. 비율이 높은 순으로 정렬
            melted_gunsan = melted_gunsan.sort_values(by='비율(%)', ascending=False)
            
            # 5. 가독성 높은 가로 막대 그래프 그리기!
            fig6 = px.bar(
                melted_gunsan, 
                x='비율(%)', 
                y='어려움 요인', 
                text='비율(%)',
                orientation='h',  # 가로 막대그래프
                title="군산시 청년이 느끼는 취업의 어려움 요인 (단위: %)",
                color='비율(%)', 
                color_continuous_scale='Blues'
            )
            
            fig6.update_traces(texttemplate='%{text}%', textposition='outside')
            fig6.update_layout(yaxis={'categoryorder':'total ascending'})  # 높은 순으로 정렬
            
            st.plotly_chart(fig6, use_container_width=True, key="fig6")
            
            # 6. 원본 데이터도 접이식(Expander)으로 깔끔하게 넣어주기
            with st.expander("🔍 군산시 원본 데이터 표 보기"):
                st.dataframe(gunsan_data[valid_cols], use_container_width=True)
                
        else:
            st.warning("⚠️ 데이터 내에서 '군산시' 행을 찾지 못했습니다. 원본 표의 '특성별2' 컬럼에 '군산시'가 맞는지 확인해 주세요.")
            # 찾지 못했을 땐 그냥 원본 표 보여주기
            st.dataframe(difficulty_df, use_container_width=True)
            
    else:
        st.warning("⚠️ DB에서 '취업의 어려움 사회조사' 테이블을 불러오지 못했습니다.")

# 📌 7번 영역 (원룸 및 오피스텔 분포 - 정밀화 버전)
    st.write("---")
    st.subheader("🏠 7. 군산시 읍면동별 원룸 및 오피스텔 분포")
    
    if room_df is not None and not room_df.empty:
        st.info("💡 군산시의 청년들이 거주하기 좋은 원룸과 오피스텔이 어느 동네에 밀집해 있는지 보여주는 데이터입니다.")
        
        col_list = room_df.columns.tolist()
        dong_col = None
        for c in col_list:
            if '동' in c or '소재지' in c or '주소' in c:
                dong_col = c
                break
                
        if dong_col:
            # ✂️ [긴급 수술] 번지수가 붙은 상세주소에서 '동'까지만 싹둑 자릅니다.
            # 예: "전북특별자치도 군산시 소룡동 831" -> "소룡동"
            def extract_dong(address):
                if not address:
                    return "기타"
                # 공백으로 주소를 쪼갠 뒤, '동', '읍', '면'으로 끝나는 글자만 찾아냅니다.
                parts = str(address).split()
                for part in parts:
                    if part.endswith('동') or part.endswith('읍') or part.endswith('면'):
                        return part
                return "기타"
            
            # 새로운 '정제된_동네' 컬럼을 만들어 동만 쏙 뽑아 넣습니다.
            room_df['정제된_동네'] = room_df[dong_col].apply(extract_dong)
            
            # 묶어서 개수 세기!
            room_counts = room_df['정제된_동네'].value_counts().reset_index()
            room_counts.columns = ['동네', '건물 수']
            
            # '기타'로 빠진 데이터는 제외하고 상위 10개 추출
            room_counts = room_counts[room_counts['동네'] != '기타']
            top_rooms = room_counts.head(10)
            
            # 가로 막대 그래프 그리기
            fig7 = px.bar(
                top_rooms, x='건물 수', y='동네', text='건물 수',
                orientation='h', title="군산시 원룸 및 오피스텔 밀집 동네 Top 10",
                color='건물 수', color_continuous_scale='Purples'
            )
            fig7.update_traces(texttemplate='%{text}개', textposition='outside')
            fig7.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig7, use_container_width=True, key="fig7")
            
        else:
            st.warning("⚠️ 동네를 구분할 수 있는 컬럼을 찾지 못했습니다.")
            
        with st.expander("🔍 군산시 원룸 및 오피스텔 원본 표 보기"):
            st.dataframe(room_df, use_container_width=True)
    else:
        st.warning("⚠️ DB에서 '원룸 및 오피스텔 현황' 테이블을 불러오지 못했습니다.")

    # 📌 8. 전북특별자치도 연령별 취업자 비중 (완성 버전!)
    st.write("---")
    st.subheader("💼 8. 전북특별자치도 연령별 취업자 비중")
    
    if 'job_df' in locals() and job_df is not None and not job_df.empty:
        st.info("💡 전북 전체 취업자 중 청년층(15~39세)이 차지하는 비중을 한눈에 보여줍니다.")
        
        try:
            # 1. 데이터 전처리 (가장 최근 연도 기준)
            # 텍스트로 되어있을지 모를 숫자를 진짜 숫자로 변환
            job_df['연도'] = pd.to_numeric(job_df['연도'], errors='coerce')
            job_df['취업자수'] = pd.to_numeric(job_df['취업자수'], errors='coerce')
            
            # 가장 최근 연도 찾기
            latest_year = job_df['연도'].max()
            
            # 최근 연도 데이터만 쏙 빼오기
            recent_job_df = job_df[job_df['연도'] == latest_year].copy()
            
            # 2. 청년층(15~39세) vs 그 외 연령대 분류기
            def categorize_age(age):
                youth_ages = ['15~19세', '20~24세', '25~29세', '30~34세', '35~39세']
                if age in youth_ages:
                    return '청년층 (15~39세)'
                else:
                    return '그 외 연령대'
                    
            recent_job_df['연령_그룹'] = recent_job_df['연령'].apply(categorize_age)
            
            # 3. 그룹별로 취업자수 다 더하기
            grouped_job = recent_job_df.groupby('연령_그룹')['취업자수'].sum().reset_index()
            
            # 4. 파이 차트 그리기 🎨
            fig8 = px.pie(
                grouped_job, values='취업자수', names='연령_그룹', 
                title=f"{int(latest_year)}년 전북 취업자 중 청년층 비율",
                color='연령_그룹', 
                color_discrete_map={'청년층 (15~39세)': '#3498DB', '그 외 연령대': '#E5E7E9'}
            )
            
            # 차트 안팎으로 퍼센트와 이름 예쁘게 표시
            fig8.update_traces(textinfo='percent+label', textfont_size=15, pull=[0.05, 0])
            st.plotly_chart(fig8, use_container_width=True, key="fig8")
            
            # 표도 숨겨서 놔두기
            with st.expander("🔍 연령별 취업자 원본 표 보기"):
                st.dataframe(recent_job_df, use_container_width=True)
                
        except Exception as e:
            st.error(f"데이터를 차트로 그리는 중 문제가 발생했습니다: {e}")
            st.dataframe(job_df)

    else:
        st.warning("⚠️ DB에서 '연령별취업자' 테이블을 불러오지 못했습니다.")

# 📌 9. 군산시 청년도약계좌 취급은행 현황 (최종 UI 개선 버전)
    st.write("---")
    st.subheader("💰 9. 청년도약계좌 취급은행 현황")
    
    if 'saving_df' in locals() and saving_df is not None and not saving_df.empty:
        st.info("💡 군산시 청년들이 도약계좌를 개설할 수 있는 취급 은행 목록입니다.")
        
        try:
            # 은행명 컬럼에서 고유한 은행 이름들만 쏙 뽑아내기
            bank_col = '은행명'
            banks = saving_df[bank_col].dropna().unique().tolist()
            
            st.markdown("#### 🏦 가입 가능한 제휴 은행 (가나다순)")
            
            # 은행 목록을 가나다순으로 정렬
            banks.sort()
            
            # 한 줄에 3개씩 예쁜 카드로 배치하기 위해 Streamlit 컬럼 기능 활용!
            for i in range(0, len(banks), 3):
                cols = st.columns(3)
                # 첫 번째 칸
                if i < len(banks):
                    cols[0].success(f"**{banks[i]}**")
                # 두 번째 칸
                if i+1 < len(banks):
                    cols[1].success(f"**{banks[i+1]}**")
                # 세 번째 칸
                if i+2 < len(banks):
                    cols[2].success(f"**{banks[i+2]}**")
            
            st.write("") # 줄바꿈용 공백
            
            # 원본 데이터도 하단에 얌전히 묻어두기
            with st.expander("🔍 원본 데이터 표 보기"):
                st.dataframe(saving_df, use_container_width=True)
                
        except Exception as e:
            st.error(f"데이터를 불러오는 중 문제가 발생했습니다: {e}")
            st.dataframe(saving_df, use_container_width=True)
            
    else:
        st.warning("⚠️ DB에서 '청년도약계좌' 테이블을 불러오지 못했습니다.")
    
# --- 파일 끝 ---
except FileNotFoundError as e:
    st.error(f"🚨 파일을 찾을 수 없습니다: {e}")
except Exception as e:
    st.error(f"🚨 오류가 발생했습니다: {e}")
