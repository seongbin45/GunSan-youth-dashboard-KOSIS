# 군산시 청년 금융·정책 대시보드

군산시 청년이 자신의 월 소득을 기준으로 예산을 세우고, 지출을 기록하며, KOSIS 기반 지역 통계와 청년 정책 정보를 한 화면에서 확인할 수 있는 Streamlit 대시보드입니다.

이 프로젝트는 사회초년생과 청년 사용자가 복잡한 금융·정책 정보를 쉽게 이해하고, 군산시 청년 데이터에 근거해 저축·주거·취업·복지 관련 의사결정을 돕는 것을 목표로 합니다.

- 월 소득과 저축 강도에 따른 예산 배분
- Google Sheets 기반 지출 기록 및 분석
- 국가·군산시 청년 정책 조건별 안내
- KOSIS 기반 군산시 청년 인구·주거·소득·건강 데이터 시각화
- 온통청년 API 기반 정책·청년센터·콘텐츠 조회

## 사용된 기술

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-150458?style=flat-square&logo=pandas&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.18+-3F4F75?style=flat-square&logo=plotly&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Data-003B57?style=flat-square&logo=sqlite&logoColor=white)
![Google Sheets](https://img.shields.io/badge/Google%20Sheets-API-34A853?style=flat-square&logo=googlesheets&logoColor=white)
![pytest](https://img.shields.io/badge/pytest-8.0+-0A9EDC?style=flat-square&logo=pytest&logoColor=white)

주요 스택은 Python, Streamlit, Pandas, Plotly, SQLite, Google Sheets API, 온통청년 API, pytest입니다.

## 미리보기

현재 저장소에는 앱 실행 화면 스크린샷 파일이 포함되어 있지 않습니다.

추후 `streamlit run app.py`로 앱을 실행한 뒤 다음 화면을 캡처해 이 섹션에 추가하면 프로젝트를 더 빠르게 이해할 수 있습니다.

- 메인 화면: 월 소득 입력 및 저축 강도별 예산 배분
- 가계부 화면: 지출 입력, 카테고리별 지출 차트, 목표 대비 달성 현황
- 군산시 청년 데이터 화면: KOSIS 기반 인구·주거·소득·건강 지표 차트
- 청년혜택 업데이트 화면: 온통청년 정책·센터·콘텐츠 목록 조회

## 시작하기 / 설치

### 1. 저장소 복제

```bash
git clone https://github.com/seongbin45/GunSan-youth-dashboard-KOSIS.git
cd GunSan-youth-dashboard-KOSIS
```

### 2. 가상환경 생성

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 앱 실행

```bash
streamlit run app.py
```

실행 후 브라우저에서 Streamlit이 안내하는 로컬 주소로 접속합니다. 기본 포트는 보통 `http://localhost:8501`입니다.

GitHub Codespaces 또는 Dev Container 환경에서는 `.devcontainer/devcontainer.json` 설정에 따라 8501 포트가 자동 포워딩되고 Streamlit 앱이 실행될 수 있습니다.

## 환경 변수 및 Secrets

기본 KOSIS 데이터 대시보드는 저장소에 포함된 CSV/SQLite 파일을 사용하므로 별도 API 키 없이도 주요 시각화 화면을 확인할 수 있습니다.

일부 기능은 외부 서비스 연결을 위해 Streamlit Secrets 또는 환경 변수가 필요합니다.

### Google Sheets 가계부

`pages/1_가계부.py`는 Google Sheets에 지출 데이터를 저장합니다. 사용하려면 `.streamlit/secrets.toml`에 서비스 계정 정보를 설정합니다.

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/your-service-account"
```

### 온통청년 API

`pages/7_청년혜택업데이트.py`는 온통청년 정책·청년센터·콘텐츠 데이터를 조회하고 캐시합니다.

필수 또는 권장 설정값:

| 이름 | 용도 |
| --- | --- |
| `YOUTH_API_KEY` | 정책 API 조회 키 |
| `YOUTH_CENTER_API_KEY` | 청년센터 API 조회 키 |
| `YOUTH_CONTENT_API_KEY` | 콘텐츠 API 조회 키 |
| `YOUTH_CACHE_DB_PATH` | 캐시 DB 경로, 기본값 `youth_cache.db` |
| `YOUTH_API_TIMEOUT_SECONDS` | API 요청 타임아웃 |
| `YOUTH_API_RATE_LIMIT_PER_MINUTE` | 분당 요청 제한 |

환경 변수로 설정하거나 Streamlit Secrets에 같은 이름으로 등록할 수 있습니다.

## 사용법

### 월 예산 계획하기

1. 앱을 실행합니다.
2. 메인 화면에서 월 소득 또는 용돈을 입력합니다.
3. 저축 강도 슬라이더를 1~10단계 중 선택합니다.
4. 저축, 고정비, 여가·식비 예산이 자동 계산됩니다.

### 지출 기록하기

1. 왼쪽 사이드바에서 `가계부` 페이지로 이동합니다.
2. 날짜, 대분류, 소분류, 금액, 메모를 입력합니다.
3. 저장 후 카테고리별 지출 비율과 목표 대비 달성 현황을 확인합니다.

### 군산시 청년 데이터 보기

1. `군산시 청년 데이터` 페이지로 이동합니다.
2. 청년 인구 비중, 주택 소유 비율, 소득 분포, 건강 지표를 확인합니다.
3. 원본 데이터 표가 필요한 경우 각 확장 영역에서 상세 데이터를 확인합니다.

### 청년 정책 찾기

1. `국가 지원 청년 혜택` 또는 `군산시 청년 정책` 페이지로 이동합니다.
2. 나이, 소득 수준, 주택 보유 여부, 취업·창업·농업 등 조건을 입력합니다.
3. 조건에 맞는 자산 형성, 주거, 취업, 생활·복지 정책을 확인합니다.

### 온통청년 데이터 업데이트하기

1. `청년혜택업데이트` 페이지로 이동합니다.
2. 데이터 구분에서 정책, 청년센터, 콘텐츠 중 하나를 선택합니다.
3. 검색어와 목록 개수를 설정합니다.
4. 필요한 경우 `지금 동기화`를 눌러 최신 데이터를 캐시에 반영합니다.

## 주요 기능

- 청년 머니 플래너: 월 소득과 저축 강도 기반 예산 추천
- 가계부: Google Sheets 연동 지출 입력, 저장, 분석
- 저축 단계 가이드: 1~10단계 저축 비율, 실천 팁, 목표 시뮬레이션
- 국가 청년 혜택: 적금, 주거, 취업, 신용·금융, 교육 지원 정보 검색
- 군산시 청년 정책: 나이·소득·주거·직업 조건 기반 정책 매칭
- 군산시 청년 데이터: KOSIS와 공공데이터 기반 통계 시각화
- 금융 용어 사전: 사회초년생을 위한 저축·신용·세금·일상 금융 용어 설명
- 청년혜택 업데이트: 온통청년 API 목록 조회, 상세 조회, 캐시, 30분 주기 동기화

## 로드맵

- Streamlit 실행 화면 스크린샷 및 GIF 추가
- 정책 정보의 기준 연도와 최신성 검증 절차 강화
- KOSIS 및 공공데이터 갱신 자동화 개선
- 중복된 Streamlit 화면 구성과 정책 설명 코드 정리
- Google Sheets 연결 실패 시 로컬 저장 폴백 추가
- 테스트 범위 확대: API 클라이언트 오류 처리, Streamlit 페이지 데이터 로딩, DB 스키마 검증

## 프로젝트 구조

```text
.
├── app.py                         # Streamlit 메인 앱
├── pages/                         # Streamlit 멀티 페이지 화면
│   ├── 1_가계부.py
│   ├── 2_저축단계설정.py
│   ├── 3_국가 지원 청년 혜택.py
│   ├── 4_군산시 청년 정책.py
│   ├── 5_군산시 청년 데이터.py
│   ├── 6_금융용어.py
│   └── 7_청년혜택업데이트.py
├── finfit_youth/                  # 온통청년 API, 캐시, 동기화 서비스
├── tests/                         # pytest 테스트
├── gunsan_youth_data.db           # 군산시 청년 데이터 SQLite DB
├── gunsan_youth.db                # CSV 통합용 SQLite DB
├── gunsan_*.csv                   # KOSIS 테이블 목록 데이터
├── gunsan_youth_*_data.csv        # 군산시 청년 지표 데이터
├── make_database.py               # CSV를 SQLite DB로 통합하는 스크립트
└── requirements.txt               # Python 의존성
```

## 데이터 출처

- KOSIS 국가통계포털: 군산시 청년 인구, 주거, 일자리, 창업, 복지, 건강 관련 통계
- 공공데이터 및 지역 데이터: 군산시 원룸·오피스텔 현황, 취업 어려움 등 일부 보조 데이터
- 온통청년 API: 정책, 청년센터, 콘텐츠 목록 및 상세 정보
- Google Sheets: 사용자가 입력한 개인 가계부 데이터 저장소

정책과 통계는 수집 시점, 제공 기관의 갱신 주기, API 권한 상태에 따라 실제 최신 정보와 차이가 있을 수 있습니다. 중요한 신청 조건은 반드시 공식 사이트에서 다시 확인하세요.

## 테스트

테스트는 `pytest`로 실행합니다.

```bash
pytest
```

현재 테스트는 `finfit_youth.service.YouthDataService`의 목록 캐시, 검색 필터, 상세 조회 캐시 흐름을 중심으로 검증합니다.

## 기여 방법

1. GitHub Issues에 버그, 개선 제안, 데이터 오류를 등록합니다.
2. 작업용 브랜치를 만듭니다.
3. 변경 후 `pytest`를 실행해 기존 테스트가 통과하는지 확인합니다.
4. 변경 내용, 확인한 테스트, 관련 이슈를 적어 Pull Request를 생성합니다.

정책 데이터나 통계 수치를 수정할 때는 출처, 수집일, 기준 연도를 함께 남겨 주세요.

## 지원 / 문의

질문, 오류 제보, 기능 제안은 저장소의 [GitHub Issues](https://github.com/seongbin45/GunSan-youth-dashboard-KOSIS/issues)를 사용해 주세요.

## 라이선스

현재 저장소에는 별도의 `LICENSE` 파일이 포함되어 있지 않습니다.

코드, 데이터, 문서의 사용·수정·배포 조건은 저장소 소유자에게 확인한 뒤 사용하세요.
