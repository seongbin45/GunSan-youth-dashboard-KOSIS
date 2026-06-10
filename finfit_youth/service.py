from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Callable

# 파일 맨 위 import 부분에 추가
from pydantic import ValidationError
from models.normalized import NormalizedItem

logger = logging.getLogger(__name__)
# ---------------------------

from .cache_store import CacheStore
from .client import YouthApiClient, YouthApiError
from .config import (
    CACHE_DB_PATH,
    CACHE_TTL_SECONDS,
    DETAIL_TTL_SECONDS,
    YOUTH_CENTER_DEFAULT_PAGE_SIZE,
    YOUTH_CENTER_DEFAULT_RTN_TYPE,
    YOUTH_CENTER_URL,
    YOUTH_CONTENT_DEFAULT_PAGE_SIZE,
    YOUTH_CONTENT_DEFAULT_RTN_TYPE,
    YOUTH_CONTENT_URL,
    YOUTH_POLICY_DEFAULT_PAGE_SIZE,
    YOUTH_POLICY_DEFAULT_RTN_TYPE,
    YOUTH_POLICY_URL,
)

logger = logging.getLogger(__name__)

SOURCE_MAP = {
    "policy": {"list": YOUTH_POLICY_URL, "detail": YOUTH_POLICY_URL},
    "center": {"list": YOUTH_CENTER_URL, "detail": YOUTH_CENTER_URL},
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
            region = str(item.get("pstSeNm") or item.get("pstSeCd") or item.get("region") or item.get("rgnNm") or "")
            normalized = {
                "id": uid,
                "source": source,
                "title": title,
                "summary": summary,
                "region": region,
                "raw": item,
            }
        elif source == "policy":
            uid = str(item.get("plcyNo") or item.get("id") or item.get("idx") or "")
            title = str(item.get("plcyNm") or item.get("title") or item.get("name") or "")
            summary = str(item.get("plcyExplnCn") or item.get("summary") or item.get("desc") or "")
            region = str(item.get("zipCd") or item.get("region") or item.get("rgnNm") or "")
            normalized = {
                "id": uid,
                "source": source,
                "title": title,
                "summary": summary,
                "region": region,
                "raw": item,
            }
        elif source == "center":
            uid = str(item.get("cntrSn") or item.get("plcSn") or item.get("id") or "")
            title = str(item.get("cntrNm") or item.get("title") or item.get("name") or "")
            addr = str(item.get("cntrAddr") or "").strip()
            daddr = str(item.get("cntrDaddr") or "").strip()
            summary = (addr + " " + daddr).strip() or str(item.get("summary") or item.get("desc") or "")
            region = str(
                item.get("stdgCtpvCdNm")
                or item.get("stdgSggCdNm")
                or item.get("region")
                or item.get("rgnNm")
                or ""
            )
            normalized = {
                "id": uid,
                "source": source,
                "title": title,
                "summary": summary,
                "region": region,
                "raw": item,
            }
        else:
            uid = str(item.get("id") or item.get("idx") or "")
            title = str(item.get("title") or item.get("name") or "")
            summary = str(item.get("summary") or item.get("desc") or "")
            region = str(item.get("region") or item.get("rgnNm") or "")
            normalized = {
                "id": uid,
                "source": source,
                "title": title,
                "summary": summary,
                "region": region,
                "raw": item,
            }

        # ===================== P0: NormalizedItem 검증 =====================
        try:
            NormalizedItem.model_validate(normalized)
            return normalized  # dict 그대로 반환 (캐시 호환성 최고)
        except ValidationError as e:
            logger.warning(
                f"NormalizedItem validation failed for {source} item {normalized.get('id')}: {e}"
            )
            # 검증 실패 → skip (전체 sync가 죽지 않도록)
            # sync_source 루프에서 호출되므로 raise 대신 continue를 상위에서 처리하는 게 좋음
            raise  # 지금은 raise로 문제 즉시 발견
    
    
    def _extract_list(self, payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [x for x in payload if isinstance(x, dict)]
        if isinstance(payload, dict):
            for key in ("youthCenterList", "youthContentList", "youthPolicyList", "result", "data", "list", "items"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]
                if isinstance(value, dict):
                    nested = self._extract_list(value)
                    if nested:
                        return nested
        return []

    def _policy_list_params(self, page_num: int = 1) -> dict[str, Any]:
        return {
            "pageNum": page_num,
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

    def _content_list_params(self, page_num: int = 1, pst_se_cd: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {
            "pageNum": page_num,
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

    def _center_list_params(
        self,
        page_num: int = 1,
        ctpv_cd: str | None = None,
        sgg_cd: str | None = None,
        plc_type: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "pageNum": page_num,
            "pageSize": YOUTH_CENTER_DEFAULT_PAGE_SIZE,
            "pageType": 1,
            "rtnType": YOUTH_CENTER_DEFAULT_RTN_TYPE,
        }
        if ctpv_cd:
            params["ctpvCd"] = ctpv_cd
        if sgg_cd:
            params["sggCd"] = sgg_cd
        if plc_type:
            params["plcType"] = plc_type
        return params

    def _center_detail_attempts(self, plc_sn: str) -> list[dict[str, Any]]:
        return [
            {"pageType": 2, "plcSn": plc_sn, "rtnType": YOUTH_CENTER_DEFAULT_RTN_TYPE},
            {"plcSn": plc_sn, "rtnType": YOUTH_CENTER_DEFAULT_RTN_TYPE},
            {"pageType": 2, "plcSn": plc_sn},
        ]

    def _fetch_all_pages(
        self,
        endpoint: str,
        params_builder: Callable[[int], dict[str, Any]],
        max_pages: int = 200,
    ) -> list[dict[str, Any]]:
        all_items: list[dict[str, Any]] = []
        page_num = 1

        while page_num <= max_pages:
            params = params_builder(page_num)
            payload = self.client.get(endpoint, params=params)
            items = self._extract_list(payload)

            if not items:
                break

            all_items.extend(items)
            page_size = int(params.get("pageSize", 100))
            if len(items) < page_size:
                break

            page_num += 1

        return all_items

    def sync_source(self, source: str) -> dict[str, Any]:
        endpoint = SOURCE_MAP[source]["list"]
        if not endpoint:
            raise YouthApiError(f"{source} list endpoint is not configured")

        if source == "policy":
            items = self._fetch_all_pages(endpoint, lambda p: self._policy_list_params(p))
        elif source == "center":
            items = self._fetch_all_pages(endpoint, lambda p: self._center_list_params(p))
        elif source == "content":
            # Stabilization: avoid excessive paging when content endpoint is unstable
            payload = self.client.get(endpoint, params=self._content_list_params(1))
            items = self._extract_list(payload)
        else:
            raise YouthApiError(f"unsupported source: {source}")

        normalized = [self._normalize_item(source, x) for x in items]
        self.store.set(f"snapshot:{source}", normalized)
        self.store.set(
            f"latest_sync:{source}",
            {
                "count": len(normalized),
                "source": source,
                "synced_at": datetime.now(UTC).isoformat(timespec="seconds"),
            },
        )
        self.store.set(
            f"sync_status:{source}",
            {
                "api_status": "정상",
                "fallback_used": False,
                "last_error": "",
                "checked_at": datetime.now(UTC).isoformat(timespec="seconds"),
            },
        )
        return {"source": source, "count": len(normalized)}

    def record_source_error(self, source: str, error: str) -> None:
        self.store.set(
            f"sync_status:{source}",
            {
                "api_status": "오류",
                "fallback_used": True,
                "last_error": error,
                "checked_at": datetime.now(UTC).isoformat(timespec="seconds"),
            },
        )

    def get_source_status(self, source: str) -> dict[str, Any]:
        snapshot = self.store.get(f"snapshot:{source}", max_age_seconds=None)
        latest = self.store.get(f"latest_sync:{source}", max_age_seconds=None) or {}
        sync_status = self.store.get(f"sync_status:{source}", max_age_seconds=None) or {}
        cache_age = self.store.age_seconds(f"snapshot:{source}")
        item_count = len(snapshot) if isinstance(snapshot, list) else int(latest.get("count") or 0)

        cache_status = "정상" if snapshot else "없음"
        api_status = sync_status.get("api_status") or ("정상" if latest else "미확인")

        return {
            "source": source,
            "last_synced_at": latest.get("synced_at"),
            "cache_age_seconds": cache_age,
            "item_count": item_count,
            "api_status": api_status,
            "cache_status": cache_status,
            "fallback_used": bool(sync_status.get("fallback_used", False)),
            "last_error": sync_status.get("last_error", ""),
        }

    def sync_all(self) -> dict[str, Any]:
        results = []
        for source in ("policy", "center", "content"):
            try:
                results.append(self.sync_source(source))
            except Exception as exc:
                logger.exception("sync failed for %s", source)
                results.append({"source": source, "error": str(exc)})
        return {"results": results}

    def get_list(self, source: str, query: str = "", page: int = 1, size: int = 10) -> dict[str, Any]:
        key = f"snapshot:{source}"
        snapshot = self.store.get(key)
        fallback_used = False

        if snapshot is None:
            try:
                self.sync_source(source)
                snapshot = self.store.get(key) or []
            except Exception:
                fallback_used = True
                snapshot = self.store.get(key, max_age_seconds=None) or []
                self.record_source_error(source, "initial sync failed; using cache")

        age = self.store.age_seconds(key)
        if age is not None and age > CACHE_TTL_SECONDS:
            try:
                self.sync_source(source)
                snapshot = self.store.get(key) or snapshot
            except Exception:
                fallback_used = True
                self.record_source_error(source, "refresh failed; using cache")
                pass

        rows = snapshot if isinstance(snapshot, list) else []
        if query:
            q = query.lower()
            rows = [r for r in rows if q in r.get("title", "").lower() or q in r.get("summary", "").lower()]

        total = len(rows)
        start = max((page - 1) * size, 0)
        end = start + size
        return {
            "source": source,
            "items": rows[start:end],
            "total": total,
            "page": page,
            "size": size,
            "fallback_used": fallback_used,
            "cache_age_seconds": self.store.age_seconds(key),
        }

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
            attempts = [
                {"pageType": "2", "pstSn": item_id, "rtnType": YOUTH_CONTENT_DEFAULT_RTN_TYPE},
                {"pstSn": item_id, "rtnType": YOUTH_CONTENT_DEFAULT_RTN_TYPE},
                {"pageType": "2", "pstSn": item_id},
            ]

            payload = None
            last_exc: Exception | None = None

            for params in attempts:
                try:
                    payload = self.client.get(endpoint, params=params)
                    break
                except Exception as exc:
                    last_exc = exc

            if payload is None:
                snapshot = self.store.get("snapshot:content", max_age_seconds=None) or []
                for row in snapshot:
                    if str(row.get("id")) == str(item_id):
                        detail = dict(row.get("raw") or {})
                        detail["id"] = item_id
                        detail["source"] = source
                        detail["fallback"] = "snapshot_raw"
                        self.store.set(cache_key, detail)
                        return detail

                raise last_exc if last_exc else YouthApiError("content detail failed")

        elif source == "center":
            payload = None
            last_exc: Exception | None = None

            for params in self._center_detail_attempts(item_id):
                try:
                    payload = self.client.get(endpoint, params=params)
                    break
                except Exception as exc:
                    last_exc = exc

            if payload is None:
                snapshot = self.store.get("snapshot:center", max_age_seconds=None) or []
                for row in snapshot:
                    if str(row.get("id")) == str(item_id):
                        detail = dict(row.get("raw") or {})
                        detail["id"] = item_id
                        detail["source"] = source
                        detail["fallback"] = "snapshot_raw"
                        self.store.set(cache_key, detail)
                        return detail

                raise last_exc if last_exc else YouthApiError("center detail failed")

        else:
            raise YouthApiError(f"unsupported source: {source}")

        detail = payload if isinstance(payload, dict) else {"raw": payload}
        detail["id"] = item_id
        detail["source"] = source
        self.store.set(cache_key, detail)
        return detail
