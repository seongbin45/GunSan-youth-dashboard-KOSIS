"""One-shot cross-verification for recent multipage / H5 / 404 work."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from finfit_youth.agent import FinFitAgent, UserState
from finfit_youth.page_router import NOT_FOUND_PAGE, PAGE_ROUTES, resolve_page_path
from finfit_youth.user_context import build_user_context, income_range_to_monthly_won


def main() -> int:
    fails: list[str] = []

    print("=== 1. ROUTE FILES ON DISK ===")
    for slug, path in sorted(PAGE_ROUTES.items()):
        ok = (ROOT / path).is_file()
        print(f"  {'OK' if ok else 'MISS'} {slug:28} -> {path}")
        if not ok:
            fails.append(f"missing route file {slug} -> {path}")
    if not (ROOT / NOT_FOUND_PAGE).is_file():
        fails.append("NOT_FOUND_PAGE missing")

    print("=== 2. RESOLVE ===")
    cases = [
        ("ai", True),
        ("AI", True),
        ("benefit", True),
        ("benefits", True),
        ("stats", True),
        ("ledger", True),
        ("404", True),
        ("nope-xyz", False),
        ("", False),
        (None, False),
    ]
    for slug, expect_ok in cases:
        got = resolve_page_path(slug)
        ok = (got is not None) == expect_ok
        print(f"  resolve({slug!r}) -> {got!r}  {'OK' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"resolve {slug!r}")

    print("=== 3. H5 CONF MATRIX ===")
    c1 = build_user_context({"monthly_income_range": "under50"})
    if c1.monthly_income != 400_000 or c1.sources.get("monthly_income") != "onboarding_range_mid":
        fails.append(f"range only: {c1.monthly_income} {c1.sources}")
    print("  range only", c1.monthly_income, c1.sources.get("monthly_income"), "OK" if c1.monthly_income == 400_000 else "FAIL")

    c2 = build_user_context({"monthly_income_range": "under50", "income": 2_000_000})
    if c2.monthly_income != 400_000:
        fails.append(f"range+ledger_def should be 400k got {c2.monthly_income}")
    print("  range+ledger_def", c2.monthly_income, c2.sources.get("monthly_income"))

    c3 = build_user_context(
        {"monthly_income_range": "under50", "income": 2_000_000},
        prior=UserState(monthly_income=2_500_000),
    )
    if c3.monthly_income != 2_500_000 or c3.sources.get("monthly_income") != "agent":
        fails.append(f"agent should win: {c3.monthly_income} {c3.sources}")
    print("  range+agent", c3.monthly_income, c3.sources.get("monthly_income"))

    c4 = build_user_context(
        {
            "monthly_income_range": "over200",
            "income": 2_000_000,
            "income_touched": True,
        }
    )
    if c4.monthly_income != 2_000_000 or c4.sources.get("monthly_income") != "ledger":
        fails.append(f"touched ledger: {c4.monthly_income} {c4.sources}")
    print("  range+touched", c4.monthly_income, c4.sources.get("monthly_income"))

    # H1 still: agent vs ledger default alone
    c5 = build_user_context({"income": 2_000_000}, prior=UserState(monthly_income=2_500_000))
    if c5.monthly_income != 2_500_000:
        fails.append(f"H1 regression: {c5.monthly_income}")
    print("  H1 agent vs ledger_def", c5.monthly_income, c5.sources.get("monthly_income"))

    print("=== 4. SAVINGS TOOL ===")
    a = FinFitAgent(user_id="xv")
    a.state = UserState()
    a.clear_turn_scratch()
    a.sync_from_session({"monthly_income_range": "100to150"})
    args = a.savings_tool_args(None, "")
    if args["income"] != 1_250_000:
        fails.append(f"savings mid {args}")
    ass = [x for x in a.assumptions if x.get("field") == "monthly_income"]
    if not ass or ass[0].get("source") != "onboarding_range_mid":
        fails.append(f"missing assumption {ass}")
    print("  savings mid", args["income"], ass[0].get("source") if ass else None)

    a2 = FinFitAgent(user_id="xv2")
    a2.state = UserState()
    a2.clear_turn_scratch()
    a2.sync_from_session({"monthly_income_range": "under50"})
    args2 = a2.savings_tool_args(None, "월급 250만원인데 저축 어떻게")
    if args2["income"] != 2_500_000:
        fails.append(f"msg should be 250만 got {args2['income']}")
    print("  msg beats mid", args2["income"])

    print("=== 5. MIDPOINTS ===")
    expected = {
        "under50": 400_000,
        "50to100": 750_000,
        "100to150": 1_250_000,
        "150to200": 1_750_000,
        "over200": 2_500_000,
        "50~100만원": 750_000,
    }
    for k, v in expected.items():
        got = income_range_to_monthly_won(k)
        ok = got == v
        print(f"  {k} -> {got} {'OK' if ok else 'FAIL expected '+str(v)}")
        if not ok:
            fails.append(f"mid {k}")

    print("=== 6. PAGE6 / 7 / 99 / LEDGER MARKERS ===")
    p6 = (ROOT / "pages" / "6_군산시 청년 데이터.py").read_text(encoding="utf-8")
    for marker in [
        "_has_kosis_key",
        "ensure_fresh_core",
        "st.stop 없음",
        "로컬 DB",
        "_sync_fail_message",
    ]:
        ok = marker in p6
        print(f"  page6 {marker!r}: {'OK' if ok else 'MISS'}")
        if not ok:
            fails.append(f"page6 missing {marker}")

    p7 = (ROOT / "pages" / "7_청년혜택업데이트.py").read_text(encoding="utf-8")
    for marker in ["any_key", "no st.stop()", "youth_cache"]:
        ok = marker in p7
        print(f"  page7 {marker!r}: {'OK' if ok else 'MISS'}")
        if not ok:
            fails.append(f"page7 missing {marker}")

    app = (ROOT / "app.py").read_text(encoding="utf-8")
    home = (ROOT / "pages" / "0_Home.py").read_text(encoding="utf-8")
    for name, text in [("app", app), ("0_Home", home)]:
        ok = "handle_query_page_param" in text and "st.stop()" in text
        print(f"  {name} query+stop: {'OK' if ok else 'FAIL'}")
        if not ok:
            fails.append(f"{name} router wiring")

    freeze = (ROOT / "Technical_document" / "ACCURACY_FREEZE.md").read_text(encoding="utf-8")
    for marker in ["H5 — 적용됨", "404 UX", "page6 KOSIS", "onboarding_range_mid"]:
        ok = marker in freeze
        print(f"  freeze {marker!r}: {'OK' if ok else 'MISS'}")
        if not ok:
            fails.append(f"freeze missing {marker}")

    print("=== RESULT ===")
    if fails:
        print("FAILS:")
        for f in fails:
            print(" -", f)
        return 1
    print("ALL CROSS-CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
