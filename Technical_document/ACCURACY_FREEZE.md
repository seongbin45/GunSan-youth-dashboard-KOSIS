# FinFit 정확도 축 — 동결 기록

기준일: 2026-07-12 (이후 H1/H2/H3/H5/H6 · multipage · 404 보강)  
기준 테스트: `pytest tests` **244 passed** (2026-07-25 교차검증)  
근거 계획: 옵션 2 (reflect + 합성 가드 + 데모 정직) + golden/intent_routing/turn_log + **근거 고정 답변**

---

## 1. 동결하는 것 (당분간 손대지 않음)

의도적으로 **기능 변경·점수 튜닝·키워드 추가를 하지 않는** 범위.

| 축 | 모듈/경로 | 동결 이유 |
|----|-----------|-----------|
| 통계 단일 엔진 | `finfit_youth/gunsan_stats.py` | Main·page6·AI 동일; 취업 집계 검증됨 |
| 의도→도구 게이트 | `finfit_youth/intent_routing.py`, `tests/intent_golden.jsonl` | golden으로 잠김; 키워드 무한 추가는 감 코딩 |
| 근거 고정 답 | `finfit_youth/grounded_answer.py` + AI 페이지 분기 | 통계/저축/혜택/multi/clarify LLM 본문 스킵 |
| 질문 프로필 파싱 | `income_parse.py` (소득·나이·고용·주택) | 실로그 검증됨 |
| 생애주기 매칭 감점 | `benefits_matcher._life_stage_score_delta` | 신혼/창업 신호 기준; **군산 가점 강화 안 함** |
| 데모 정직 | `demo_mode.py` | 가정/추정 표기 정렬 |
| 턴 로그 스키마 | `turn_log.py` | 수동 교차검증용; 스키마 v1 유지 |
| 연구 루프 단순화 | `research_step` shallow/standard → 도구 후 synth | assess/prepare 연극 축소 |

**명시적 비목표 (동결 기간에도 하지 않음)**

- UI/캡션·단위 문구 polish  
- employment unit을 “명”으로 단정  
- 군산 우선 랭킹  
- CLARIFY 문장 미학  
- LLM 문장 생성 복원(정확 우선과 반대)  
- 키워드 golden 없이 라우팅 확장  

---

## 2. 허용하는 변경 (동결 중에도 OK)

| 종류 | 예 |
|------|-----|
| 버그픽스 | 크래시, 잘못된 도구 인수, 명확한 숫자 불일치 |
| 테스트 보강 | 기존 계약 깨지지 않게 회귀만 추가 |
| 의존성·보안 | 취약점 패치 |
| 문서 | 본 파일·README 사실 갱신 |
| 인프라 | 로컬 키 설정, KOSIS 동기화 운영 |

버그픽스 시: **관련 golden/e2e가 있으면 먼저 실패 케이스를 테스트로 고정**한 뒤 수정.

**Streamlit 페이지 (2026-07-23 교차검증)**  
- page6 `_stale` NameError 수정 · page7 BOM 제거  
- Household_Ledger: 시트 실패 시 **페이지 유지 + 세션 폴백** (시트 우선, 로컬-only 가정 금지)  
- 7_청년혜택업데이트: API 키 없어도 **페이지 유지 + 캐시 목록**; 동기화 실패 시 `st.stop` 제거  
- page6 KOSIS: 키 없어도 **페이지·DB 차트 유지**; 상단 키 배너 + 동기화 실패 fail-open (page7 패턴)  
- 404 UX: `finfit_youth/page_router.py` + `pages/99_페이지를_찾을_수_없음.py`  
  · `?page=` 미지 슬러그 → FinFit 테마 404 (홈 본문과 미겹침)  
  · Streamlit 자체 임의 URL 404는 플랫폼 제한(완전 대체 아님)  
- 재검증 (2026-07-25): `pytest tests` **244** · `scripts/_smoke_streamlit_pages.py` **13/13** · `scripts/_cross_verify_session.py` ALL PASSED

---

## 3. 다시 열 조건 (이 중 하나면 해당 축만 재오픈)

1. **실사용에서 반복되는 사실 오류**  
   예: 질문 소득/나이 무시, 통계 숫자 ≠ DB, multi에서 도구 결과와 다른 수치.
2. **회귀 테스트 실패**  
   `intent_golden` / `test_product_grounded_e2e` / employment 집계 테스트 red.
3. **제품 요구 변경**  
   예: 혜택 매칭을 공식 자격 API 수준으로 올리기로 결정.
4. **새 데이터 소스**  
   새 KOSIS 표·캐시 스키마 변경으로 gunsan_stats/matcher 계약이 깨질 때.

재오픈 시: **한 축만**, 차근차근, golden/e2e 갱신을 같은 PR/작업에 포함.

---

## 4. 동결 후 남는 백로그

| ID | 항목 | 비고 |
|----|------|------|
| B1 | 페이지↔에이전트 세션 동기화 | **아래 §7 조사 완료** — 수정은 재오픈 조건·한 축씩 |
| B2 | `agent.py` / AI 페이지 복잡도 분리 | 동작 0 변경 characterization |
| B3 | Streamlit UI E2E (선택) | 환경 비용 큼 |
| B4 | 혜택 매칭 품질 추가 튜닝 | 군산 가점 없이, 측정 가능한 골든 케이스 있을 때만 |

---

## 7. B1 조사: 페이지 ↔ 에이전트 동기화 구멍 (읽기 전용)

조사 방법: `user_context.build_user_context` / `sync_session_and_state`,  
`2_AI` 진입 시 `update_from_onboarding` + `sync_from_session`,  
온보딩·가계부·Savings·Main·혜택 페이지의 `session_state` 키.

### 7.1 데이터 흐름 (요약)

```
Onboarding → monthly_income_range, first_goal, user_level
Ledger/Savings/Main → income, level, expenses, savings_goals
혜택 page4 / Main 매칭 → benefit_profile, matched_*, ai_shared_benefits
        ↓
AI page load: FinFitAgent(session) → sync_from_session(session_state)
        ↓
UserState + last_user_context (+ agent JSON persist)
```

우선순위(필드별, 높은 conf 우선 — **현재 코드 기준**):

| 필드 | conf 스택 (높음 → 낮음) |
|------|-------------------------|
| `monthly_income` | `ledger` 실입력 **0.95** > `agent`/채팅 **0.65** > `onboarding_range_mid` **0.55** > `ledger_default`(미터치 200만) **0.45** |
| `income_level` | `benefit_profile` **1.0** > `onboarding_derived` **0.72** > `agent` **0.65** |
| `income_range` (라벨/id) | 온보딩 **0.95** (구간 문자열; 원 단위 중위와 별개) |
| age / 고용 / 주택 | `benefit_profile` **1.0** > `agent` prior |

### 7.2 구멍 목록 (심각도)

| ID | 심각도 | 구멍 | 근거 |
|----|--------|------|------|
| **H1** | **높음** | ~~가계부 기본 200만이 agent 소득을 덮어씀~~ → **수정**: 미터치 `income==2M` → conf **0.45** (`ledger_default`); 터치 시 **0.95** | 재현(수정 후): prior 2.5M + session 2M 미터치 → **2.5M / agent** |
| H2 | 중 | ~~에이전트 prior가 온보딩 derived를 이김~~ → **수정**: onboarding_derived conf **0.72** (> agent 0.65, < benefit 1.0) | conf 비교 로직 |
| H3 | 중 | 채팅 파싱 값이 agent에 남아 페이지 폼과 어긋날 수 있음 → **부분 완화**: AI 페이지 상단 **프로필 출처 한 줄** (`age←…`) | persist + sync |
| H4 | 중 | benefit_profile conf 1.0 최우선은 유지(설계) → 출처 캡션으로 **인지 가능하게** | by design |
| H5 | 낮 | ~~온보딩 range만 넣고 원 미연동~~ → **수정**: `income_range_to_monthly_won` 중위 추정 conf **0.55** (`onboarding_range_mid`); 저축 도구 assumption 표기 | agent 0.65·ledger 0.95 아래, ledger_default 0.45 위 |
| H6 | 낮 | ~~savings_level 미연동~~ → **수정**: UserState.savings_level + savings_tool_args가 session `level` 사용 | Savings/Main 슬라이더 |
| H7 | 낮 | `known_benefits`가 매칭 결과·에피소드로 누적 → 상태 문자열은 길어지나 **근거 고정 답에는 미포함** (현재 의도) | 정직에는 유리, 상태 UI 혼잡 |
| H8 | 정보 | page4와 Main 모두 `benefit_profile` 키 스키마 유사 (`income_ui`, `housing_ui`, …) — 대체로 정렬됨 | 양호 |
| H9 | 정보 | 통계 DB는 session이 아니라 파일 DB — 페이지↔AI 숫자 정합은 gunsan_stats로 이미 잠김 | B1 범위 밖·양호 |

### 7.3 수정 시 권장 순서

1. **H1 — 적용됨 (2026-07-12)**  
   - 미터치 기본값 `income==2_000_000` → conf **0.45** (`ledger_default`)  
   - Main/Savings에서 값 변경 시 `income_touched=True` → conf **0.95** (`ledger`)  
   - 테스트: `test_ledger_default_2m_does_not_stomp_agent_income`  
2. **H2 — 적용됨**: onboarding_derived conf **0.72**  
3. **H3–H4 — 부분 적용**: AI 페이지 상단 프로필 출처 caption (로직 conf 변경 없음)  
4. **H6 — 적용됨**: session `level` → UserState.savings_level → savings_tool_args  
   (추가) `plan()`이 `savings_level=5` 하드코딩하던 회귀 제거 → `None`으로 세션 강도 사용
5. **H5 — 적용됨 (2026-07-23)**  
   - `income_range_to_monthly_won` (under50→40만 … over200→250만 중위)  
   - conf **0.55** / source `onboarding_range_mid`  
   - 저축 도구: silent default 230만 대신 구간 중위 + assumption  
   - 테스트: `test_h5_*` in `tests/test_user_context.py`

**군산 가점·매칭 문구 튜닝은 이 목록과 무관 — 동결 유지.**  
**H7** (`known_benefits` 상태 문자열 혼잡)는 근거 고정 답에 미포함이 **현재 의도** — 동결 유지.

### 7.4 재현 스니펫 (H1)

```python
# --- 수정 전(참고): ledger를 0.95로 읽으면 agent 2.5M을 2M으로 덮어씀 ---
# session = {"income": 2000000}  # 미터치 기본값인데 conf 0.95 취급
# prior monthly_income=2_500_000 → 잘못 2_000_000

# --- 수정 후(현재): ledger_default 0.45 < agent 0.65 ---
prior = UserState(monthly_income=2_500_000)
session = {"income": 2_000_000}  # income_touched 없음
# build_user_context → monthly_income == 2_500_000, source == "agent"
# (+ H5) monthly_income_range="over200" 중위 2.5M conf 0.55 도 agent(0.65)에 짐
```

---

## 5. 빠른 검증 명령

```text
cd <project-root>
.venv\Scripts\python.exe -m pytest tests -q
```

수동 스모크 (선택, 앱 재시작 후):

1. `군산시 청년 취업 상황 어때?` → 근거 고정 · 33.7% 등 DB  
2. `월급 250만원인데 저축 어떻게 해야 해?` → income 250만  
3. `나 25살 취준생… 혜택` → 신혼 1위 아님 · income_level 가정/추정만  
4. `창업하려는 26살인데 혜택이랑 저축…` → multi · 도구 2 · 정리 적음  

---

## 6. 한 줄

**정확도 본게임(옵션 2 + 근거 고정 + 측정 인프라)은 동결.  
다음 코드 작업은 “다시 열 조건”에 해당하는 버그·요구가 있을 때만.**
