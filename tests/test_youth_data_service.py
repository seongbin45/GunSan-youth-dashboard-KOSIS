from finfit_youth.service import YouthDataService


class FakeClient:
    def __init__(self):
        self.calls = []

    def get(self, path, params=None):
        self.calls.append((path, params or {}))
        if str((params or {}).get("pageType")) == "2":
            return {"id": params.get("id") or params.get("bizId") or params.get("plcyNo"), "title": "상세"}
        return {
            "result": [
                {"id": "A1", "title": "청년 취업 지원", "summary": "취업 준비", "region": "서울"},
                {"id": "A2", "title": "청년 주거 지원", "summary": "월세 지원", "region": "부산"},
            ]
        }


class FakeStore:
    def __init__(self):
        self.db = {}

    def set(self, key, payload):
        self.db[key] = payload

    def get(self, key, max_age_seconds=None):
        return self.db.get(key)

    def age_seconds(self, key):
        return 0 if key in self.db else None


def test_list_cache_and_filter():
    service = YouthDataService(client=FakeClient(), store=FakeStore())
    out = service.get_list("policy", query="주거", page=1, size=10)
    assert out["total"] == 1
    assert out["items"][0]["id"] == "A2"


def test_detail_realtime_then_cache():
    client = FakeClient()
    store = FakeStore()
    service = YouthDataService(client=client, store=store)

    first = service.get_detail("policy", "A1")
    second = service.get_detail("policy", "A1")

    assert first["id"] == "A1"
    assert second["id"] == "A1"
    detail_calls = [c for c in client.calls if str(c[1].get("pageType")) == "2"]
    assert len(detail_calls) == 1
