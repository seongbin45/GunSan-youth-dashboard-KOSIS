"""YouthDataService unit tests with fakes matching real client.get(url, params) shape."""
from __future__ import annotations

from finfit_youth.service import YouthDataService


class FakeClient:
    """Mirrors YouthApiClient.get(path, params) usage in YouthDataService."""

    def __init__(self):
        self.calls: list[tuple[str, dict]] = []

    def get(self, path, params=None):
        params = dict(params or {})
        self.calls.append((str(path), params))

        # Detail requests use pageType "2" (policy/content) — not a "/detail" URL path
        if str(params.get("pageType")) == "2":
            item_id = (
                params.get("plcyNo")
                or params.get("pstSn")
                or params.get("plcSn")
                or params.get("id")
                or ""
            )
            return {
                "plcyNo": item_id,
                "title": "상세",
                "plcyNm": "상세 정책",
            }

        # List (pageType 1 or default)
        return {
            "result": [
                {
                    "id": "A1",
                    "title": "청년 취업 지원",
                    "summary": "취업 준비",
                    "region": "서울",
                },
                {
                    "id": "A2",
                    "title": "청년 주거 지원",
                    "summary": "월세 지원",
                    "region": "부산",
                },
            ]
        }


class FakeStore:
    def __init__(self):
        self.db = {}

    def set(self, key, payload):
        self.db[key] = payload

    def get(self, key, max_age_seconds=None):
        # TTL ignored in fake; presence alone simulates cache hit
        return self.db.get(key)

    def age_seconds(self, key):
        return 0 if key in self.db else None


def _detail_calls(client: FakeClient) -> list:
    return [c for c in client.calls if str(c[1].get("pageType")) == "2"]


def test_list_cache_and_filter():
    service = YouthDataService(client=FakeClient(), store=FakeStore())
    out = service.get_list("policy", query="주거", page=1, size=10)
    assert out["total"] == 1
    assert out["items"][0]["id"] == "A2"
    assert "주거" in out["items"][0]["title"]


def test_detail_realtime_then_cache():
    """First detail hits network once; second serves DETAIL_TTL cache."""
    client = FakeClient()
    store = FakeStore()
    service = YouthDataService(client=client, store=store)

    first = service.get_detail("policy", "A1")
    second = service.get_detail("policy", "A1")

    assert first["id"] == "A1"
    assert second["id"] == "A1"
    assert first.get("source") == "policy"

    dcalls = _detail_calls(client)
    assert len(dcalls) == 1, f"expected 1 detail network call, got {len(dcalls)}: {dcalls}"
    assert dcalls[0][1].get("plcyNo") == "A1"
    assert str(dcalls[0][1].get("pageType")) == "2"

    # Cache key written
    assert store.get("detail:policy:A1") is not None


def test_detail_different_ids_two_calls():
    client = FakeClient()
    service = YouthDataService(client=client, store=FakeStore())
    service.get_detail("policy", "A1")
    service.get_detail("policy", "A2")
    assert len(_detail_calls(client)) == 2
