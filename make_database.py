import sqlite3
import pandas as pd

def create_youth_database():
    # 1. 데이터베이스 파일 생성 및 연결 (파일이 없으면 알아서 새로 만듭니다)
    conn = sqlite3.connect("gunsan_youth.db")
    print("🔋 'gunsan_youth.db' 데이터베이스에 성공적으로 연결되었습니다.")
    
    # 2. 우리가 가진 CSV 파일 목록
    csv_files = {
        "population": "gunsan_youth_population_success.csv",
        "housing": "gunsan_youth_housing_data.csv",
        "wage": "gunsan_youth_wage_data.csv",
        "health": "gunsan_youth_health_data.csv"
    }
    
    # 3. CSV 파일을 하나씩 읽어서 DB의 테이블로 저장
    for table_name, file_name in csv_files.items():
        try:
            # CSV 파일 읽기
            df = pd.read_csv(file_name)
            
            # DB에 테이블로 저장 (이미 같은 이름의 테이블이 있다면 덮어쓰기)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            print(f"✅ '{file_name}' 데이터를 '{table_name}' 테이블로 이사 완료!")
            
        except FileNotFoundError:
            print(f"🚨 '{file_name}' 파일이 폴더에 없습니다. 건너뜁니다.")
        except Exception as e:
            print(f"🚨 '{table_name}' 처리 중 오류 발생: {e}")
            
    # 4. 연결 종료
    conn.close()
    print("\n🎉 모든 데이터가 하나의 DB 파일로 통합되었습니다!")

if __name__ == "__main__":
    create_youth_database()
