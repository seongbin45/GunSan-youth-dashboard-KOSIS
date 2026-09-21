"""page_router: deep-link slugs + 404 resolution (no Streamlit UI)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.page_router import (
    PAGE_ROUTES,
    resolve_page_path,
    NOT_FOUND_PAGE,
)


def test_known_slugs_resolve():
    assert resolve_page_path("ai") == "pages/2_AI와_대화하기.py"
    assert resolve_page_path("benefit") == resolve_page_path("benefits")
    assert resolve_page_path("ledger") == "pages/Household_Ledger.py"
    assert resolve_page_path("stats") == "pages/6_군산시 청년 데이터.py"
    assert resolve_page_path("onboarding") == "pages/Onboarding.py"


def test_case_insensitive_alias():
    assert resolve_page_path("AI") == resolve_page_path("ai")
    assert resolve_page_path("Household_Ledger") is not None


def test_unknown_slug_returns_none():
    assert resolve_page_path("this-does-not-exist-xyz") is None
    assert resolve_page_path("") is None
    assert resolve_page_path(None) is None


def test_404_slug_points_to_not_found_page():
    assert resolve_page_path("404") == NOT_FOUND_PAGE
    assert resolve_page_path("not_found") == NOT_FOUND_PAGE
    assert Path(ROOT, NOT_FOUND_PAGE).is_file()


def test_route_targets_exist_on_disk():
    missing = []
    for slug, path in PAGE_ROUTES.items():
        if not Path(ROOT, path).is_file():
            missing.append((slug, path))
    assert missing == [], f"route files missing: {missing}"
