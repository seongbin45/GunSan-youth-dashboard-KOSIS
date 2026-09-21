"""
Smoke-import every Streamlit entry page with a lightweight st mock.

Catches IndentationError, missing imports, NameError at module load.
Does NOT fully render UI or hit live APIs (secrets/gspread may soft-fail).
"""
from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class _Session(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError as e:
            raise AttributeError(k) from e

    def __setattr__(self, k, v):
        self[k] = v


def _make_st() -> MagicMock:
    st = MagicMock()
    st.session_state = _Session()
    # common defaults pages expect
    st.session_state.income = 2_000_000
    st.session_state.level = 5
    st.session_state.chat_history = []
    st.session_state.expenses = []

    def form(*_a, **_k):
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=ctx)
        ctx.__exit__ = MagicMock(return_value=False)
        return ctx

    st.form = form
    st.sidebar = MagicMock()
    st.sidebar.__enter__ = MagicMock(return_value=st.sidebar)
    st.sidebar.__exit__ = MagicMock(return_value=False)
    def columns(spec=None, **_k):
        if isinstance(spec, int):
            n = max(1, spec)
        elif isinstance(spec, (list, tuple)):
            n = max(1, len(spec))
        else:
            n = 2
        return [MagicMock() for _ in range(n)]

    st.columns = columns
    def tabs(spec=None, **_k):
        if isinstance(spec, int):
            n = max(1, spec)
        elif isinstance(spec, (list, tuple)):
            n = max(1, len(spec))
        else:
            n = 2
        return [MagicMock() for _ in range(n)]

    st.tabs = tabs
    st.container = form
    st.expander = form
    st.empty = MagicMock(return_value=MagicMock())
    st.spinner = form
    st.chat_message = form
    st.fragment = lambda f: f

    def _cache_decorator(*_a, **_k):
        def wrap(f):
            return f

        # support both @st.cache_data and @st.cache_data()
        if _a and callable(_a[0]) and not _k:
            return _a[0]
        return wrap

    st.cache_data = _cache_decorator
    st.cache_resource = _cache_decorator
    st.secrets = MagicMock()
    st.secrets.get = MagicMock(return_value=None)
    # allow `key in st.secrets` patterns
    st.secrets.__contains__ = MagicMock(return_value=False)
    st.secrets.__getitem__ = MagicMock(side_effect=KeyError("no secrets in smoke"))
    st.query_params = {}
    st.switch_page = MagicMock()
    st.rerun = MagicMock()
    st.stop = MagicMock(side_effect=SystemExit("st.stop"))
    # widgets return neutral values
    st.number_input = MagicMock(return_value=2_000_000)
    st.slider = MagicMock(return_value=5)

    def selectbox(_label=None, options=None, index=0, **_k):
        if options is None:
            return None
        opts = list(options)
        if not opts:
            return None
        try:
            i = int(index)
        except Exception:
            i = 0
        if i < 0 or i >= len(opts):
            i = 0
        return opts[i]

    def radio(_label=None, options=None, index=0, **_k):
        return selectbox(_label, options, index, **_k)

    st.selectbox = selectbox
    st.radio = radio
    st.multiselect = MagicMock(side_effect=lambda _l=None, options=None, default=None, **_k: list(default or []))
    st.text_input = MagicMock(return_value="")
    st.text_area = MagicMock(return_value="")
    st.button = MagicMock(return_value=False)
    st.form_submit_button = MagicMock(return_value=False)
    st.checkbox = MagicMock(return_value=False)
    st.file_uploader = MagicMock(return_value=None)
    st.chat_input = MagicMock(return_value=None)  # no chat turn on import
    st.dataframe = MagicMock()
    st.plotly_chart = MagicMock()
    st.metric = MagicMock()
    st.progress = MagicMock()
    return st


def load_page(path: Path, st_mod) -> tuple[str, str | None]:
    name = f"smoke_page_{path.stem}"
    # isolate streamlit per load
    sys.modules["streamlit"] = st_mod
    # some pages import plotly / pandas fine
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return "ok", None
    except SystemExit as e:
        # st.stop() used intentionally
        return "ok_stop", str(e)
    except Exception:
        return "fail", traceback.format_exc()


def main() -> int:
    pages = [ROOT / "app.py"] + sorted((ROOT / "pages").glob("*.py"))
    st = _make_st()
    results = []
    for p in pages:
        # fresh session each page
        st = _make_st()
        status, err = load_page(p, st)
        results.append((p.relative_to(ROOT), status, err))
        mark = "OK" if status.startswith("ok") else "FAIL"
        print(f"{mark:4} {p.relative_to(ROOT)} ({status})")
        if err and status == "fail":
            print(err[:2000])
            print("---")

    fails = [r for r in results if r[1] == "fail"]
    print(f"\nsummary: {len(results) - len(fails)}/{len(results)} loadable, fails={len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
