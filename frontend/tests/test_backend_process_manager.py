"""
Tests for BackendProcessManager.

Covers:
- ready signal fires when health check passes immediately
- failed signal fires after all retries are exhausted
- health check is called exactly once per attempt (max_retries + 1 total)
- succeeds on a retry when the first attempt fails
- failed fires quickly when the subprocess exits before health check passes
- stop() terminates the subprocess
- stop() emits stopped signal
- default process factory launches uvicorn via subprocess.Popen
- integration: real backend subprocess starts and ready signal fires
"""

import socket
import pytest
from unittest.mock import MagicMock, patch

from PySide6.QtCore import QEventLoop, QTimer

from frontend.backend.process_manager import BackendProcessManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def wait_for_signal(signal, timeout_ms=2000):
    loop = QEventLoop()
    received = []

    def capture(*args):
        received.extend(args if args else [True])
        loop.quit()

    signal.connect(capture)
    QTimer.singleShot(timeout_ms, loop.quit)
    loop.exec()
    return received


def _running_mock():
    """MagicMock that looks like a running subprocess (poll() returns None)."""
    proc = MagicMock()
    proc.poll.return_value = None
    return proc


def make_manager(
    health_checker=None,
    max_retries=2,
    retry_interval=0.0,
    startup_timeout=0.0,
):
    """Return a manager with a running mock process and fast timing."""
    return BackendProcessManager(
        process_factory=_running_mock,
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
    result = wait_for_signal(manager.ready)
    manager.stop()
    assert result


# ---------------------------------------------------------------------------
# Failed signal
# ---------------------------------------------------------------------------


def test_failed_signal_fires_after_all_retries_exhausted(qapp):
    manager = make_manager(health_checker=lambda url: False)
    manager.start()
    result = wait_for_signal(manager.failed)
    manager.stop()
    assert result


def test_failed_message_includes_retry_count(qapp):
    manager = make_manager(health_checker=lambda url: False, max_retries=2)
    manager.start()
    messages = wait_for_signal(manager.failed)
    manager.stop()
    assert messages and "2" in messages[0]


def test_failed_fires_quickly_when_process_exits(qapp):
    """If the subprocess exits before the health check passes, fail fast — do
    not wait for the full startup_timeout (which would be 30 s in production)."""
    exited_proc = MagicMock()
    exited_proc.poll.return_value = 1  # non-None → process has exited

    manager = BackendProcessManager(
        process_factory=lambda: exited_proc,
        health_checker=lambda url: False,
        max_retries=0,
        retry_interval=0.0,
        poll_interval=0.0,
        startup_timeout=30.0,  # would block for 30 s without exit detection
    )
    manager.start()
    result = wait_for_signal(manager.failed, timeout_ms=2000)
    manager.stop()
    assert result, "failed signal did not fire quickly after process exit"


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
    manager.stop()

    assert call_count[0] == 3  # initial attempt + 2 retries


def test_succeeds_on_retry(qapp):
    call_count = [0]

    def flaky_checker(url):
        call_count[0] += 1
        return call_count[0] >= 2  # fail first call, pass on second

    manager = make_manager(health_checker=flaky_checker, max_retries=2)
    manager.start()
    result = wait_for_signal(manager.ready)
    manager.stop()
    assert result


# ---------------------------------------------------------------------------
# stop()
# ---------------------------------------------------------------------------


def test_stop_terminates_process(qapp):
    mock_proc = _running_mock()
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
# Retrying signal
# ---------------------------------------------------------------------------


def test_retrying_signal_fires_once_per_retry(qapp):
    manager = make_manager(health_checker=lambda url: False, max_retries=2)
    retry_attempts = []
    manager.retrying.connect(lambda n: retry_attempts.append(n))
    manager.start()
    wait_for_signal(manager.failed)
    manager.stop()
    assert len(retry_attempts) == 2  # max_retries=2 → two retries


def test_retrying_signal_not_fired_on_initial_attempt(qapp):
    manager = make_manager(health_checker=lambda url: False, max_retries=0)
    retry_attempts = []
    manager.retrying.connect(lambda n: retry_attempts.append(n))
    manager.start()
    wait_for_signal(manager.failed)
    manager.stop()
    assert retry_attempts == []  # no retries — initial attempt only


# ---------------------------------------------------------------------------
# Default process factory
# ---------------------------------------------------------------------------


def test_default_factory_launches_uvicorn(qapp):
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = _running_mock()
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
        manager.stop()

    assert mock_popen.called
    cmd = mock_popen.call_args[0][0]
    assert any("uvicorn" in str(part) for part in cmd)


# ---------------------------------------------------------------------------
# Integration — real backend subprocess
# ---------------------------------------------------------------------------


def _port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


@pytest.mark.integration
def test_real_backend_startup_fires_ready(qapp):
    """Start an actual backend subprocess and verify the ready signal fires.

    This is the test that catches 'the backend never starts' failures that
    unit tests (which mock everything) cannot detect.
    """
    port = 18765
    if not _port_free(port):
        pytest.skip(f"port {port} in use — cannot run integration test")

    manager = BackendProcessManager(
        port=port,
        max_retries=0,
        retry_interval=0.0,
        poll_interval=0.5,
        startup_timeout=30.0,
    )
    manager.start()
    result = wait_for_signal(manager.ready, timeout_ms=35000)
    manager.stop()
    wait_for_signal(manager.stopped, timeout_ms=5000)

    assert result, (
        "Backend never became ready — check that the virtualenv has uvicorn "
        "and that backend/app/main.py starts correctly"
    )
