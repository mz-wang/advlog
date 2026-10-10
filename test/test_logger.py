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


class TestRotation:
    """Test size-based rotation through the high-level entry points."""

    def test_manager_rotates_shared_file(self):
        """max_file_size on the manager rotates the shared file and keeps backups."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            shared = Path(tmpdir) / "shared.log"
            manager = LoggerManager(
                shared_console=False, shared_file=str(shared), file_format="both", max_file_size=300, backup_count=2
            )
            log = manager.register_logger("rot_shared", file_strategy="merged", use_console=False)
            assert log.handlers and all(isinstance(h, logging.handlers.RotatingFileHandler) for h in log.handlers)
            for i in range(30):
                log.info("message number %d padded out to make the file grow", i)
            LoggerManager.reset()

            names = sorted(p.name for p in Path(tmpdir).iterdir())
            assert names == [
                "shared.jsonl",
                "shared.jsonl.1",
                "shared.jsonl.2",
                "shared.log",
                "shared.log.1",
                "shared.log.2",
            ]
            # Rotated JSON files still hold whole records
            assert _read_jsonl(Path(tmpdir) / "shared.jsonl.1")

    def test_no_rotation_by_default(self):
        """Without max_file_size the plain file handler is used."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            manager = LoggerManager(shared_console=False, shared_file=str(Path(tmpdir) / "shared.log"))
            log = manager.register_logger("rot_none", file_strategy="merged", use_console=False)
            assert type(log.handlers[0]) is logging.FileHandler
            LoggerManager.reset()

    def test_loggerconfig_overrides_rotation(self):
        """LoggerConfig.max_file_size / backup_count override the manager's values."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            manager = LoggerManager(shared_console=False, max_file_size=1000, backup_count=5)
            config = LoggerConfig(
                name="rot_cfg",
                log_file=str(Path(tmpdir) / "mod.log"),
                console_output=False,
                max_file_size=50,
                backup_count=1,
            )
            handler = manager.register_logger(config=config).handlers[0]
            assert isinstance(handler, logging.handlers.RotatingFileHandler)
            assert handler.maxBytes == 50
            assert handler.backupCount == 1

            inherited = manager.register_logger(
                "rot_inherit", file_strategy="separate", log_file=str(Path(tmpdir) / "other.log"), use_console=False
            ).handlers[0]
            assert inherited.maxBytes == 1000
            assert inherited.backupCount == 5
            LoggerManager.reset()

    def test_rotating_handler_matches_plain_handler(self):
        """Rotating files use the same line format and are created lazily."""
        from advlog import create_file_handler

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            plain_file = Path(tmpdir) / "plain.log"
            rotating_file = Path(tmpdir) / "rotating.log"
            plain = create_file_handler(str(plain_file))
            rotating = create_file_handler(str(rotating_file), max_file_size=10_000)
            assert not rotating_file.exists()

            record = logging.LogRecord("test", logging.INFO, "file.py", 1, "same line", (), None)
            plain.emit(record)
            rotating.emit(record)
            plain.close()
            rotating.close()
            assert plain_file.read_text() == rotating_file.read_text()
            assert "|INFO    | same line" in rotating_file.read_text()


class TestContext:
    """Test context fields bound to every record."""

    def test_bound_fields_reach_every_logger(self):
        """Bound fields are attached to records of loggers registered before and after."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            shared = Path(tmpdir) / "shared.log"
            manager = LoggerManager(shared_console=False, shared_file=str(shared), file_format="json")
            before = manager.register_logger("ctx_before", file_strategy="merged")
            manager.bind_context(run_id="exp-42", seed=7)
            after = manager.register_logger("ctx_after", file_strategy="merged")
            before.info("one")
            after.info("two", extra={"step": 3})
            LoggerManager.reset()

            records = _read_jsonl(shared.with_suffix(".jsonl"))
            assert records[0]["extra"] == {"run_id": "exp-42", "seed": 7}
            assert records[1]["extra"] == {"step": 3, "run_id": "exp-42", "seed": 7}

    def test_explicit_extra_wins(self):
        """A field passed via extra= overrides the bound value for that call only."""
        manager = LoggerManager(shared_console=False, context={"stage": "train"})
        log = manager.register_logger("ctx_explicit", file_strategy="none", use_console=False)
        records = []
        handler = logging.Handler()
        handler.emit = records.append
        log.addHandler(handler)

        log.info("overridden", extra={"stage": "eval"})
        log.info("default")
        assert [r.stage for r in records] == ["eval", "train"]

    def test_unbind_and_clear(self):
        """unbind_context removes named fields; clear_context removes all."""
        manager = LoggerManager(shared_console=False)
        manager.bind_context(a=1, b=2, c=3)
        manager.unbind_context("a", "missing")
        assert manager.get_context() == {"b": 2, "c": 3}
        manager.clear_context()
        assert manager.get_context() == {}

    def test_reserved_names_rejected(self):
        """Fields that would overwrite LogRecord attributes are rejected and change nothing."""
        manager = LoggerManager(shared_console=False, context={"run_id": "keep"})
        with pytest.raises(ValueError):
            manager.bind_context(ok=1, message="clobber")
        with pytest.raises(ValueError):
            LoggerManager(shared_console=False, context={"levelname": "clobber"})
        assert manager.get_context() == {"run_id": "keep"}

    def test_context_survives_reinitialize_until_replaced(self):
        """Re-initializing keeps the context unless a new one is passed."""
        manager = LoggerManager(shared_console=False, context={"run_id": "first"})
        LoggerManager(shared_console=False)
        assert manager.get_context() == {"run_id": "first"}
        LoggerManager(shared_console=False, context={"run_id": "second"})
        assert manager.get_context() == {"run_id": "second"}
        LoggerManager(shared_console=False, context={})
        assert manager.get_context() == {}

    def test_unregistered_logger_stops_receiving_context(self):
        """Unregistering detaches the context filter from the logger."""
        manager = LoggerManager(shared_console=False, context={"run_id": "x"})
        log = manager.register_logger("ctx_unregister", file_strategy="none", use_console=False)
        assert log.filters
        manager.unregister_logger("ctx_unregister")
        assert log.filters == []


class TestReinitialize:
    """Test that re-initializing applies the new settings in full."""

    def test_dropping_shared_file_stops_file_output(self):
        """Re-initializing without a shared file detaches and closes the old one."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            shared = Path(tmpdir) / "shared.log"
            manager = LoggerManager(shared_console=False, shared_file=str(shared), file_format="both")
            log = manager.register_logger("reinit_drop", file_strategy="merged", use_console=False)
            old_handlers = list(log.handlers)
            log.info("before")

            LoggerManager(shared_console=False)
            log.info("after")

            assert log.handlers == []
            assert all(h.stream is None for h in old_handlers)  # closed
            assert "after" not in shared.read_text()
            assert len(_read_jsonl(shared.with_suffix(".jsonl"))) == 1

    def test_use_color_controls_shared_console(self):
        """use_color=False turns color off on the shared console (and back on)."""
        from advlog.utils.console import get_shared_console

        try:
            LoggerManager(use_color=False)
            assert get_shared_console().no_color is True
            LoggerManager(use_color=True)
            assert get_shared_console().no_color is False
        finally:
            get_shared_console().no_color = False


class TestFileContent:
    """Test what ends up in the files (as opposed to on the console)."""

    def test_rich_markup_stripped_from_files(self):
        """Paired Rich tags are removed from text and JSON files; other brackets stay."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            shared = Path(tmpdir) / "shared.log"
            manager = LoggerManager(shared_console=False, shared_file=str(shared), file_format="both")
            log = manager.register_logger("content_markup", file_strategy="merged", use_console=False)
            log.info("[bold red]alert[/bold red] at arr[i] [1/3]")
            LoggerManager.reset()

            assert shared.read_text().rstrip().endswith("| alert at arr[i] [1/3]")
            assert _read_jsonl(shared.with_suffix(".jsonl"))[0]["message"] == "alert at arr[i] [1/3]"

    def test_text_only_records_skip_json(self):
        """Records marked text_only reach the text file but not the JSON file."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            shared = Path(tmpdir) / "shared.log"
            manager = LoggerManager(shared_console=False, shared_file=str(shared), file_format="both")
            log = manager.register_logger("content_text_only", file_strategy="merged", use_console=False)
            log.info("=" * 20, extra={"text_only": True})
            log.info("real record")
            LoggerManager.reset()

            assert shared.read_text().count("\n") == 2
            assert [r["message"] for r in _read_jsonl(shared.with_suffix(".jsonl"))] == ["real record"]


class TestLoggerConfigFields:
    """Test that every LoggerConfig field has an effect."""

    def test_file_format_fields_applied(self):
        """log_format, date_format and encoding shape the logger's own file."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            log_file = Path(tmpdir) / "mod.log"
            config = LoggerConfig(
                name="cfg_format",
                log_file=str(log_file),
                console_output=False,
                log_format="%(asctime)s <%(levelname)s> %(message)s",
                date_format="%Y",
                encoding="utf-16",
            )
            manager = LoggerManager(shared_console=False)
            manager.register_logger(config=config).info("héllo")
            LoggerManager.reset()

            line = log_file.read_text(encoding="utf-16").strip()
            year, rest = line.split(" ", 1)
            assert len(year) == 4 and year.isdigit()
            assert rest == "<INFO> héllo"

    def test_log_format_kept_with_show_location(self):
        """show_location inserts the location into a custom log_format instead of replacing it."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            log_file = Path(tmpdir) / "mod.log"
            config = LoggerConfig(
                name="cfg_location",
                log_file=str(log_file),
                console_output=False,
                show_location=True,
                log_format="<%(levelname)s> %(message)s",
            )
            manager = LoggerManager(shared_console=False)
            manager.register_logger(config=config).info("located")
            LoggerManager.reset()

            line = log_file.read_text().strip()
            assert line.startswith("<INFO> [test_logger.py:")
            assert line.endswith(":test_log_format_kept_with_show_location] located")

    def test_default_format_unchanged(self):
        """A config without format overrides writes the same line as no config."""
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            with_config = Path(tmpdir) / "a.log"
            without_config = Path(tmpdir) / "b.log"
            manager = LoggerManager(shared_console=False)
            manager.register_logger(
                config=LoggerConfig(name="cfg_default_a", log_file=str(with_config), console_output=False)
            ).info("same")
            manager.register_logger(
                "cfg_default_b", file_strategy="separate", log_file=str(without_config), use_console=False
            ).info("same")
            LoggerManager.reset()

            assert "|INFO    | same" in with_config.read_text()
            assert with_config.read_text()[19:] == without_config.read_text()[19:]

    def test_console_fields_applied_without_shared_console(self):
        """use_color and enable_rich_tracebacks configure the logger's own console handler."""
        from advlog.utils.console import get_shared_console

        manager = LoggerManager(shared_console=False)
        plain = manager.register_logger("cfg_console_default", file_strategy="none").handlers[0]
        assert plain.console is get_shared_console()
        assert plain.rich_tracebacks is True

        config = LoggerConfig(name="cfg_console", use_color=False, enable_rich_tracebacks=False)
        handler = manager.register_logger(config=config).handlers[0]
        assert handler.console is not get_shared_console()
        assert handler.console.no_color is True
        assert handler.rich_tracebacks is False

    def test_use_accelerate_silences_non_main_process(self, monkeypatch):
        """use_accelerate drops records once accelerate reports a non-main process."""
        import sys
        import types

        class FakePartialState:
            _shared_state: dict = {}
            is_main_process = True

        fake_module = types.ModuleType("accelerate.state")
        fake_module.PartialState = FakePartialState
        monkeypatch.setitem(sys.modules, "accelerate.state", fake_module)

        manager = LoggerManager(shared_console=False)
        log = manager.register_logger(
            config=LoggerConfig(name="cfg_accelerate", console_output=False, use_accelerate=True)
        )
        other = manager.register_logger("cfg_no_accelerate", file_strategy="none", use_console=False)
        seen = []
        handler = logging.Handler()
        handler.emit = lambda record: seen.append(record.getMessage())
        log.addHandler(handler)
        other.addHandler(handler)

        log.info("accelerate not initialized")
        FakePartialState._shared_state = {"initialized": True}
        log.info("main process")
        FakePartialState.is_main_process = False
        log.info("worker process")
        other.info("logger without use_accelerate")

        assert seen == ["accelerate not initialized", "main process", "logger without use_accelerate"]

    def test_to_dict_round_trip(self):
        """to_dict() carries every field, so from_dict() rebuilds an equal config."""
        config = LoggerConfig(
            name="cfg_round_trip",
            log_file="logs/x.log",
            file_format="both",
            max_file_size=1024,
            backup_count=2,
            use_color=False,
            log_format="%(message)s",
            date_format="%H:%M",
            encoding="latin-1",
            enable_rich_tracebacks=False,
            use_accelerate=True,
        )
        assert LoggerConfig.from_dict(config.to_dict()) == config


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

    def test_initialize_with_rotation_and_context(self):
        """initialize() passes rotation settings and context through to the log files."""
        from advlog import get_logger, initialize, reset

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            log_file = Path(tmpdir) / "run.log"
            initialize(
                log_file_path=str(log_file),
                file_format="both",
                max_file_size=400,
                backup_count=1,
                context={"run_id": "exp-42"},
            )
            log = get_logger("init_rotation")
            for i in range(20):
                log.info("line %d of a run that outgrows its file", i)
            reset()

            assert (Path(tmpdir) / "run.log.1").exists()
            assert not (Path(tmpdir) / "run.log.2").exists()
            records = _read_jsonl(log_file.with_suffix(".jsonl"))
            assert records and all(r["extra"] == {"run_id": "exp-42"} for r in records)

    def test_bind_context_api(self):
        """bind_context works before initialize() and survives it; reset() clears it."""
        from advlog import bind_context, clear_context, get_logger, initialize, reset, unbind_context

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            log_file = Path(tmpdir) / "run.log"
            bind_context(run_id="early", stage="setup")
            initialize(log_file_path=str(log_file), file_format="json")
            log = get_logger("init_context")
            log.info("first")
            unbind_context("stage")
            bind_context(epoch=2)
            log.info("second")
            clear_context()
            log.info("third")
            reset()

            records = _read_jsonl(log_file.with_suffix(".jsonl"))
            assert records[0]["extra"] == {"run_id": "early", "stage": "setup"}
            assert records[1]["extra"] == {"run_id": "early", "epoch": 2}
            assert "extra" not in records[2]

            initialize(enable_file_logging=False)
            from advlog import api

            assert api._LOGGER_MANAGER.get_context() == {}

    def test_disabling_file_logging_stops_writing(self):
        """initialize(enable_file_logging=False) detaches the log file set up earlier."""
        from advlog import get_logger, initialize, reset

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            log_file = Path(tmpdir) / "run.log"
            initialize(log_file_path=str(log_file), file_mode="w")
            log = get_logger("init_disable")
            log.warning("before")
            initialize(enable_file_logging=False)
            log.warning("after")
            reset()

            content = log_file.read_text()
            assert "before" in content
            assert "after" not in content

    def test_get_logger_applies_level_to_existing_logger(self):
        """An explicit log_level changes the level of an already-registered logger."""
        from advlog import get_logger

        log = get_logger("level.override")
        assert log.level == logging.DEBUG
        assert get_logger("level.override", log_level="ERROR") is log
        assert log.level == logging.ERROR
        # No level given: left as is
        get_logger("level.override")
        assert log.level == logging.ERROR

    def test_uncaught_exception_reaches_log_file(self):
        """The default exception hook logs through the managed logger, into the file."""
        import sys

        from advlog import initialize, reset, setup_exception_logging

        original = sys.excepthook
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:
            log_file = Path(tmpdir) / "run.log"
            initialize(log_file_path=str(log_file), file_format="both")
            try:
                setup_exception_logging()
                try:
                    raise RuntimeError("nobody caught this")
                except RuntimeError:
                    sys.excepthook(*sys.exc_info())
            finally:
                sys.excepthook = original
            reset()

            content = log_file.read_text()
            assert "Uncaught exception" in content
            assert "RuntimeError: nobody caught this" in content
            record = _read_jsonl(log_file.with_suffix(".jsonl"))[0]
            assert record["level"] == "ERROR"
            assert "RuntimeError: nobody caught this" in record["exception"]

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
