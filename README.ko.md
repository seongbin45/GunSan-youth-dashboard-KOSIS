# FinFit

사회초년생과 청년이 흩어져 있는 금융·정책 정보를 쉽게 이해하고, 자신의 조건에 맞는 혜택 후보를 빠르게 찾도록 돕는 Streamlit MVP입니다.

## 1. 왜 만들었는가

청년 혜택 정보는 기관별로 흩어져 있고, 신청 조건에는 중위소득, 무주택, 비과세, 매칭지원 같은 낯선 용어가 많습니다. 사용자는 혜택이 있는지조차 모른 채 포기하기 쉽습니다.

FinFit은 이 문제를 다음 관점으로 풉니다.

- 최신 청년 혜택을 업데이트 가능한 구조로 관리
- 나에게 맞는 혜택 추천
- 어려운 금융 정보를 쉬운 언어로 설명

## 2. 어떤 문제를 해결하는가

사용자 피드백에서 반복된 요구는 세 가지였습니다.

- 혜택 정보 자동 업데이트 또는 최신화
- 나이, 소득, 직업, 주거 상태에 따른 맞춤 추천
- 여러 기관에 흩어진 금융·정책 정보를 한곳에서 확인

이번 정비는 새 기능을 늘리는 것이 아니라 중복 홈 화면, 하드코딩된 정책 조건, 혼재된 라우팅을 줄여 운영 가능한 MVP 구조를 만드는 데 집중합니다.

## 3. 핵심 기능

- **맞춤 혜택 추천**: `UserProfile`을 만들고 `match_policies(profile, policies)`로 정책 후보를 추천합니다.
- **정책 데이터 관리**: 정책 조건은 Python UI 코드가 아니라 `data/policies.json`에서 관리합니다.
- **청년 혜택 업데이트**: 온통청년 API 동기화, 캐시 상태, 데이터 신선도, fallback 여부를 확인합니다.
- **쉬운 금융 설명**: 사회초년생이 이해하기 어려운 정책·금융 용어를 쉬운 언어로 설명합니다.

## 4. 시스템 구조

```text
app.py
pages/
services/
    models.py
    policy_loader.py
    recommendation.py
data/
    policies.json
finfit_youth/
    client.py
    cache_store.py
    service.py
tests/
docs/
```

추천 흐름:

```text
사용자 입력
  -> UserProfile
  -> load_policies()
  -> match_policies(profile, policies)
  -> 추천 결과 렌더링
```

운영 상태 흐름:

```text
온통청년 API
  -> YouthDataService
  -> CacheStore
  -> 마지막 동기화 / 데이터 신선도 / API 상태 / fallback 표시
```

## 5. 데모

현재 데모 GIF는 추후 `assets/`에 추가합니다.

목표 데모:

- API 정상 연결 화면
- API 실패 후 캐시 fallback 화면
- 조건 입력 후 맞춤 혜택 추천 화면

## 6. 테스트

```bash
pytest
```

검증 항목:

- 정책 JSON 필수 필드 검증
- 추천 로직 조건별 검증
- API 실패와 캐시 fallback 검증
- 기존 `YouthDataService` 캐시/상세 조회 흐름 검증

GitHub Actions의 `.github/workflows/test.yml`에서 push/PR 시 pytest를 실행합니다.

## 7. 기술 스택

- Python
- Streamlit
- Pandas
- Plotly
- SQLite
- Requests
- pytest

## 실행 방법

```bash
pip install -r requirements.txt
streamlit run app.py
```

일부 외부 API 기능은 Streamlit secrets 또는 환경 변수에 API 키가 필요합니다.

## Non-Goals

FinFit v1은 다음을 제공하지 않습니다.

- 금융상품 가입 대행
- 법적 자격 판정
- 투자 자문
- 금융기관 대체 서비스
- 커뮤니티, 랭킹, 친구, SNS 기능
- Flutter 전환
- DB 교체

정책 추천은 공식 출처 확인을 돕는 1차 후보 추천입니다.
