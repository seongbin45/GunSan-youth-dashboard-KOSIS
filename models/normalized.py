from pydantic import BaseModel, Field
from typing import Any, Dict, Literal


class NormalizedItem(BaseModel):
    """_normalize_item()이 반환하는 정규화 구조를 보호하는 P0 데이터 계약"""
    id: str
    source: Literal["policy", "center", "content"]
    title: str
    summary: str
    region: str = ""
    raw: Dict[str, Any] = Field(default_factory=dict)
