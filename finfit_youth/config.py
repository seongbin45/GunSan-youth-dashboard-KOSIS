import os
from pathlib import Path

try:
    import streamlit as st
except Exception:
    st = None

# Project root (parent of finfit_youth/)
_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_dotenv_into_environ() -> list[str]:
    """
    Load KEY=VALUE lines from .env / .env.local into os.environ (no extra deps).
    Does not override variables already set in the process environment.
    Returns list of files successfully loaded.
    """
    loaded: list[str] = []
    candidates = [
        _PROJECT_ROOT / ".env",
        _PROJECT_ROOT / ".env.local",
        Path.cwd() / ".env",
        Path.cwd() / ".env.local",
    ]
    seen: set[Path] = set()
    for path in candidates:
        try:
            path = path.resolve()
        except Exception:
            continue
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        try:
            text = path.read_text(encoding="utf-8-sig")
        except Exception:
            continue
        for raw in text.splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            if not key:
                continue
            # do not clobber real process env
            if os.environ.get(key, "").strip():
                continue
            os.environ[key] = val
        loaded.append(str(path))
    return loaded


def _load_secrets_toml_into_environ() -> list[str]:
    """
    Parse .streamlit/secrets.toml for CLI (outside `streamlit run`).
    Supports flat KEY = "value" and simple [kosis] API_KEY / KOSIS_API_KEY.
    Does not override existing process env.
    """
    loaded: list[str] = []
    path = _PROJECT_ROOT / ".streamlit" / "secrets.toml"
    if not path.is_file():
        return loaded
    try:
        text = path.read_text(encoding="utf-8-sig")
    except Exception:
        return loaded

    # Only promote API-like keys (avoid multiline private_key / gcp fields)
    _ALLOW_PREFIXES = (
        "KOSIS_",
        "YOUTH_",
        "GOOGLE_",
        "GROQ_",
        "OPENAI_",
        "ANTHROPIC_",
        "MISTRAL_",
        "GUNSAN_",
    )
    section = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().strip('"').strip("'").lower()
            continue
        # skip unfinished multiline / non simple assignments
        if "=" not in line or line.count('"') % 2 == 1:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if not key or not val or "BEGIN PRIVATE" in val or "\\n" in val and "PRIVATE" in val:
            continue
        # Map nested [kosis] keys
        env_key = key
        if section == "kosis":
            if key.upper() in ("API_KEY", "KEY", "KOSIS_API_KEY"):
                env_key = "KOSIS_API_KEY"
            elif not key.upper().startswith("KOSIS_"):
                env_key = f"KOSIS_{key.upper()}"
        if not env_key.upper().startswith(_ALLOW_PREFIXES) and env_key != "KOSIS_API_KEY":
            # allow exact common names without prefix only for kosis mapping above
            if section != "kosis":
                continue
        if os.environ.get(env_key, "").strip():
            continue
        os.environ[env_key] = val
    loaded.append(str(path))
    return loaded


_DOTENV_LOADED = _load_dotenv_into_environ()
_SECRETS_TOML_LOADED = _load_secrets_toml_into_environ()


def _secret(name: str, default: str = "") -> str:
    """
    Resolve secret in order:
      1) Streamlit secrets (flat key, or nested [kosis] / [secrets])
      2) process environment / .env / secrets.toml (CLI fallback)
      3) default
    """
    # 1) Streamlit secrets (when running under streamlit)
    if st is not None:
        try:
            sec = st.secrets
            if name in sec:
                v = sec[name]
                if v is not None and str(v).strip() != "":
                    return str(v).strip()
            # nested [kosis] API_KEY or KOSIS_API_KEY
            if "kosis" in sec:
                block = sec["kosis"]
                for alt in (name, name.replace("KOSIS_", ""), "API_KEY", "api_key"):
                    try:
                        v = block[alt] if alt in block else None
                    except Exception:
                        v = None
                    if v is not None and str(v).strip() != "":
                        return str(v).strip()
            if "secrets" in sec and name in sec["secrets"]:
                v = sec["secrets"][name]
                if v is not None and str(v).strip() != "":
                    return str(v).strip()
        except Exception:
            pass

    # 2) environment (.env + secrets.toml already merged when possible)
    v = os.getenv(name)
    if v is not None and str(v).strip() != "":
        return str(v).strip()

    # aliases
    if name == "KOSIS_API_KEY":
        for alt in ("KOSIS_OPENAPI_KEY", "KOSIS_KEY"):
            v = os.getenv(alt)
            if v is not None and str(v).strip() != "":
                return str(v).strip()

    return default


def secret_status(name: str = "KOSIS_API_KEY") -> dict:
    """UI/CLI helper: is the key set, and where it came from (never returns the raw key)."""
    source = "missing"
    present = False

    if st is not None:
        try:
            sec = st.secrets
            if name in sec and str(sec.get(name) or "").strip():
                source, present = "streamlit_secrets", True
            elif "kosis" in sec:
                block = sec["kosis"]
                for alt in (name, "API_KEY", "api_key"):
                    if alt in block and str(block[alt] or "").strip():
                        source, present = "streamlit_secrets[kosis]", True
                        break
        except Exception:
            pass

    if not present:
        if os.getenv(name, "").strip() or (
            name == "KOSIS_API_KEY"
            and (os.getenv("KOSIS_OPENAPI_KEY", "").strip() or os.getenv("KOSIS_KEY", "").strip())
        ):
            if any("secrets.toml" in f for f in _SECRETS_TOML_LOADED):
                # env may have been filled from secrets.toml file parse
                source, present = "secrets.toml_file", True
            else:
                source, present = "environment_or_dotenv", True

    value = _secret(name, "")
    # refine source if we only got value via _secret after file load
    if value and source == "missing":
        source = "secrets.toml_file" if _SECRETS_TOML_LOADED else "environment_or_dotenv"

    masked = ""
    if value:
        if len(value) <= 8:
            masked = value[:2] + "…" + value[-2:]
        else:
            masked = value[:4] + "…" + value[-4:]

    return {
        "name": name,
        "configured": bool(value),
        "source": source if value else "missing",
        "masked": masked,
        "dotenv_files": list(_DOTENV_LOADED),
        "secrets_toml_loaded": list(_SECRETS_TOML_LOADED),
        "secrets_example": str(_PROJECT_ROOT / ".streamlit" / "secrets.toml.example"),
        "env_example": str(_PROJECT_ROOT / ".env.example"),
    }


def _safe_base_url(v: str) -> str:
    v = (v or "").strip()
    if (not v) or (":8080" in v) or (not v.startswith("https://")):
        return "https://www.youthcenter.go.kr"
    return v.rstrip("/")


def _safe_url(v: str, default: str) -> str:
    v = (v or "").strip()
    if not v:
        v = default
    if v.startswith("http://"):
        v = "https://" + v[len("http://"):]
    if ":8080" in v:
        v = v.replace(":8080", "")
    return v.rstrip("/")


def _safe_path(v: str, default: str) -> str:
    v = (v or "").strip()
    if not v:
        return default
    if not v.startswith("/"):
        v = "/" + v
    return v


YOUTH_API_BASE_URL = _safe_base_url(_secret("YOUTH_API_BASE_URL", "https://www.youthcenter.go.kr"))

# Separate keys by source
YOUTH_API_KEY = _secret("YOUTH_API_KEY", "")
YOUTH_CONTENT_API_KEY = _secret("YOUTH_CONTENT_API_KEY", "")
YOUTH_CENTER_API_KEY = _secret("YOUTH_CENTER_API_KEY", "")

YOUTH_POLICY_URL = _safe_url(
    _secret("YOUTH_POLICY_URL", "https://www.youthcenter.go.kr/go/ythip/getPlcy"),
    "https://www.youthcenter.go.kr/go/ythip/getPlcy",
)
YOUTH_CONTENT_URL = _safe_url(
    _secret("YOUTH_CONTENT_URL", "https://www.youthcenter.go.kr/go/ythip/getContent"),
    "https://www.youthcenter.go.kr/go/ythip/getContent",
)
YOUTH_CENTER_URL = _safe_url(
    _secret("YOUTH_CENTER_URL", "https://www.youthcenter.go.kr/go/ythip/getSpace"),
    "https://www.youthcenter.go.kr/go/ythip/getSpace",
)

YOUTH_POLICY_DEFAULT_PAGE_SIZE = int(_secret("YOUTH_POLICY_DEFAULT_PAGE_SIZE", "100"))
YOUTH_POLICY_DEFAULT_RTN_TYPE = _secret("YOUTH_POLICY_DEFAULT_RTN_TYPE", "json")
YOUTH_CONTENT_DEFAULT_PAGE_SIZE = int(_secret("YOUTH_CONTENT_DEFAULT_PAGE_SIZE", "100"))
YOUTH_CONTENT_DEFAULT_RTN_TYPE = _secret("YOUTH_CONTENT_DEFAULT_RTN_TYPE", "json")
YOUTH_CENTER_DEFAULT_PAGE_SIZE = int(_secret("YOUTH_CENTER_DEFAULT_PAGE_SIZE", "100"))
YOUTH_CENTER_DEFAULT_RTN_TYPE = _secret("YOUTH_CENTER_DEFAULT_RTN_TYPE", "json")

# Legacy paths kept only for policy/content compatibility
YOUTH_POLICY_LIST_PATH = _safe_path(_secret("YOUTH_POLICY_LIST_PATH", "/opi/youthPlcyList.do"), "/opi/youthPlcyList.do")
YOUTH_CONTENT_LIST_PATH = _safe_path(_secret("YOUTH_CONTENT_LIST_PATH", "/opi/youthContentList.do"), "/opi/youthContentList.do")
YOUTH_POLICY_DETAIL_PATH = _safe_path(_secret("YOUTH_POLICY_DETAIL_PATH", "/opi/youthPlcyDtl.do"), "/opi/youthPlcyDtl.do")
YOUTH_CONTENT_DETAIL_PATH = _safe_path(_secret("YOUTH_CONTENT_DETAIL_PATH", "/opi/youthContentDtl.do"), "/opi/youthContentDtl.do")

CACHE_DB_PATH = _secret("YOUTH_CACHE_DB_PATH", "youth_cache.db")
CACHE_TTL_SECONDS = int(_secret("YOUTH_CACHE_TTL_SECONDS", "1800"))
DETAIL_TTL_SECONDS = int(_secret("YOUTH_DETAIL_TTL_SECONDS", "120"))

# KOSIS (군산시청년통계) — see Technical_document .../4_&_5_pages.txt
KOSIS_API_KEY = _secret("KOSIS_API_KEY", "")
KOSIS_API_BASE = _secret("KOSIS_API_BASE", "https://kosis.kr/openapi")
GUNSAN_STATS_DB_PATH = _secret("GUNSAN_STATS_DB_PATH", "gunsan_youth_data.db")
# Core table refresh TTL (seconds). Default 7 days. 0 = manual only.
GUNSAN_STATS_SYNC_TTL_SECONDS = int(_secret("GUNSAN_STATS_SYNC_TTL_SECONDS", str(7 * 24 * 3600)))

HTTP_TIMEOUT_SECONDS = float(_secret("YOUTH_API_TIMEOUT_SECONDS", "8"))
HTTP_MAX_RETRIES = int(_secret("YOUTH_API_MAX_RETRIES", "3"))
HTTP_BACKOFF_SECONDS = float(_secret("YOUTH_API_BACKOFF_SECONDS", "0.7"))
HTTP_RATE_LIMIT_PER_MINUTE = int(_secret("YOUTH_API_RATE_LIMIT_PER_MINUTE", "120"))

YOUTH_CODEBOOK_XLSX_PATH = _secret("YOUTH_CODEBOOK_XLSX_PATH", "")

# ── Shared budget / savings levels (centralized to remove duplication across pages) ──
LEVELS = {
    1:  {"name":"여가 최우선",    "save":0.05, "fix":0.45, "leisure":0.50, "color":"#4CAF50",
         "tips":["친구 모임, 취미 생활 충분히 즐기기","남는 돈은 CMA통장에 자동이체","소비 패턴 파악하는 시기"]},
    2:  {"name":"여가 중심",      "save":0.10, "fix":0.50, "leisure":0.40, "color":"#8BC34A",
         "tips":["여가비 예산 세우고 그 안에서 즐기기","적금 1개 만들어 자동이체 설정","지출 앱으로 소비 기록 시작"]},
    3:  {"name":"균형 여가형",    "save":0.15, "fix":0.55, "leisure":0.30, "color":"#CDDC39",
         "tips":["청년희망적금 / 청년도약계좌 가입 검토","외식 횟수 주 2회로 줄이기","구독 서비스 점검 및 정리"]},
    4:  {"name":"생활 균형형",    "save":0.20, "fix":0.55, "leisure":0.25, "color":"#FFEB3B",
         "tips":["비상금 3개월치 먼저 만들기","교통비 할인카드 발급","식비는 식료품 위주로 전환"]},
    5:  {"name":"균형형",         "save":0.25, "fix":0.55, "leisure":0.20, "color":"#FFC107",
         "tips":["청년도약계좌 (월 최대 70만원) 적극 활용","점심은 도시락 또는 구내식당","여가는 무료·저가 문화활동 위주"]},
    6:  {"name":"저축 균형형",    "save":0.30, "fix":0.55, "leisure":0.15, "color":"#FF9800",
         "tips":["주거비 절감 방안 검토 (청년월세지원 신청)","카드 대신 체크카드 사용","월말 잔액 추가 저축 습관 만들기"]},
    7:  {"name":"저축 집중형",    "save":0.40, "fix":0.50, "leisure":0.10, "color":"#FF5722",
         "tips":["고정비 항목 전면 재검토","통신비 알뜰폰으로 전환 (월 1~2만원대)","여가는 한 달에 1~2회만"]},
    8:  {"name":"고강도 저축",    "save":0.50, "fix":0.45, "leisure":0.05, "color":"#F44336",
         "tips":["월세 부담 낮추기 (룸메이트 또는 고시원 검토)","식비는 직접 요리 위주","절약 챌린지 SNS 커뮤니티 참여"]},
    9:  {"name":"극한 저축",      "save":0.65, "fix":0.35, "leisure":0.00, "color":"#E91E63",
         "tips":["단기 목돈 마련 목표 설정 (1년 내)","불필요한 모든 지출 제거","정부 지원 식품바우처 등 최대한 활용"]},
    10: {"name":"생존형 저축",    "save":0.80, "fix":0.20, "leisure":0.00, "color":"#9C27B0",
         "tips":["생활비 최저 생계비 수준으로 제한","무료 와이파이·공공시설 적극 이용","번아웃 주의: 1~2개월 단기 목표로 운영"]},
}

def calculate_budget(income: int, level: int):
    """Shared budget allocation logic to eliminate duplication across pages."""
    if level not in LEVELS:
        level = 5
    lv = LEVELS[level]
    save_amt = int(income * lv["save"])
    fix_amt = int(income * lv["fix"])
    leisure_amt = int(income * lv["leisure"])
    return {
        "save": save_amt,
        "fix": fix_amt,
        "leisure": leisure_amt,
        "level_info": lv,
    }


def get_gspread_client():
    """Centralized Google Sheets client (with caching) to remove duplication."""
    import streamlit as st
    import json
    import gspread
    @st.cache_resource(ttl=3300)
    def _get():
        json_string = st.secrets["gspread_json"]
        credentials = json.loads(json_string)
        return gspread.service_account_from_dict(credentials)
    return _get()


def render_feedback_form(key_prefix: str = "feedback"):
    """Shared feedback form UI + submission logic.

    key_prefix: unique per page to avoid StreamlitDuplicateElementId when
    the same form is rendered more than once in a multipage app session.
    """
    import streamlit as st
    from datetime import datetime

    st.markdown("### 💌 서비스 의견 공유")
    st.markdown(
        "**저희는 더 나은 경험을 드리기 위해 꾸준히 준비 중입니다.** "
        "소중한 의견을 들려주시면 서비스 개선에 큰 도움이 됩니다!"
    )
    user_feedback = st.text_area(
        "자유롭게 적어주세요 👇",
        placeholder="예: 이런 기능이 추가되면 좋겠어요 / 이 부분이 사용하기 조금 불편해요",
        key=f"{key_prefix}_text_area",
    )
    if st.button("피드백 남기기", use_container_width=True, key=f"{key_prefix}_submit_btn"):
        if not user_feedback.strip():
            st.warning("내용을 입력한 후 버튼을 눌러주세요! ⚠️")
        else:
            try:
                gc = get_gspread_client()
                sh = gc.open_by_key(st.secrets["spreadsheet_id"])
                worksheet = sh.get_worksheet(0)
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                worksheet.append_row([current_time, user_feedback])
                st.balloons()
                st.success(
                    "🎉 소중한 피드백이 성공적으로 전달되었어요! 앞으로도 많은 기대 부탁드려요! 🙏"
                )
            except Exception as e:
                st.error(f"데이터 저장 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요: {e}")


def match_benefits(age: int, income_level: str, has_house: bool, selected_keywords: list) -> dict:
    """
    Backward-compatible entry used by page 4 / legacy callers.
    Delegates to benefits_matcher (온통청년 policy cache) — single source of truth with AI tools.
    """
    from .benefits_matcher import match_benefits_for_ui

    return match_benefits_for_ui(
        age=age,
        income_level=income_level,
        has_house=has_house,
        selected_keywords=list(selected_keywords or []),
        limit=15,
    )


def inject_finfit_theme():
    """Centralized FinFit light theme CSS. Call this at the top of any page that uses .asset-card, .feature-card, .stat-pill, .benefit-banner etc.
    (Onboarding.py uses its own dark immersive styles instead.)
    """
    st.markdown("""
<style>
/* ============================================
   FinFit Unified Theme + Common CSS
   Dark #111111 full page background + consistent card system (TSX prototype fidelity)
   Used by all pages for 일관성 (consistency)
   ============================================ */

:root {
    --finfit-primary: #6366F1;
    --finfit-primary-dark: #5855EB;
    --finfit-gradient: linear-gradient(135deg, #6366F1 0%, #8B5CF6 60%, #A78BFA 100%);
    --finfit-bg: #111111;
    --finfit-card: #1a1a1a;
    --finfit-text: #f0f0f0;
    --finfit-muted: #888888;
    --finfit-border: #333333;
}

/* Base - entire page background dark (full page as requested) */
.main, .stApp, body, .block-container, .stMain, .stApp > div {
    background-color: #111111 !important;
}

h1, h2, h3, h4, h5 {
    color: var(--finfit-text) !important;
}

/* Header (used on Home and main landing) */
.header-container {
    text-align: center;
    margin-bottom: 1.5rem;
    padding-top: 1rem;
}
.header-title {
    font-size: 2.4em;
    font-weight: 800;
    color: var(--finfit-text);
    letter-spacing: -0.02em;
}
.header-subtitle {
    font-size: 1.05em;
    color: var(--finfit-muted);
    font-weight: 500;
    margin-top: 0.25rem;
}

/* Standard feature / content cards */
.feature-card {
    background: var(--finfit-card);
    border-radius: 20px;
    padding: 1.75rem 1.5rem;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    border: 1px solid var(--finfit-border);
    transition: all 0.2s ease;
}
.feature-card:hover {
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.10);
    transform: translateY(-2px);
}

/* Colored left border variants */
.card-yellow  { border-left: 6px solid #F4D160; }
.card-mint    { border-left: 6px solid #95E1D3; }
.card-peach   { border-left: 6px solid #FF9E7D; }
.card-blue    { border-left: 6px solid #579BB1; }
.card-pastel-fog { border-left: 6px solid #C1D3DB; }

/* Asset / Summary Card (big gradient one) */
.asset-card {
    background: var(--finfit-gradient);
    color: white;
    border-radius: 20px;
    padding: 20px 22px;
    box-shadow: 0 8px 32px rgba(99, 102, 241, 0.35);
    position: relative;
    overflow: hidden;
}
.asset-card .sub-metric {
    background: rgba(255,255,255, 0.18);
    border-radius: 14px;
    padding: 10px 14px;
}

/* Progress bars */
.finfit-progress {
    height: 10px;
    background: #333333;
    border-radius: 999px;
    overflow: hidden;
}
.finfit-progress > div {
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s ease;
}
.progress-green { background: linear-gradient(90deg, #10B981, #34D399); }
.progress-yellow { background: linear-gradient(90deg, #F59E0B, #FBBF24); }
.progress-red   { background: linear-gradient(90deg, #EF4444, #F97316); }
.progress-indigo { background: var(--finfit-gradient); }

/* Stat pills / small cards */
.stat-pill {
    background: #1a1a1a;
    border-radius: 16px;
    padding: 12px 14px;
    border: 1px solid var(--finfit-border);
}
.stat-pill .label { font-size: 10px; color: #888888; }
.stat-pill .value { font-size: 18px; font-weight: 700; color: var(--finfit-text); }

/* Quick action / grid tiles */
.action-tile {
    background: #222222;
    border-radius: 16px;
    padding: 14px 10px;
    text-align: center;
    transition: all 0.2s;
}
.action-tile:hover { filter: brightness(0.97); }
.action-tile .icon { font-size: 22px; }
.action-tile .label { font-size: 11px; font-weight: 700; color: #6366F1; }
.action-tile .sub { font-size: 10px; color: #888888; }

/* Benefits / NEW banner */
.benefit-banner {
    background: var(--finfit-gradient);
    color: white;
    border-radius: 20px;
    padding: 16px 18px;
    box-shadow: 0 6px 24px rgba(99, 102, 241, 0.35);
}

/* Transaction / list rows */
.tx-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: #1a1a1a;
    border-bottom: 1px solid #333333;
}
.tx-icon {
    width: 36px; height: 36px; border-radius: 999px;
    background: #222222; display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
}

/* Buttons - global nicer look */
div[data-testid="stButton"] > button {
    width: 100%;
    font-size: 0.95em !important;
    font-weight: 600 !important;
    padding: 10px 18px !important;
    height: auto !important;
    min-height: 42px !important;
    border-radius: 12px !important;
    transition: all 0.2s ease !important;
    border: 1px solid transparent !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: var(--finfit-primary) !important;
    color: white !important;
}

/* Badges */
.badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 999px;
}
.badge-new { background: #6366F1; color: white; }
.badge-dday { background: #FEF3C7; color: #92400E; }

/* Search / input polish */
.stTextInput > div > div > input {
    border-radius: 14px !important;
    border: 1px solid var(--finfit-border) !important;
    background: #1a1a1a !important;
    color: #f0f0f0 !important;
}

/* Consistent dark cards and text for all pages */
.stSubheader, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
    color: #f0f0f0 !important;
}
.stInfo, .stSuccess, .stWarning {
    background: #1a1a1a !important;
    color: #f0f0f0 !important;
    border: 1px solid #333 !important;
}

/* Hide Streamlit default top chrome for clean prototype top */
.stApp > header, 
.stApp > div[data-testid="stToolbar"], 
.stApp > div[data-testid="stDecoration"] { 
    display: none !important; 
}

/* Fix weird empty space at top of st.tabs content across the app */
.stTabs,
.stTabs > div,
.stTabs [data-baseweb="tab-panel"],
.stTabs [data-baseweb="tab-panel"] > div,
.stTabs [data-baseweb="tab-panel"] > div:first-child,
.stTabs [data-baseweb="tab-panel"] .stMarkdown,
.stTabs [data-baseweb="tab-panel"] .stMarkdown > div {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
.stTabs [data-baseweb="tab-list"] {
    margin-bottom: 2px !important;
    margin-top: 0 !important;
    padding-top: 0 !important;
}
.stTabs {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
/* Also reduce general container top space */
.main .block-container {
    padding-top: 0 !important;
}
/* Tighten radio and first widgets after headers */
.stRadio {
    margin-top: 0 !important;
}
.stRadio > div {
    margin-top: 0 !important;
}

/* Stat cards (for summary numbers on dashboard) */
.stat-card {
    background: #1a1a1a;
    border: 1px solid var(--finfit-border);
    border-radius: 16px;
    padding: 16px 14px;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.stat-card .stat-label { font-size: 11px; color: #888888; margin-bottom: 2px; }
.stat-card .stat-number { font-size: 22px; font-weight: 800; color: var(--finfit-text); line-height: 1.1; margin: 4px 0; }

/* Footer / small text */
.footer {
    text-align: center;
    padding: 1.5rem 0;
    color: #9CA3AF;
    font-size: 0.85em;
}

/* Responsive */
@media (max-width: 768px) {
    .header-title { font-size: 1.9em; }
    .feature-card { padding: 1.25rem 1rem; min-height: auto; }
}
</style>
""", unsafe_allow_html=True)
