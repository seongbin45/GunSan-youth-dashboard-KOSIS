import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="군산시 청년 맞춤 혜택 찾기", layout="wide")

st.title("📊 군산시 청년 데이터 시각화 대시보드")
st.markdown("""**직접 KOSIS에서 수집한 데이터로 만든 대시보드입니다.** 사회초년생을 위한 금융 서비스의 기초가 됩니다""")
st.write("---")

# 📌 청소년과 대학생을 위해 친절하게 수정한 안내판!
st.info("""
### 🙋‍♂️ "이 단어, 무슨 뜻인가요?"

**1. 중위소득이 뭔가요?**
전체 가구를 소득순으로 세웠을 때 딱 중간인 집의 소득이에요. 
부모님께 "우리 집 건강보험료가 중위소득 몇 % 정도예요?" 라고 물어보면 내가 혜택을 받을 수 있는지 바로 알 수 있어요!

**2. 임차인이 뭐예요?**
집을 빌려 쓰는 '손님'인 여러분을 말해요. 

**3. 보증금 vs 월세**
* **보증금**: 나중에 나갈 때 **돌려받는** 큰돈 (잠시 맡겨두는 돈)
* **월세**: 매달 **사라지는** 집 이용료 (유튜브 구독료 같은 것)

**4. 이자 지원이 왜 좋아요?**
은행에서 큰돈을 빌리면 '빌린 값(이자)'을 내야 해요. 군산시가 이 '빌린 값'을 대신 내주니까, 여러분은 공짜나 다름없이 돈을 빌릴 수 있는 거예요!
""")
st.write("---")

st.info("""
🔰 **[청소년과 대학생을 위한 위한 용어 사전]**
* 🏢 **기준 중위소득 (나의 소득 등수)**
  👉 우리나라 사람들을 소득 순으로 1등부터 100등까지 줄을 세웠을 때, 딱 중간인 **50등 사람의 소득**이에요. '중위소득 60%'는 그 중간 사람보다 소득이 적은 친구들을 정부가 먼저 집중해서 도와주겠다는 뜻입니다!
* 🎁 **바우처 (지정 이용권)**
  👉 현금 대신 주는 것으로, 정해진 곳 에서만 현금처럼 쓸 수 있는 특별한 쿠폰이에요. (예: 심리상담 바우처 등)
* 🛡️ **비과세 (세금 안 뗌!)**
  👉 원래 은행 이자를 받으면 세금을 내야 하지만, 이건 **세금을 한 푼도 떼지 않고 이자를 통째로 다 주는** 엄청난 혜택이에요.
* 🤝 **매칭 지원 (1+1 저축)**
  👉 내가 10만 원을 저축하면, 나라나 군산시가 똑같이 **10만 원을 공짜로 더 얹어주는** 꿀이득 시스템이에요!
""")

st.header("📋 나의 조건 입력하기")

col1, col2, col3, col4 = st.columns(4)

with col1:
    age = st.number_input("만 나이를 입력하세요", min_value=15, max_value=50, value=25)

with col2:
    income_level = st.selectbox("가구 소득 수준을 선택하세요", [
        "기준 중위소득 60% 이하 (저소득층 및 집중 주거지원 대상)",
        "기준 중위소득 100% 이하",
        "기준 중위소득 140% 이하",
        "기준 중위소득 150% 이하",
        "기준 중위소득 180% 이하",
        "해당 없음 (소득 기준 초과)"
    ])

with col3:
    has_house = st.radio("본인 명의의 주택을 소유하고 계신가요?", ["아니오 (무주택)", "예 (유주택)"])

with col4:
    job_status = st.radio("현재 경제 활동 상태는 무엇인가요?", ["미취업 (구직 중)", "창업자 (7년 미만)", "취업자 (군산 소재 기업)"])

st.write("---")

# 추천 알고리즘 가동 버튼
if st.button("내 맞춤 혜택 결과 보기 🚀"):
    st.success("🎉 입력하신 조건에 부합하는 군산시 청년 정책 매칭 결과입니다.")
    
    is_youth_18_39 = 18 <= age <= 39
    is_youth_19_34 = 19 <= age <= 34
    is_youth_19_39 = 19 <= age <= 39
    is_youth_19_49 = 19 <= age <= 49

    st.subheader("💰 1. 청년 자산 형성 지원 상품")
    
    if is_youth_19_34 and income_level != "해당 없음 (소득 기준 초과)":
        st.markdown("""
        📌 **청년도약계좌 (중앙정부)**
        * **지원 내용**: 매월 일정 금액 저축 시 정부 기여금과 이자 비과세 혜택을 지원하여 목돈 마련을 돕습니다.
        * **안내**: 개인 소득(7,500만 원 이하) 기준과 가구 소득(중위 180% 이하) 기준을 모두 충족하셔야 최종 승인됩니다.
        """)
        
    if is_youth_18_39 and income_level in ["기준 중위소득 60% 이하 (저소득층 및 집중 주거지원 대상)", "기준 중위소득 100% 이하", "기준 중위소득 140% 이하"] and job_status != "미취업 (구직 중)":
        st.markdown("""
        📌 **전북청년 함께 두배적금 (전북특별자치도/군산시)**
        * **지원 내용**: 월 10만 원을 저축하면 지자체에서 동일 금액(10만 원)을 1:1로 매칭 지원하여 2년 후 두 배의 자산을 형성합니다.
        * **안내**: 도내 거주 및 근로(창업) 중인 청년을 대상으로 합니다.
        """)

    st.subheader("🏠 2. 청년 주거 안정 지원 사업")
    
    if has_house == "아니오 (무주택)":
        if is_youth_19_34 and income_level == "기준 중위소득 60% 이하 (저소득층 및 집중 주거지원 대상)":
            st.markdown("""
            📌 **청년월세 한시 특별지원 사업**
            * **지원 내용**: 실제 납부하는 임대료의 월 최대 20만 원을 최대 12개월간 현금으로 지원합니다.
            * **안내**: 청년 독립가구 기준 중위소득 60% 이하 조건 외에 임차보증금 5,000만 원 이하 및 월세 70만 원 이하 주택 조건이 추가로 필요합니다.
            """)
            
        if (is_youth_19_49 and job_status == "창업자 (7년 미만)") or (is_youth_19_39 and job_status == "취업자 (군산 소재 기업)"):
            st.markdown("""
            📌 **군산 STAY 주거지원사업**
            * **지원 내용**: 최대 2년(24개월) 동안 임대주택 보증금 최대 350만 원, 월 임차료 최대 10만 원을 지원합니다.
            * **안내**: 군산시 관내 LH 소유 임대 원룸 및 아파트 등에 입주할 수 있습니다.
            """)
            
        if is_youth_18_39 and income_level != "해당 없음 (소득 기준 초과)":
            st.markdown("""
            📌 **신혼부부 및 청년 전세자금 대출이자 지원**
            * **지원 내용**: 전세 임차보증금 대출 잔액의 최대 2% (연 최대 200만 원 한도) 내에서 이자를 지원합니다.
            * **안내**: 가구당 중위소득 180% 이하 및 전세보증금 3억 원 이하 조건을 만족해야 합니다.
            """)
    else:
        st.info("💡 주택을 보유 중이시라 무주택 대상 주거 정책(월세 지원, 전세대출 이자 지원 등) 매칭에서 제외되었습니다.")

    st.subheader("🏃‍♂️ 3. 청년 구직 및 정착 지원")
    
    if job_status == "미취업 (구직 중)":
        if is_youth_18_39 and income_level not in ["기준 중위소득 180% 이하", "해당 없음 (소득 기준 초과)"]:
            st.markdown("""
            📌 **전북형 청년활력수당**
            * **지원 내용**: 미취업 청년의 구직 활동을 위해 1인당 월 50만 원씩 최대 6개월간 지원합니다.
            * **안내**: 중위소득 150% 이하인 미취업 청년을 대상으로 합니다.
            """)
            
        if 18 <= age <= 34:
            st.markdown("""
            📌 **청년도전지원사업 (군산시 청년뜰)**
            * **지원 내용**: 구직 단념 청년들을 위한 맞춤형 프로그램을 제공하고, 참여 시 최대 350만 원의 참여 수당을 지급합니다.
            """)
            
    st.subheader("🧠 4. 청년 심리 건강 지원")
    
    if is_youth_19_34:
        st.markdown("""
        📌 **청년 마음건강지원사업 (전국민 마음투자 지원)**
        * **지원 내용**: 우울, 불안 등 정서적 어려움이 있어 심리 상담이 필요한 청년에게 전문 심리상담 바우처를 총 8회(1회당 50분 이상) 제공합니다.
        * **안내**: 소득 및 재산 기준은 전혀 없으며, 본인 부담금은 소득 수준에 따라 일부 차등 발생할 수 있습니다.
        """)

    if age > 49:
        st.warning("⚠️ 입력하신 나이(만 50세 이상)는 현재 등록된 군산시 청년 특화 정책의 연령 범위를 벗어납니다. 중장년층을 위한 정책을 확인해 주세요.")


# 📈 시각화 대시보드 파트 (try-except 구문을 데이터 로드 전체에 적용)
st.write("---")
st.header("📈 군산시 청년 통계 대시보드")

st.info("""
**📅 데이터 기준:** 2024년 (현재 KOSIS에 등록된 가장 최신 통계)  
**🔍 수집 일시:** 2026년 2월 13일 (KOSIS API 기준)  
**🏢 데이터 출처:** 국가통계포털(KOSIS) - 군산시 청년통계 API  
**💡 2026년에 조회했는데, 왜 2024년 데이터가 나올까요?** 통계청이나 지자체에서 전수 조사 및 가공을 거쳐 KOSIS에 데이터를 공식 등재하는 데는 보통 1~2년의 시간이 걸립니다.  
따라서 현재 시점에서 얻을 수 있는 가장 최신의 군산시 청년 데이터라고 할 수 있습니다!""")

st.write("---")

# 🔌 [개조 포인트] CSV 대신 DB에서 데이터를 긁어오는 함수!
@st.cache_data
def load_data_from_db():
    # 데이터베이스 연결
    conn = sqlite3.connect("gunsan_youth.db")
    
    # SQL 쿼리를 날려 데이터프레임으로 바로 읽어옵니다.
    pop_df = pd.read_sql("SELECT * FROM population", conn)
    house_df = pd.read_sql("SELECT * FROM housing", conn)
    wage_df = pd.read_sql("SELECT * FROM wage", conn)
    health_df = pd.read_sql("SELECT * FROM health", conn)
    
    conn.close() # 작업이 끝나면 안전하게 닫아줍니다.
    return pop_df, house_df, wage_df, health_df

try:
    # DB에서 데이터 로드
    pop_df, house_df, wage_df, health_df = load_data_from_db()

    # (이하 시각화 차트를 그리는 코드는 기존과 동일하게 유지됩니다!)
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
        st.plotly_chart(fig1, use_container_width=True)

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
        st.plotly_chart(fig2, use_container_width=True)

    st.write("---")
    
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
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.subheader("🍺 4. 청년 건강 지표 (%)")
        health_df['DT'] = pd.to_numeric(health_df['DT'])
        latest_health_year = health_df['PRD_DE'].max()
        latest_health = health_df[health_df['PRD_DE'] == latest_health_year]
        
        fig4 = px.bar(latest_health, x='C2_NM', y='DT', color='C1_NM',
                      title=f"{latest_health_year}년 생활 건강 지표 비교",
                      labels={'C2_NM': '지표 구분', 'DT': '비율(%)'},
                      barmode='group', color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig4, use_container_width=True)

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
    st.plotly_chart(fig5, use_container_width=True)

except FileNotFoundError as e:
    st.error(f"🚨 파일을 찾을 수 없습니다: {e}")
except Exception as e:
    st.error(f"🚨 오류가 발생했습니다: {e}")
