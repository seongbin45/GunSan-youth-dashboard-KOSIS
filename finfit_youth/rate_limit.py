import threading
import time
from collections import deque


class SimpleRateLimiter:
    def __init__(self, per_minute: int):
        self.per_minute = max(1, per_minute)
        self._lock = threading.Lock()
        self._hits = deque()

    def acquire(self) -> None:
        with self._lock:
            now = time.time()
            while self._hits and now - self._hits[0] > 60:
                self._hits.popleft()

            if len(self._hits) >= self.per_minute:
                sleep_time = 60 - (now - self._hits[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)

            self._hits.append(time.time())
