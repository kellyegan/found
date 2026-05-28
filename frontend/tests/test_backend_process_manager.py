"""
Tests for BackendProcessManager.

Covers:
- ready signal fires when health check passes immediately
- failed signal fires after all retries are exhausted
- health check is called exactly once per attempt (max_retries + 1 total)
- succeeds on a retry when the first attempt fails
- stop() terminates the subprocess
- stop() emits stopped signal
- default process factory launches uvicorn via subprocess.Popen
"""

import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QEventLoop, QTimer

from frontend.backend.process_manager import BackendProcessManager


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def wait_for_signal(signal, timeout_ms=2000):
    """Block the Qt event loop until signal fires or timeout expires.

    Returns a list of the emitted arguments (empty list on timeout).
    """
    loop = QEventLoop()
    received = []

    def capture(*args):
        received.extend(args if args else [True])
        loop.quit()

    signal.connect(capture)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    return received


def make_manager(
    health_checker=None,
    max_retries=2,
    retry_interval=0.0,
    startup_timeout=0.0,
):
    """Return a manager with an inert mock process and fast timing."""
    return BackendProcessManager(
        process_factory=lambda: MagicMock(),
        health_checker=health_checker or (lambda url: True),
        max_retries=max_retries,
        retry_interval=retry_interval,
        poll_interval=0.0,
        startup_timeout=startup_timeout,
    )


# ---------------------------------------------------------------------------
# Ready signal
# ---------------------------------------------------------------------------


def test_ready_signal_fires_when_health_check_passes(qapp):
    manager = make_manager(health_checker=lambda url: True)
    manager.start()
    assert wait_for_signal(manager.ready)


# ---------------------------------------------------------------------------
# Failed signal
# ---------------------------------------------------------------------------


def test_failed_signal_fires_after_all_retries_exhausted(qapp):
    manager = make_manager(health_checker=lambda url: False)
    manager.start()
    assert wait_for_signal(manager.failed)


def test_failed_message_includes_retry_count(qapp):
    manager = make_manager(health_checker=lambda url: False, max_retries=2)
    manager.start()
    messages = wait_for_signal(manager.failed)
    assert messages and "2" in messages[0]


# ---------------------------------------------------------------------------
# Retry behaviour
# ---------------------------------------------------------------------------


def test_health_check_called_once_per_attempt(qapp):
    call_count = [0]

    def counting_checker(url):
        call_count[0] += 1
        return False

    manager = make_manager(health_checker=counting_checker, max_retries=2)
    manager.start()
    wait_for_signal(manager.failed)

    assert call_count[0] == 3  # initial attempt + 2 retries


def test_succeeds_on_retry(qapp):
    call_count = [0]

    def flaky_checker(url):
        call_count[0] += 1
        return call_count[0] >= 2  # fail first call, pass on second

    manager = make_manager(health_checker=flaky_checker, max_retries=2)
    manager.start()
    assert wait_for_signal(manager.ready)


# ---------------------------------------------------------------------------
# stop()
# ---------------------------------------------------------------------------


def test_stop_terminates_process(qapp):
    mock_proc = MagicMock()
    manager = BackendProcessManager(
        process_factory=lambda: mock_proc,
        health_checker=lambda url: True,
        max_retries=0,
        retry_interval=0.0,
        poll_interval=0.0,
        startup_timeout=0.0,
    )
    manager.start()
    wait_for_signal(manager.ready)
    manager.stop()

    mock_proc.terminate.assert_called_once()


def test_stop_emits_stopped_signal(qapp):
    manager = make_manager()
    received = []
    manager.stopped.connect(lambda: received.append(True))
    manager.start()
    wait_for_signal(manager.ready)
    manager.stop()

    assert received


# ---------------------------------------------------------------------------
# Default process factory
# ---------------------------------------------------------------------------


def test_default_factory_launches_uvicorn(qapp):
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.poll.return_value = None
        mock_popen.return_value = mock_proc

        manager = BackendProcessManager(
            health_checker=lambda url: True,
            max_retries=0,
            retry_interval=0.0,
            poll_interval=0.0,
            startup_timeout=0.0,
        )
        manager.start()
        wait_for_signal(manager.ready)

    assert mock_popen.called
    cmd = mock_popen.call_args[0][0]
    assert any("uvicorn" in str(part) for part in cmd)
