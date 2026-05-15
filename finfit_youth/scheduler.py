from __future__ import annotations

import threading
import time

from .service import YouthDataService


class YouthSyncScheduler:
    def __init__(self, service: YouthDataService, interval_seconds: int = 1800):
        self.service = service
        self.interval_seconds = interval_seconds
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run_loop(self) -> None:
        while not self._stop.is_set():
            try:
                self.service.sync_all()
            except Exception:
                pass
            self._stop.wait(self.interval_seconds)


def ensure_scheduler_started(service: YouthDataService, interval_seconds: int = 1800) -> YouthSyncScheduler:
    scheduler = YouthSyncScheduler(service=service, interval_seconds=interval_seconds)
    scheduler.start()
    return scheduler
