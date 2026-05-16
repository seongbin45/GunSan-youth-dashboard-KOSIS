from __future__ import annotations
raise RuntimeError("CLIENT_PY_NEW_VERSION_LOADED")

import json
import time
from typing import Any
from xml.etree import ElementTree

import requests

from .config import (
    HTTP_BACKOFF_SECONDS,
    HTTP_MAX_RETRIES,
    HTTP_RATE_LIMIT_PER_MINUTE,
    HTTP_TIMEOUT_SECONDS,
    YOUTH_API_BASE_URL,
    YOUTH_API_KEY,
)
from .rate_limit import SimpleRateLimiter


class YouthApiError(Exception):
    pass


class YouthApiClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key if api_key is not None else YOUTH_API_KEY

        raw_base = (base_url or YOUTH_API_BASE_URL or "").strip()
        if (not raw_base) or (":8080" in raw_base) or (not raw_base.startswith("https://")):
            raw_base = "https://www.youthcenter.go.kr"
        self.base_url = raw_base.rstrip("/")

        self.rate_limiter = SimpleRateLimiter(HTTP_RATE_LIMIT_PER_MINUTE)

    def _parse_response(self, response: requests.Response) -> Any:
        text = response.text.strip()
        if not text:
            return {}

        content_type = response.headers.get("content-type", "")
        if "json" in content_type:
            return response.json()

        if text.startswith("{") or text.startswith("["):
            return json.loads(text)

        root = ElementTree.fromstring(text)
        return self._xml_to_dict(root)

    def _xml_to_dict(self, element: ElementTree.Element) -> Any:
        children = list(element)
        if not children:
            return element.text or ""

        result: dict[str, Any] = {}
        for child in children:
            value = self._xml_to_dict(child)
            if child.tag in result:
                existing = result[child.tag]
                if isinstance(existing, list):
                    existing.append(value)
                else:
                    result[child.tag] = [existing, value]
            else:
                result[child.tag] = value
        return result

    def get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if not self.api_key:
            raise YouthApiError("YOUTH_API_KEY is not set")

        base = (self.base_url or "").strip()
        if (not base) or (":8080" in base) or (not base.startswith("https://")):
            base = "https://www.youthcenter.go.kr"

        p = (path or "").strip()
        if p.startswith("http://") or p.startswith("https://"):
            p = "/opi/youthPlcyList.do"
        if not p.startswith("/"):
            p = "/" + p
        if p == "/":
            p = "/opi/youthPlcyList.do"

        endpoint = f"{base}{p}"
        print(f"DEBUG endpoint={endpoint}")

        query = dict(params or {})
        query["openApiVlak"] = self.api_key

        attempt = 0
        last_error: Exception | None = None

        while attempt < HTTP_MAX_RETRIES:
            attempt += 1
            self.rate_limiter.acquire()
            try:
                response = requests.get(endpoint, params=query, timeout=HTTP_TIMEOUT_SECONDS)
                if response.status_code >= 500:
                    raise YouthApiError(f"upstream {response.status_code}")
                if response.status_code >= 400:
                    raise YouthApiError(f"request failed: {response.status_code}")
                return self._parse_response(response)
            except Exception as exc:
                last_error = exc
                if attempt >= HTTP_MAX_RETRIES:
                    break
                time.sleep(HTTP_BACKOFF_SECONDS * attempt)

        raise YouthApiError(str(last_error) if last_error else "unknown API error")
