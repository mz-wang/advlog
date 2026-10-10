# Copyright 2026 Mengzhao Wang
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for LoggerManager and global API."""

import json
import logging
import logging.handlers
import tempfile
from pathlib import Path

import pytest

from advlog.core import LoggerConfig, LoggerManager, create_logger_group


@pytest.fixture(autouse=True)
def reset_manager():
    """Reset LoggerManager singleton between tests."""
    yield
    LoggerManager.reset()


class TestLoggerManager:
    """Test LoggerManager class."""

    def test_singleton(self):
        """LoggerManager is a singleton."""
        m1 = LoggerManager()
        m2 = LoggerManager()
        assert m1 is m2

    def test_register_logger(self):
        """Registering a logger returns a logging.Logger."""
        manager = LoggerManager(shared_console=False)
        logger = manager.register_logger("test_module", file_strategy="none")
        assert isinstance(logger, logging.Logger)
        assert "test_module" in manager.loggers

    def test_register_returns_same_logger(self):
        """Registering the same name twice returns the same object."""
        manager = LoggerManager(shared_console=False)
        l1 = manager.register_logger("mod", file_strategy="none")
        l2 = manager.register_logger("mod", file_strategy="none")
        assert l1 is l2

    def test_get_logger(self):
        """get_logger retrieves a previously registered logger."""
        manager = LoggerManager(shared_console=False)
        registered = manager.register_logger("mod", file_strategy="none")
        assert manager.get_logger("mod") is registered

    def test_get_nonexistent_logger(self):
        """get_logger returns None for unknown names."""
        manager = LoggerManager(shared_console=False)
        assert manager.get_logger("does_not_exist") is None

    def test_unregister_logger(self):
        """Unregistering removes the logger from the manager."""
        manager = LoggerManager(shared_console=False)
        manager.register_logger("mod", file_strategy="none")
        manager.unregister_logger("mod")
        assert "mod" not in manager.loggers

    def test_get_all_loggers(self):
        """get_all_loggers returns all registered loggers."""
        manager = LoggerManager(shared_console=False)
        manager.register_logger("a", file_strategy="none")
        manager.register_logger("b", file_strategy="none")
        all_loggers = manager.get_all_loggers()
        assert "a" in all_loggers
        assert "b" in all_loggers

    def test_register_with_loggerconfig(self):
        """register_logger correctly applies LoggerConfig overrides."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            log_file = str(Path(tmpdir) / "mod.log")
            config = LoggerConfig(
                name="configured_mod",
                log_file=log_file,
                log_level="DEBUG",
                show_location=False,
                console_output=False,
            )
            manager = LoggerManager(shared_console=False)
            logger = manager.register_logger(config=config)
            assert isinstance(logger, logging.Logger)
            assert logger.level == logging.DEBUG
            assert Path(log_file).parent.exists()
            LoggerManager.reset()

    def test_register_loggerconfig_requires_name(self):
        """register_logger raises ValueError when name is empty and no config given."""
        manager = LoggerManager(shared_console=False)
        with pytest.raises(ValueError):
            manager.register_logger()  # no name, no config

    def test_file_logging(self):
        """Logger writes to file when configured with separate strategy."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            log_file = str(Path(tmpdir) / "test.log")
            manager = LoggerManager(shared_console=False)
            logger = manager.register_logger(
                "file_mod",
                file_strategy="separate",
                log_file=log_file,
            )
            logger.info("hello from test")
            for h in logger.handlers:
                h.flush()
            assert Path(log_file).exists()
            assert "hello from test" in Path(log_file).read_text()
            LoggerManager.reset()

    def test_merged_file_strategy(self):
        """Loggers with merged strategy share the shared file handler."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            shared = str(Path(tmpdir) / "shared.log")
            manager = LoggerManager(shared_console=False, shared_file=shared, file_mode="w")
            l1 = manager.register_logger("m1", file_strategy="merged")
            l2 = manager.register_logger("m2", file_strategy="merged")
            l1.warning("from m1")
            l2.warning("from m2")
            for h in l1.handlers + l2.handlers:
                h.flush()
            content = Path(shared).read_text()
            assert "from m1" in content
            assert "from m2" in content
            LoggerManager.reset()


def _read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines()]


class TestFileFormat:
    """Test structured (JSON Lines) file output."""

    def test_both_writes_text_and_jsonl(self):
        """file_format='both' writes a text file and a .jsonl file side by side."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            shared = Path(tmpdir) / "shared.log"
            manager = LoggerManager(shared_console=False, shared_file=str(shared), file_format="both")
            log = manager.register_logger("fmt_both", file_strategy="merged")
            log.info("run started", extra={"lr": 0.001})
            LoggerManager.reset()

            assert "run started" in shared.read_text()
            records = _read_jsonl(shared.with_suffix(".jsonl"))
            assert len(records) == 1
            assert records[0]["message"] == "run started"
            assert records[0]["logger"] == "fmt_both"
            assert records[0]["extra"] == {"lr": 0.001}

    def test_json_only_writes_jsonl(self):
        """file_format='json' writes only the .jsonl file."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            shared = Path(tmpdir) / "shared.log"
            manager = LoggerManager(shared_console=False, shared_file=str(shared), file_format="json")
            log = manager.register_logger("fmt_json", file_strategy="merged")
            log.info("only json")
            LoggerManager.reset()

            assert not shared.exists()
            assert _read_jsonl(shared.with_suffix(".jsonl"))[0]["message"] == "only json"

    def test_text_is_default(self):
        """The default format writes no .jsonl file."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            shared = Path(tmpdir) / "shared.log"
            manager = LoggerManager(shared_console=False, shared_file=str(shared))
            manager.register_logger("fmt_text", file_strategy="merged").info("plain")
            LoggerManager.reset()

            assert shared.exists()
            assert not shared.with_suffix(".jsonl").exists()

    def test_invalid_format_rejected(self):
        """Unknown formats raise ValueError."""
        with pytest.raises(ValueError):
            LoggerManager(shared_console=False, file_format="yaml")
        with pytest.raises(ValueError):
            LoggerConfig(name="bad", file_format="yaml")

    def test_separate_logger_inherits_manager_format(self):
        """Separate-file loggers follow the manager's file_format."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            log_file = Path(tmpdir) / "mod.log"
            manager = LoggerManager(shared_console=False, file_format="both")
            log = manager.register_logger("fmt_sep", file_strategy="separate", log_file=str(log_file))
            log.info("separate")
            LoggerManager.reset()

            assert "separate" in log_file.read_text()
            assert _read_jsonl(log_file.with_suffix(".jsonl"))[0]["message"] == "separate"

    def test_loggerconfig_overrides_manager_format(self):
        """LoggerConfig.file_format overrides the manager's file_format."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            log_file = Path(tmpdir) / "mod.log"
            manager = LoggerManager(shared_console=False)
            config = LoggerConfig(name="fmt_cfg", log_file=str(log_file), file_format="json", console_output=False)
            manager.register_logger(config=config).info("from config")
            LoggerManager.reset()

            assert not log_file.exists()
            assert _read_jsonl(log_file.with_suffix(".jsonl"))[0]["message"] == "from config"

    def test_reinitialize_switches_format(self):
        """Re-initializing with a new format re-attaches handlers to existing loggers."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            shared = Path(tmpdir) / "shared.log"
            manager = LoggerManager(shared_console=False)
            log = manager.register_logger("fmt_reinit", file_strategy="merged", use_console=False)
            assert log.handlers == []
            LoggerManager(shared_console=False, shared_file=str(shared), file_format="both")
            log.info("after reinit")
            assert len(log.handlers) == 2
            LoggerManager.reset()

            assert "after reinit" in shared.read_text()
            assert _read_jsonl(shared.with_suffix(".jsonl"))[0]["message"] == "after reinit"


class TestCreateFileHandlers:
    """Test the create_file_handlers factory."""

    def test_rotating_json(self):
        """Rotation and JSON output can be combined."""
        from advlog import JSONFormatter, create_file_handler

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            handler = create_file_handler(str(Path(tmpdir) / "rot.jsonl"), max_file_size=1024, use_json_format=True)
            assert isinstance(handler, logging.handlers.RotatingFileHandler)
            assert isinstance(handler.formatter, JSONFormatter)
            handler.close()

    def test_json_path_kept_when_already_jsonl(self):
        """A .jsonl path is used as-is for the JSON file."""
        from advlog import create_file_handlers

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            base = Path(tmpdir) / "run.jsonl"
            handlers = create_file_handlers(str(base), file_format="both")
            names = sorted(Path(h.baseFilename).name for h in handlers)
            assert names == ["run.jsonl", "run.log"]
            for h in handlers:
                h.close()


class TestCreateLoggerGroup:
    """Test create_logger_group convenience function."""

    def test_creates_multiple_loggers(self):
        """create_logger_group returns a dict of logging.Logger instances."""
        loggers = create_logger_group(
            ["api", "db"],
            shared_console=False,
            file_strategy="none",
        )
        assert set(loggers) == {"api", "db"}
        assert all(isinstance(v, logging.Logger) for v in loggers.values())


class TestGlobalAPI:
    """Test the initialize/get_logger/get_progress/reset API."""

    def teardown_method(self):
        from advlog import reset

        reset()

    def test_get_logger_auto_initializes(self):
        """get_logger works without explicit initialize()."""
        from advlog import get_logger

        log = get_logger("test.auto")
        assert isinstance(log, logging.Logger)

    def test_get_logger_returns_same_instance(self):
        """get_logger returns the same logger for the same name."""
        from advlog import get_logger

        l1 = get_logger("test.same")
        l2 = get_logger("test.same")
        assert l1 is l2

    def test_initialize_with_file(self):
        """initialize() configures file logging."""
        from advlog import get_logger, initialize, reset

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            initialize(output_dir=tmpdir, session_name="test_session", file_mode="w")
            log = get_logger("init_test")
            log.info("initialized message")
            for h in log.handlers:
                h.flush()
            # Find the log file
            log_files = list(Path(tmpdir).rglob("*.log"))
            assert len(log_files) >= 1
            content = log_files[0].read_text()
            assert "initialized message" in content
            # Close all handlers before tmpdir cleanup
            reset()

    def test_initialize_with_both_formats(self):
        """initialize(file_format='both') adds a .jsonl file next to the text log."""
        from advlog import get_logger, initialize, reset

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            initialize(output_dir=tmpdir, session_name="structured", file_mode="w", file_format="both")
            log = get_logger("init_structured")
            log.info("run params", extra={"params": {"lr": 0.001, "batch_size": 32}})
            # Close all handlers before reading and tmpdir cleanup
            reset()

            log_files = list(Path(tmpdir).rglob("*.log"))
            jsonl_files = list(Path(tmpdir).rglob("*.jsonl"))
            assert len(log_files) == 1
            assert len(jsonl_files) == 1
            assert jsonl_files[0].stem == log_files[0].stem
            records = _read_jsonl(jsonl_files[0])
            assert records[0]["extra"]["params"] == {"lr": 0.001, "batch_size": 32}

    def test_setup_exception_logging(self):
        """setup_exception_logging installs a custom excepthook."""
        import sys

        from advlog import setup_exception_logging

        original = sys.excepthook
        setup_exception_logging()
        assert sys.excepthook is not original
        # Restore
        sys.excepthook = original

    def test_reset_clears_state(self):
        """reset() allows re-initialization."""
        from advlog import get_logger, reset

        get_logger("before_reset")
        reset()
        # After reset, get_logger should re-initialize cleanly
        log = get_logger("after_reset")
        assert isinstance(log, logging.Logger)
