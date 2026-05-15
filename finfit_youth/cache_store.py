import json
import sqlite3
import time
from typing import Any


class CacheStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_items (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                )
                """
            )
            conn.commit()

    def set(self, key: str, payload: Any) -> None:
        now = int(time.time())
        serialized = json.dumps(payload, ensure_ascii=False)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO cache_items(cache_key, payload, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    payload=excluded.payload,
                    updated_at=excluded.updated_at
                """,
                (key, serialized, now),
            )
            conn.commit()

    def get(self, key: str, max_age_seconds: int | None = None) -> Any | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload, updated_at FROM cache_items WHERE cache_key=?",
                (key,),
            ).fetchone()
        if not row:
            return None

        payload, updated_at = row
        if max_age_seconds is not None and int(time.time()) - updated_at > max_age_seconds:
            return None

        return json.loads(payload)

    def age_seconds(self, key: str) -> int | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT updated_at FROM cache_items WHERE cache_key=?",
                (key,),
            ).fetchone()
        if not row:
            return None
        return int(time.time()) - int(row[0])
