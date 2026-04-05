import streamlit as st
import pandas as pd
import sqlite3  # 👈 이 녀석이 빠져 있어서 에러가 났던 겁니다!
import plotly.express as px

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
