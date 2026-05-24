from __future__ import annotations

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
    YOUTH_CONTENT_API_KEY,
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
        p = (path or "").strip()
        if p.startswith("http://"):
            p = "https://" + p[len("http://"):]
        if ":8080" in p:
            p = p.replace(":8080", "")

        if p.startswith("https://"):
            endpoint = p
        else:
            base = (self.base_url or "").strip()
            if (not base) or (":8080" in base) or (not base.startswith("https://")):
                base = "https://www.youthcenter.go.kr"
            if not p.startswith("/"):
                p = "/" + p
            endpoint = f"{base}{p}"

        query = dict(params or {})

        is_content = "/go/ythip/getContent" in endpoint
        is_policy = "/go/ythip/getPlcy" in endpoint

        if is_content:
            content_key = (YOUTH_CONTENT_API_KEY or "").strip()
            if not content_key:
                raise YouthApiError("YOUTH_CONTENT_API_KEY is not set")
            query.setdefault("apiKeyNm", content_key)
            query.pop("openApiVlak", None)
        elif is_policy:
            if not self.api_key:
                raise YouthApiError("YOUTH_API_KEY is not set")
            query.setdefault("apiKeyNm", self.api_key)
            query.pop("openApiVlak", None)
        else:
            if not self.api_key:
                raise YouthApiError("YOUTH_API_KEY is not set")
            query.setdefault("openApiVlak", self.api_key)

        attempt = 0
        last_error: Exception | None = None

        while attempt < HTTP_MAX_RETRIES:
            attempt += 1
            self.rate_limiter.acquire()
            try:
                response = requests.get(endpoint, params=query, timeout=HTTP_TIMEOUT_SECONDS)

                if response.status_code == 403:
                    key_mode = "apiKeyNm" if (is_content or is_policy) else "openApiVlak"
                    raise YouthApiError(f"request failed: 403 (endpoint={endpoint}, auth_param={key_mode})")
                if response.status_code >= 500:
                    raise YouthApiError(f"upstream {response.status_code} (endpoint={endpoint})")
                if response.status_code >= 400:
                    raise YouthApiError(f"request failed: {response.status_code} (endpoint={endpoint})")

                return self._parse_response(response)

            except Exception as exc:
                last_error = exc
                if attempt >= HTTP_MAX_RETRIES:
                    break
                time.sleep(HTTP_BACKOFF_SECONDS * attempt)

        raise YouthApiError(str(last_error) if last_error else "unknown API error")
