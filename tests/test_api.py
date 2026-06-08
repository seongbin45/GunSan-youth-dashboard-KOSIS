from finfit_youth.service import YouthDataService


class FailingClient:
    def get(self, path, params=None):
        raise RuntimeError("upstream unavailable")


class MemoryStore:
    def __init__(self):
        self.db = {}
        self.ages = {}

    def set(self, key, payload):
        self.db[key] = payload
        self.ages[key] = 0

    def get(self, key, max_age_seconds=None):
        return self.db.get(key)

    def age_seconds(self, key):
        return self.ages.get(key)


def test_get_list_uses_cache_when_api_fails():
    store = MemoryStore()
    store.set(
        "snapshot:policy",
        [{"id": "A1", "source": "policy", "title": "청년 주거", "summary": "월세 지원", "region": "전국"}],
    )
    store.ages["snapshot:policy"] = 999999
    service = YouthDataService(client=FailingClient(), store=store)

    result = service.get_list("policy", query="주거")

    assert result["fallback_used"] is True
    assert result["total"] == 1


def test_status_reports_cache_metadata():
    store = MemoryStore()
    store.set("snapshot:policy", [{"id": "A1"}])
    store.set("latest_sync:policy", {"count": 1, "synced_at": "2026-06-08T13:42:00+00:00"})
    service = YouthDataService(client=FailingClient(), store=store)

    status = service.get_source_status("policy")

    assert status["item_count"] == 1
    assert status["cache_status"] == "정상"
    assert status["last_synced_at"] == "2026-06-08T13:42:00+00:00"
