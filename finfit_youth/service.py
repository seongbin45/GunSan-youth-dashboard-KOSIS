from __future__ import annotations

import logging
from typing import Any

from .cache_store import CacheStore
from .client import YouthApiClient, YouthApiError
from .config import (
    CACHE_DB_PATH,
    CACHE_TTL_SECONDS,
    DETAIL_TTL_SECONDS,
    YOUTH_CONTENT_DEFAULT_PAGE_SIZE,
    YOUTH_CONTENT_DEFAULT_RTN_TYPE,
    YOUTH_CONTENT_DETAIL_PATH,
    YOUTH_CONTENT_LIST_PATH,
    YOUTH_CONTENT_URL,
    YOUTH_POLICY_DEFAULT_PAGE_SIZE,
    YOUTH_POLICY_DEFAULT_RTN_TYPE,
    YOUTH_POLICY_URL,
    YOUTH_SPACE_DETAIL_PATH,
    YOUTH_SPACE_LIST_PATH,
)

logger = logging.getLogger(__name__)

SOURCE_MAP = {
    "policy": {"list": YOUTH_POLICY_URL, "detail": YOUTH_POLICY_URL},
    "space": {"list": YOUTH_SPACE_LIST_PATH, "detail": YOUTH_SPACE_DETAIL_PATH},
    "content": {"list": YOUTH_CONTENT_URL, "detail": YOUTH_CONTENT_URL},
}


class YouthDataService:
    def __init__(self, client: YouthApiClient | None = None, store: CacheStore | None = None):
        self.client = client or YouthApiClient()
        self.store = store or CacheStore(CACHE_DB_PATH)

    def _normalize_item(self, source: str, item: dict[str, Any]) -> dict[str, Any]:
        if source == "content":
            uid = str(item.get("pstSn") or item.get("id") or item.get("idx") or "")
            title = str(item.get("pstTtl") or item.get("title") or item.get("name") or "")
            summary = str(item.get("pstWholCn") or item.get("summary") or item.get("desc") or "")
            region = str(item.get("pstSeCd") or item.get("region") or item.get("rgnNm") or "")
            return {
                "id": uid,
                "source": source,
                "title": title,
                "summary": summary,
                "region": region,
                "raw": item,
            }

        if source == "policy":
            uid = str(item.get("plcyNo") or item.get("id") or item.get("idx") or "")
            title = str(item.get("plcyNm") or item.get("title") or item.get("name") or "")
            summary = str(item.get("plcyExplnCn") or item.get("summary") or item.get("desc") or "")
            region = str(item.get("zipCd") or item.get("region") or item.get("rgnNm") or "")
            return {
                "id": uid,
                "source": source,
                "title": title,
                "summary": summary,
                "region": region,
                "raw": item,
            }

        uid = str(item.get("bizId") or item.get("id") or item.get("idx") or "")
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
            for key in ("result", "data", "list", "youthPolicyList", "youthContentList", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]
                if isinstance(value, dict):
                    nested = self._extract_list(value)
                    if nested:
                        return nested
        return []

    def _policy_list_params(self) -> dict[str, Any]:
        return {
            "pageNum": 1,
            "pageSize": YOUTH_POLICY_DEFAULT_PAGE_SIZE,
            "pageType": "1",
            "rtnType": YOUTH_POLICY_DEFAULT_RTN_TYPE,
        }

    def _policy_detail_params(self, plcy_no: str) -> dict[str, Any]:
        return {
            "pageType": "2",
            "plcyNo": plcy_no,
            "rtnType": YOUTH_POLICY_DEFAULT_RTN_TYPE,
        }

    def _content_list_params(self, pst_se_cd: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {
            "pageNum": 1,
            "pageSize": YOUTH_CONTENT_DEFAULT_PAGE_SIZE,
            "pageType": "1",
            "rtnType": YOUTH_CONTENT_DEFAULT_RTN_TYPE,
        }
        if pst_se_cd:
            params["pstSeCd"] = pst_se_cd
        return params

    def _content_detail_params(self, pst_sn: str) -> dict[str, Any]:
        return {
            "pageType": "2",
            "pstSn": pst_sn,
            "rtnType": YOUTH_CONTENT_DEFAULT_RTN_TYPE,
        }

    def sync_source(self, source: str) -> dict[str, Any]:
        endpoint = SOURCE_MAP[source]["list"]
        if not endpoint:
            raise YouthApiError(f"{source} list endpoint is not configured")

        if source == "policy":
            payload = self.client.get(endpoint, params=self._policy_list_params())
        elif source == "content":
            payload = self.client.get(endpoint, params=self._content_list_params())
        else:
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

        if source == "policy":
            payload = self.client.get(endpoint, params=self._policy_detail_params(item_id))
        elif source == "content":
            payload = self.client.get(endpoint, params=self._content_detail_params(item_id))
        else:
            payload = self.client.get(endpoint, params={"id": item_id, "bizId": item_id})

        detail = payload if isinstance(payload, dict) else {"raw": payload}
        detail["id"] = item_id
        detail["source"] = source
        self.store.set(cache_key, detail)
        return detail
