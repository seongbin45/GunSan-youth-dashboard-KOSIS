"""
KOSIS Open API client.

Pipeline documented in:
  Technical_document/What we talked about with AI/pages/4_&_5_pages.txt

1) statisticsList.do — list folders/tables under parentListId
2) Param/statisticsParameterData.do — fetch numeric cells for a tblId
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import requests

from .config import HTTP_TIMEOUT_SECONDS, KOSIS_API_BASE, KOSIS_API_KEY

logger = logging.getLogger(__name__)


class KosisApiError(Exception):
    pass


class KosisClient:
    def __init__(self, api_key: str | None = None, base: str | None = None, timeout: float | None = None):
        self.api_key = (api_key if api_key is not None else KOSIS_API_KEY) or ""
        self.base = (base or KOSIS_API_BASE).rstrip("/")
        self.timeout = float(timeout if timeout is not None else HTTP_TIMEOUT_SECONDS or 15)

    def _require_key(self) -> None:
        if not self.api_key.strip():
            raise KosisApiError("KOSIS_API_KEY is not set (Streamlit secrets or env)")

    def fetch_list(self, parent_list_id: str, vw_cd: str = "MT_ZTITLE") -> list[dict[str, Any]]:
        """statisticsList.do — catalog under parentListId (e.g. V_3_214_005)."""
        self._require_key()
        url = f"{self.base}/statisticsList.do"
        params = {
            "method": "getList",
            "apiKey": self.api_key,
            "vwCd": vw_cd,
            "parentListId": parent_list_id,
            "format": "json",
            "jsonVD": "Y",
        }
        return self._get_json_list(url, params, label=f"list:{parent_list_id}")

    def fetch_parameter_data(
        self,
        org_id: str,
        tbl_id: str,
        *,
        itm_id: str = "T001 ",
        obj_l1: str = "A01 A02 A03",
        obj_l2: str = "B02 B03",
        prd_se: str = "F",
        new_est_prd_cnt: str = "3",
        extra: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:
        """
        Param/statisticsParameterData.do — numeric data for one table.

        Defaults match the successful GunSan youth population/housing pulls
        documented in 4_&_5_pages.txt (orgId=712, prdSe=F, ...).
        """
        self._require_key()
        url = f"{self.base}/Param/statisticsParameterData.do"
        params: dict[str, Any] = {
            "method": "getList",
            "apiKey": self.api_key,
            "itmId": itm_id,
            "objL1": obj_l1,
            "objL2": obj_l2,
            "objL3": "",
            "objL4": "",
            "objL5": "",
            "objL6": "",
            "objL7": "",
            "objL8": "",
            "format": "json",
            "jsonVD": "Y",
            "prdSe": prd_se,
            "newEstPrdCnt": str(new_est_prd_cnt),
            "orgId": str(org_id),
            "tblId": tbl_id,
        }
        if extra:
            params.update(extra)
        return self._get_json_list(url, params, label=f"data:{tbl_id}")

    def _get_json_list(self, url: str, params: dict[str, Any], label: str = "") -> list[dict[str, Any]]:
        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as e:
            raise KosisApiError(f"network error ({label}): {e}") from e

        if resp.status_code >= 400:
            raise KosisApiError(f"HTTP {resp.status_code} ({label})")

        try:
            data = resp.json()
        except Exception as e:
            raise KosisApiError(f"invalid JSON ({label}): {e}") from e

        if isinstance(data, dict):
            if data.get("err") or data.get("errMsg"):
                raise KosisApiError(
                    f"KOSIS error ({label}): {data.get('errMsg') or data.get('err')}"
                )
            # single object → list
            if any(k in data for k in ("DT", "C1_NM", "TBL_ID", "LIST_ID", "listId")):
                return [data]
            raise KosisApiError(f"unexpected dict payload ({label}): keys={list(data.keys())[:8]}")

        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]

        raise KosisApiError(f"unexpected payload type ({label}): {type(data)}")
