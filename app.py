import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3

st.set_page_config(page_title="군산시 청년 데이터 & 맞춤 혜택", layout="wide")

st.title("📊 군산시 청년 데이터 시각화 대시보드")
st.markdown("""**직접 KOSIS에서 수집한 데이터로 만든 대시보드입니다.**   
사회초년생을 위한 금융 서비스의 기초가 됩니다""")
st.write("---")

# 📌 여기에 기간과 출처를 명확하게 명시해 줍니다!
st.info("""
**📅 데이터 기준:**  
2024년 (현재 KOSIS에 등록된 가장 최신 통계)  
**🔍 수집 일시:**   
2026년 2월 13일 (KOSIS API 기준)  
**🏢 데이터 출처:**   
국가통계포털(KOSIS) - 군산시 청년통계 API  
**💡 2026년에 조회했는데,   
왜 2024년 데이터가 나올까요?**   
통계청이나 지자체에서 전수 조사 및 가공을 거쳐 KOSIS에 데이터를 공식 등재하는 데는 보통 1~2년의 시간이 걸립니다.  
따라서 현재 시점에서 얻을 수 있는 가장 최신의 군산시 청년 데이터라고 할 수 있습니다!""")

# DB에서 데이터 로드하는 함수
@st.cache_data
def load_data_from_db():
    conn = sqlite3.connect("gunsan_youth.db")
    pop_df = pd.read_sql("SELECT * FROM population", conn)
    house_df = pd.read_sql("SELECT * FROM housing", conn)
    wage_df = pd.read_sql("SELECT * FROM wage", conn)
    health_df = pd.read_sql("SELECT * FROM health", conn)
    conn.close()
    return pop_df, house_df, wage_df, health_df

try:
    pop_df, house_df, wage_df, health_df = load_data_from_db()

    st.write("---")
    st.header("🎯 내 맞춤형 청년 정책 찾아보기")
    st.markdown("본인의 조건을 입력하시면 2026년 실제 시행 중인 청년 정책과의 매칭 결과를 보여드립니다.")
    
    # 꼼꼼한 정책 연동을 위한 4단 컬럼 구성
    uc1, uc2, uc3, uc4 = st.columns(4)
    with uc1:
        age = st.number_input("만 나이를 입력하세요", min_value=0, max_value=100, value=25)
    with uc2:
        income_level = st.selectbox("소득 기준을 선택하세요", 
                                    ["중위소득 60% 이하 (1인 가구 월 약 133만 원)", 
                                     "중위소득 100% 이하", 
                                     "중위소득 180% 이하 (1인 가구 월 약 401만 원)", 
                                     "해당 없음 / 기준 초과"])
    with uc3:
        has_house = st.radio("본인 명의의 주택이 있나요?", ["아니오 (무주택)", "예 (유주택)"])
    with uc4:
        housing_condition = st.radio("임차 조건 만족 여부", ["보증금 5천만 원 & 월세 70만 원 이하", "초과 또는 자가"])

    # 추천 알고리즘 가동 버튼
    if st.button("내 맞춤 혜택 결과 보기 🚀"):
        st.success("🎉 조건에 부합하는 정책 매칭 결과입니다.")
        
        is_target_youth = 19 <= age <= 39
        is_mind_youth = 18 <= age <= 39
        is_financial_youth = 19 <= age <= 34
        
        # 혜택 1: 군산시 청년월세 특별지원 (2차 사업 등 기준)
        if (is_target_youth and has_house == "아니오 (무주택)" and 
            income_level == "중위소득 60% 이하 (1인 가구 월 약 133만 원)" and 
            housing_condition == "보증금 5천만 원 & 월세 70만 원 이하"):
            
            st.markdown("""
            🏠 **[군산시 청년월세 특별지원 대상]**
            * **내용:** 무주택 청년들의 주거 안정을 위해 월 최대 20만 원씩 12개월간 월세를 지원합니다.
            * **안내:** 2026년 확대 적용되는 군산 STAY 주거지원사업과의 중복 수혜 여부를 군산시 청년뜰 또는 시청을 통해 꼭 확인해 보세요!
            """)
            
        # 혜택 2: 전국민 마음투자 지원사업 (청년마음건강지원)
        if is_mind_youth:
            st.markdown("""
            🧠 **[전국민 마음투자 지원사업 대상]**
            * **내용:** 우울, 불안 등 정서적 어려움을 겪거나 심리 상담이 필요한 청년에게 전문 심리상담 서비스 바우처가 제공됩니다.
            * **안내:** 총 8회의 전문 심리상담을 지원받으실 수 있으며, 소득 수준에 따라 본인부담금이 일부 발생할 수 있습니다.
            """)
            
        # 혜택 3: 청년도약계좌 등 정부 지원 금융 상품
        if is_financial_youth and income_level in ["중위소득 60% 이하 (1인 가구 월 약 133만 원)", "중위소득 100% 이하", "중위소득 180% 이하 (1인 가구 월 약 401만 원)"]:
            st.markdown("""
            💰 **[청년도약계좌 가입 대상]**
            * **내용:** 목돈 마련을 희망하는 청년을 위한 정부 지원 금융 상품입니다.
            * **안내:** 개인소득 및 가구소득(중위 180% 이하) 기준을 충족하므로 가입 신청이 가능합니다. 3년 이상 유지 시 중도 해지해도 비과세 혜택과 정부 기여금을 지원받을 수 있습니다.
            """)
            
        # 연령 조건 예외 처리
        if not (is_mind_youth or is_target_youth):
            st.warning("아쉽게도 현재는 청년(만 18세~39세) 대상의 특화 정책들만 등록되어 있습니다. 향후 전 연령층 혜택으로 확대될 예정입니다.")

    # 하단 시각화 대시보드는 그대로 유지
    st.write("---")
    st.header("📈 참고: 군산시 청년 통계 대시보드")
    
    col1, col2 = st.columns(2)
    with col1:
        total_gunsan_pop = 259000  
        youth_gunsan_pop = 56117   
        other_pop = total_gunsan_pop - youth_gunsan_pop
        pie_data = pd.DataFrame({"구분": ["청년 인구(18~39세)", "그 외 인구"],"인구수": [youth_gunsan_pop, other_pop]})
        fig1 = px.pie(pie_data, values='인구수', names='구분', title="군산시 전체 인구 대비 청년 비율", color_discrete_sequence=['#FF6B6B', '#CCD1D1'])
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        house_ratio = house_df[house_df['C2_NM'].str.contains("비율", na=False)]
        house_ratio['DT'] = pd.to_numeric(house_ratio['DT'])
        latest_house = house_ratio[house_ratio['PRD_DE'] == house_ratio['PRD_DE'].max()]
        fig2 = px.bar(latest_house, x='C1_NM', y='DT', text='DT', title="연령대별 주택 소유 비율", color='C1_NM', color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_traces(texttemplate='%{text}%', textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)

except FileNotFoundError as e:
    st.error(f"🚨 파일을 찾을 수 없습니다: {e}")
except Exception as e:
    st.error(f"🚨 오류가 발생했습니다: {e}")
