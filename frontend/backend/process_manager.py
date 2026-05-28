import subprocess
import time
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QObject, QThread, Signal


class BackendProcessManager(QObject):
    ready = Signal()
    failed = Signal(str)
    stopped = Signal()

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        max_retries: int = 2,
        retry_interval: float = 10.0,
        poll_interval: float = 0.5,
        startup_timeout: float = 30.0,
        process_factory: Callable | None = None,
        health_checker: Callable[[str], bool] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._host = host
        self._port = port
        self._max_retries = max_retries
        self._retry_interval = retry_interval
        self._poll_interval = poll_interval
        self._startup_timeout = startup_timeout
        self._process_factory = process_factory or self._default_process_factory
        self._health_checker = health_checker or self._default_health_checker
        self._process = None
        self._thread: _StartupThread | None = None

    @property
    def health_url(self) -> str:
        return f"http://{self._host}:{self._port}/health"

    def start(self) -> None:
        self._process = self._process_factory()
        self._thread = _StartupThread(
            health_checker=self._health_checker,
            health_url=self.health_url,
            max_retries=self._max_retries,
            retry_interval=self._retry_interval,
            poll_interval=self._poll_interval,
            startup_timeout=self._startup_timeout,
        )
        self._thread.ready.connect(self.ready)
        self._thread.failed.connect(self.failed)
        self._thread.start()

    def stop(self) -> None:
        if self._thread and self._thread.isRunning():
            self._thread.requestInterruption()
            self._thread.wait(3000)
        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=5)
            except Exception:
                self._process.kill()
        self.stopped.emit()

    def _default_process_factory(self):
        backend_dir = Path(__file__).parent.parent.parent / "backend"
        return subprocess.Popen(
            [
                "python", "-m", "uvicorn",
                "app.main:app",
                "--host", self._host,
                "--port", str(self._port),
            ],
            cwd=str(backend_dir),
        )

    @staticmethod
    def _default_health_checker(url: str) -> bool:
        try:
            import httpx
            response = httpx.get(url, timeout=2.0)
            return response.status_code == 200
        except Exception:
            return False


class _StartupThread(QThread):
    ready = Signal()
    failed = Signal(str)

    def __init__(
        self,
        health_checker: Callable[[str], bool],
        health_url: str,
        max_retries: int,
        retry_interval: float,
        poll_interval: float,
        startup_timeout: float,
        parent=None,
    ):
        super().__init__(parent)
        self._health_checker = health_checker
        self._health_url = health_url
        self._max_retries = max_retries
        self._retry_interval = retry_interval
        self._poll_interval = poll_interval
        self._startup_timeout = startup_timeout

    def run(self) -> None:
        for attempt in range(self._max_retries + 1):
            if self.isInterruptionRequested():
                return
            if attempt > 0:
                self._interruptible_sleep(self._retry_interval)
                if self.isInterruptionRequested():
                    return
            if self._poll_until_healthy():
                self.ready.emit()
                return
        self.failed.emit(
            f"Backend failed to start after {self._max_retries} retries"
        )

    def _poll_until_healthy(self) -> bool:
        deadline = time.monotonic() + self._startup_timeout
        while True:
            if self.isInterruptionRequested():
                return False
            if self._health_checker(self._health_url):
                return True
            if time.monotonic() >= deadline:
                return False
            self._interruptible_sleep(self._poll_interval)

    def _interruptible_sleep(self, duration: float) -> None:
        if duration <= 0:
            return
        elapsed = 0.0
        step = min(0.05, duration)
        while elapsed < duration:
            if self.isInterruptionRequested():
                return
            time.sleep(step)
            elapsed += step
