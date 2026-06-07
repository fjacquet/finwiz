"""Tests for ``finwiz.tools.logger.setup_logging`` file-handler routing.

These guard the rule that test runs must not pollute the production
``logs/finwiz*.log`` files: under pytest, file logs are redirected to a
``<log_dir>/tests`` subfolder while production runs keep writing to
``<log_dir>`` directly.
"""

import logging
import os
import sys

import pytest

from finwiz.tools.logger import setup_logging


@pytest.fixture
def restore_root_logging():
    """Snapshot and restore root logger handlers around setup_logging() calls.

    ``setup_logging`` mutates the global root logger, so we restore the prior
    handlers/level afterwards to avoid leaking state into other tests.
    """
    root = logging.getLogger()
    saved_handlers = root.handlers[:]
    saved_level = root.level
    try:
        yield
    finally:
        for handler in root.handlers[:]:
            root.removeHandler(handler)
        for handler in saved_handlers:
            root.addHandler(handler)
        root.setLevel(saved_level)


def _file_handler_paths() -> list[str]:
    """Absolute paths of every file handler attached to the root logger."""
    return [
        os.path.abspath(handler.baseFilename)
        for handler in logging.getLogger().handlers
        if isinstance(handler, logging.FileHandler)  # Rotating/Timed handlers subclass FileHandler
    ]


def test_under_pytest_redirects_file_logs_to_tests_subdir(tmp_path, restore_root_logging):
    """Under pytest, file logs land in <log_dir>/tests, not <log_dir>."""
    log_dir = str(tmp_path)

    setup_logging(log_to_file=True, log_dir=log_dir)

    paths = _file_handler_paths()
    assert paths, "expected file handlers to be attached"
    tests_dir = os.path.abspath(os.path.join(log_dir, "tests"))
    for path in paths:
        assert path.startswith(tests_dir), f"{path} should be under {tests_dir}"
    # Production-named files must NOT be created at the top level.
    assert not os.path.exists(os.path.join(log_dir, "finwiz.log"))
    assert not os.path.exists(os.path.join(log_dir, "finwiz_error.log"))


def test_outside_pytest_uses_log_dir_directly(tmp_path, monkeypatch, restore_root_logging):
    """Without the pytest signal, file logs target <log_dir> directly (prod behavior)."""
    monkeypatch.delitem(sys.modules, "pytest", raising=False)
    monkeypatch.delenv("FINWIZ_TEST_LOGS", raising=False)
    log_dir = str(tmp_path)

    setup_logging(log_to_file=True, log_dir=log_dir)

    paths = _file_handler_paths()
    assert paths, "expected file handlers to be attached"
    for path in paths:
        assert os.path.dirname(path) == os.path.abspath(log_dir), f"{path} should be directly under {log_dir}"
    assert os.path.exists(os.path.join(log_dir, "finwiz.log"))
    assert os.path.exists(os.path.join(log_dir, "finwiz_error.log"))
