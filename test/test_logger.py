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

"""Tests for AdvancedLogger and LoggerManager."""

import logging

from advlog.core import AdvancedLogger, LoggerConfig, LoggerManager, create_logger_group


class TestAdvancedLogger:
    """Test AdvancedLogger class."""

    def test_imports(self):
        """Test that AdvancedLogger can be imported."""
        from advlog import AdvancedLogger

        assert AdvancedLogger is not None

    def test_singleton_per_name(self):
        """Test that loggers with the same name are singletons."""
        logger1 = AdvancedLogger(LoggerConfig(name="TestLogger"))
        logger2 = AdvancedLogger(LoggerConfig(name="TestLogger"))

        assert logger1 is logger2, "Loggers with same name should be the same instance"

    def test_different_names(self):
        """Test that loggers with different names are different instances."""
        logger1 = AdvancedLogger(LoggerConfig(name="Logger1"))
        logger2 = AdvancedLogger(LoggerConfig(name="Logger2"))

        assert logger1 is not logger2, "Loggers with different names should be different instances"

    def test_get_logger(self):
        """Test that get_logger returns a logging.Logger instance."""
        from advlog.core import AdvancedLogger
        mock_logger = AdvancedLogger(LoggerConfig(name="TestLogger"))
        logger = mock_logger.get_logger()
        assert isinstance(logger, logging.Logger)

    def test_logging_levels(self):
        """Test logging at different levels."""
        from advlog.core import AdvancedLogger
        mock_logger = AdvancedLogger(LoggerConfig(name="TestLogger"))
        logger = mock_logger.get_logger()

        # Test that methods exist
        assert hasattr(logger, "debug")
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")
        assert hasattr(logger, "critical")

    def test_set_level(self):
        """Test changing log level."""
        from advlog.core import AdvancedLogger
        mock_logger = AdvancedLogger(LoggerConfig(name="TestLogger"))
        mock_logger.set_level("DEBUG")
        assert mock_logger._logger.level == logging.DEBUG

        mock_logger.set_level("ERROR")
        assert mock_logger._logger.level == logging.ERROR

    def test_reset_instance(self):
        """Test resetting a specific logger instance."""
        logger1 = AdvancedLogger(LoggerConfig(name="TestLogger"))
        AdvancedLogger.reset_instance("TestLogger")

        # Create again after reset
        logger2 = AdvancedLogger(LoggerConfig(name="TestLogger"))

        assert logger1 is not logger2, "After reset, should get a new instance"

    def test_get_instance(self):
        """Test getting an existing logger instance."""
        logger1 = AdvancedLogger(LoggerConfig(name="TestLogger"))
        logger2 = AdvancedLogger.get_instance("TestLogger")

        assert logger1 is logger2, "get_instance should return the same instance"

    def test_get_nonexistent_instance(self):
        """Test getting a non-existent logger instance."""
        logger = AdvancedLogger.get_instance("NonExistent")
        assert logger is None


class TestLoggerManager:
    """Test LoggerManager class."""

    def test_singleton(self):
        """Test that LoggerManager is a singleton."""
        manager1 = LoggerManager()
        manager2 = LoggerManager()

        assert manager1 is manager2, "LoggerManager should be a singleton"

    def test_register_logger(self):
        """Test registering a logger."""
        manager = LoggerManager()
        logger = manager.register_logger("test_logger")

        assert isinstance(logger, logging.Logger)
        assert "test_logger" in manager.loggers

    def test_get_logger(self):
        """Test getting a registered logger."""
        manager = LoggerManager()
        registered = manager.register_logger("test_logger")
        retrieved = manager.get_logger("test_logger")

        assert registered is retrieved

    def test_get_nonexistent_logger(self):
        """Test getting a non-existent logger."""
        manager = LoggerManager()
        logger = manager.get_logger("non_existent")

        assert logger is None

    def test_unregister_logger(self):
        """Test unregistering a logger."""
        manager = LoggerManager()
        manager.register_logger("test_logger")

        assert "test_logger" in manager.loggers

        manager.unregister_logger("test_logger")
        assert "test_logger" not in manager.loggers

    def test_get_all_loggers(self):
        """Test getting all registered loggers."""
        manager = LoggerManager()
        manager.register_logger("logger1")
        manager.register_logger("logger2")

        all_loggers = manager.get_all_loggers()
        assert len(all_loggers) == 2
        assert "logger1" in all_loggers
        assert "logger2" in all_loggers

    def test_create_logger_group(self):
        """Test create_logger_group function."""
        loggers = create_logger_group(
            ["module1", "module2"],
            shared_console=False,
            file_strategy="none",
        )

        assert len(loggers) == 2
        assert "module1" in loggers
        assert "module2" in loggers
        assert all(isinstance(logger, logging.Logger) for logger in loggers.values())


class TestIntegration:
    """Integration tests for logger and manager."""

    def test_advanced_logger_with_file(self):
        """Test AdvancedLogger with file output."""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test.log"
            logger = AdvancedLogger(
                LoggerConfig(
                    name="TestLogger",
                    log_file=str(log_file),
                    console_output=False,
                )
            ).get_logger()

            logger.info("Test message")

            assert log_file.exists(), "Log file should be created"
            with open(log_file) as f:
                content = f.read()
                assert "Test message" in content

    def test_multiple_loggers_separate_files(self):
        """Test multiple loggers writing to separate files."""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmpdir:
            logger1 = AdvancedLogger(
                LoggerConfig(
                    name="Logger1",
                    log_file=str(Path(tmpdir) / "logger1.log"),
                    console_output=False,
                )
            ).get_logger()

            logger2 = AdvancedLogger(
                LoggerConfig(
                    name="Logger2",
                    log_file=str(Path(tmpdir) / "logger2.log"),
                    console_output=False,
                )
            ).get_logger()

            logger1.info("Message from logger 1")
            logger2.info("Message from logger 2")

            assert (Path(tmpdir) / "logger1.log").exists()
            assert (Path(tmpdir) / "logger2.log").exists()

            with open(Path(tmpdir) / "logger1.log") as f:
                assert "Message from logger 1" in f.read()
                assert "Message from logger 2" not in f.read()

            with open(Path(tmpdir) / "logger2.log") as f:
                assert "Message from logger 2" in f.read()
                assert "Message from logger 1" not in f.read()
