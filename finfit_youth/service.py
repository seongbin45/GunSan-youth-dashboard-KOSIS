from __future__ import annotations

import logging
from typing import Any

from .cache_store import CacheStore
from .client import YouthApiClient, YouthApiError
from .config import (
    CACHE_DB_PATH,
    CACHE_TTL_SECONDS,
    DETAIL_TTL_SECONDS,
    YOUTH_CONTENT_DETAIL_PATH,
    YOUTH_CONTENT_LIST_PATH,
    YOUTH_POLICY_DETAIL_PATH,
    YOUTH_POLICY_LIST_PATH,
    YOUTH_SPACE_DETAIL_PATH,
    YOUTH_SPACE_LIST_PATH,
)

logger = logging.getLogger(__name__)

SOURCE_MAP = {
    "policy": {"list": YOUTH_POLICY_LIST_PATH, "detail": YOUTH_POLICY_DETAIL_PATH},
    "space": {"list": YOUTH_SPACE_LIST_PATH, "detail": YOUTH_SPACE_DETAIL_PATH},
    "content": {"list": YOUTH_CONTENT_LIST_PATH, "detail": YOUTH_CONTENT_DETAIL_PATH},
}


class YouthDataService:
    def __init__(self, client: YouthApiClient | None = None, store: CacheStore | None = None):
        self.client = client or YouthApiClient()
        self.store = store or CacheStore(CACHE_DB_PATH)

    def _normalize_item(self, source: str, item: dict[str, Any]) -> dict[str, Any]:
        uid = str(item.get("bizId") or item.get("id") or item.get("idx") or item.get("polyBizSjnm") or "")
        title = str(item.get("polyBizSjnm") or item.get("title") or item.get("name") or "")
        summary = str(item.get("polyItcnCn") or item.get("summary") or item.get("desc") or "")
        region = str(item.get("zipCd") or item.get("region") or item.get("rgnNm") or "")
        return {
            "id": uid,
            "source": source,
            "title": title,
            "summary": summary,
            "region": region,
            "raw": item,
        }

    def _extract_list(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [x for x in payload if isinstance(x, dict)]
        if isinstance(payload, dict):
            for key in ("result", "data", "list", "youthPolicyList", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]
                if isinstance(value, dict):
                    nested = self._extract_list(value)
                    if nested:
                        return nested
        return []

    def sync_source(self, source: str) -> dict[str, Any]:
        endpoint = SOURCE_MAP[source]["list"]
        if not endpoint:
            raise YouthApiError(f"{source} list endpoint is not configured")

        payload = self.client.get(endpoint, params={"pageIndex": 1, "display": 100})
        items = self._extract_list(payload)
        normalized = [self._normalize_item(source, x) for x in items]

        self.store.set(f"snapshot:{source}", normalized)
        self.store.set(f"latest_sync:{source}", {"count": len(normalized)})
        return {"source": source, "count": len(normalized)}

    def sync_all(self) -> dict[str, Any]:
        results = []
        for source in ("policy", "space", "content"):
            try:
                results.append(self.sync_source(source))
            except Exception as exc:
                logger.exception("sync failed for %s", source)
                results.append({"source": source, "error": str(exc)})
        return {"results": results}

    def get_list(self, source: str, query: str = "", page: int = 1, size: int = 10) -> dict[str, Any]:
        key = f"snapshot:{source}"
        snapshot = self.store.get(key)

        if snapshot is None:
            try:
                self.sync_source(source)
                snapshot = self.store.get(key) or []
            except Exception:
                snapshot = self.store.get(key, max_age_seconds=None) or []

        age = self.store.age_seconds(key)
        if age is not None and age > CACHE_TTL_SECONDS:
            try:
                self.sync_source(source)
                snapshot = self.store.get(key) or snapshot
            except Exception:
                pass

        rows = snapshot if isinstance(snapshot, list) else []
        if query:
            q = query.lower()
            rows = [r for r in rows if q in r.get("title", "").lower() or q in r.get("summary", "").lower()]

        total = len(rows)
        start = max((page - 1) * size, 0)
        end = start + size
        return {"source": source, "items": rows[start:end], "total": total, "page": page, "size": size}

    def get_detail(self, source: str, item_id: str) -> dict[str, Any]:
        cache_key = f"detail:{source}:{item_id}"
        cached = self.store.get(cache_key, max_age_seconds=DETAIL_TTL_SECONDS)
        if cached is not None:
            return cached

        endpoint = SOURCE_MAP[source]["detail"]
        if not endpoint:
            raise YouthApiError(f"{source} detail endpoint is not configured")

        payload = self.client.get(endpoint, params={"id": item_id, "bizId": item_id})
        detail = payload if isinstance(payload, dict) else {"raw": payload}
        detail["id"] = item_id
        detail["source"] = source
        self.store.set(cache_key, detail)
        return detail
