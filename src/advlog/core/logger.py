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

"""Core logger class with advanced features."""

import logging
import sys
import threading
from typing import Dict, List, Optional

from advlog.core.config import LoggerConfig
from advlog.handlers.console import create_console_handler
from advlog.handlers.file import create_file_handler
from advlog.utils.console import get_shared_console
from advlog.utils.path import ensure_dir
from advlog.utils.rich_compat import RICH_AVAILABLE, Console


class AdvancedLogger:
    """Advanced logging system with rich features.

    This logger provides:
    - Colored console output (via Rich if available)
    - File logging with optional rotation
    - Separate log files for different levels
    - Progress bar integration
    - Distributed training support
    - Environment auto-detection

    By default, uses singleton pattern for the same logger name.

    Usage:
        # Simple usage
        logger = AdvancedLogger().get_logger()
        logger.info("Hello, world!")

        # With configuration
        config = LoggerConfig(
            name="MyApp",
            log_file="logs/app.log",
            use_color=True
        )
        logger = AdvancedLogger(config).get_logger()

        # Multiple loggers
        logger1 = AdvancedLogger(LoggerConfig(name="Module1"))
        logger2 = AdvancedLogger(LoggerConfig(name="Module2"))
    """

    _instances: Dict[str, "AdvancedLogger"] = {}
    _lock = __import__("threading").Lock()

    def __new__(cls, config: Optional[LoggerConfig] = None):
        """Create or return existing instance (singleton per logger name)."""
        # Get config first to determine the name
        cfg = config or LoggerConfig()
        name = cfg.name

        with cls._lock:
            # Check if instance already exists
            if name in cls._instances:
                return cls._instances[name]

            # Create new instance and store immediately
            instance = super().__new__(cls)
            cls._instances[name] = instance
            return instance

    def __init__(self, config: Optional[LoggerConfig] = None):
        """Initialize the logger.

        Args:
            config: Logger configuration. If None, uses default configuration.
        """
        # Get the name to check if already initialized
        cfg = config or LoggerConfig()
        name = cfg.name

        # Check if this instance was already initialized
        # (when __new__ returned an existing instance, this __init__ is called again)
        if hasattr(self, '_logger') and self._logger is not None:
            # Already initialized, just sync config reference
            self.config = self._instances[name].config
            return

        self.config = cfg

        # Initialize only if this is a new instance
        if name in self._instances and self._instances[name] is self:
            self._console: Optional["Console"] = None
            self._logger: Optional[logging.Logger] = None
            self._initialize()

    def _initialize(self):
        """Initialize the logger with handlers."""
        # Create console if Rich is available
        if RICH_AVAILABLE:
            self._console = get_shared_console()

        # Get or create logger
        self._logger = logging.getLogger(self.config.name)
        self._logger.setLevel(self.config.get_log_level())
        self._logger.propagate = self.config.propagate

        # Clear existing handlers
        if self._logger.hasHandlers():
            self._logger.handlers.clear()

        # Handle distributed training environments
        if self.config.use_accelerate:
            if not self._is_main_process():
                self._logger.addHandler(logging.NullHandler())
                return

        # Add console handler
        if self.config.console_output:
            console_handler = create_console_handler(
                use_color=self.config.use_color,
                use_rich=RICH_AVAILABLE,
                log_level=self.config.get_log_level(),
                enable_rich_tracebacks=self.config.enable_rich_tracebacks,
                console=self._console,
            )
            self._logger.addHandler(console_handler)

        # Add main file handler
        if self.config.log_file:
            file_handler = create_file_handler(
                log_file=self.config.log_file,
                mode=self.config.file_mode,
                max_file_size=self.config.max_file_size,
                backup_count=self.config.backup_count,
                log_level=self.config.get_log_level(),
                use_indented_format=True,
                indent_size=self.config.indent_size,
                date_format=self.config.date_format,
                log_format=self.config.log_format,
                encoding=self.config.encoding,
            )
            self._logger.addHandler(file_handler)

        # Add separate error file handler
        if self.config.separate_error_file:
            error_handler = create_file_handler(
                log_file=self.config.separate_error_file,
                mode=self.config.file_mode,
                log_level=logging.ERROR,
                use_indented_format=True,
                indent_size=self.config.indent_size,
                date_format=self.config.date_format,
                log_format=self.config.log_format,
                encoding=self.config.encoding,
            )
            self._logger.addHandler(error_handler)

        # Add separate debug file handler
        if self.config.separate_debug_file:
            debug_handler = create_file_handler(
                log_file=self.config.separate_debug_file,
                mode=self.config.file_mode,
                log_level=logging.DEBUG,
                use_indented_format=True,
                indent_size=self.config.indent_size,
                date_format=self.config.date_format,
                log_format=self.config.log_format,
                encoding=self.config.encoding,
            )
            self._logger.addHandler(debug_handler)

        # Add custom handlers
        for handler in self.config.handlers:
            self._logger.addHandler(handler)

    def _is_main_process(self) -> bool:
        """Check if running in main process (for distributed training).

        Returns:
            True if main process, False otherwise.
        """
        try:
            from accelerate.state import PartialState

            return PartialState().is_main_process
        except ImportError:
            return True

    def get_logger(self) -> logging.Logger:
        """Get the underlying Python logger.

        Returns:
            Configured logging.Logger instance.
        """
        return self._logger

    def get_console(self) -> Optional["Console"]:
        """Get the Rich console instance.

        Returns:
            Rich Console instance if available, None otherwise.
        """
        return self._console

    def set_level(self, level: str):
        """Change the logging level.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        level = level.upper()
        log_level = getattr(logging, level)
        self._logger.setLevel(log_level)
        self.config.log_level = level

    def add_handler(self, handler: logging.Handler):
        """Add a custom handler to the logger.

        Args:
            handler: Logging handler to add
        """
        self._logger.addHandler(handler)

    def remove_handler(self, handler: logging.Handler):
        """Remove a handler from the logger.

        Args:
            handler: Logging handler to remove
        """
        self._logger.removeHandler(handler)

    @classmethod
    def reset(cls):
        """Reset all logger instances. Useful for testing."""
        cls._instances.clear()

    @classmethod
    def reset_instance(cls, name: str):
        """Reset a specific logger instance.

        Args:
            name: Logger name to reset
        """
        if name in cls._instances:
            del cls._instances[name]

    @classmethod
    def get_instance(cls, name: str) -> Optional["AdvancedLogger"]:
        """Get an existing logger instance by name.

        Args:
            name: Logger name

        Returns:
            AdvancedLogger instance if exists, None otherwise
        """
        return cls._instances.get(name)

    # Convenience methods for logging
    def debug(self, message: str, *args, **kwargs):
        """Log a debug message."""
        self._logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log an info message."""
        self._logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log a warning message."""
        self._logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log an error message."""
        self._logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log a critical message."""
        self._logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """Log an exception with traceback."""
        self._logger.exception(message, *args, **kwargs)


def setup_exception_logging(logger: Optional[logging.Logger] = None):
    """Setup global exception handler to log uncaught exceptions.

    Args:
        logger: Logger to use for exception logging.
                If None, uses the default AdvancedLogger.

    Example:
        setup_exception_logging()
        raise Exception("This will be logged")
    """
    if logger is None:
        logger = AdvancedLogger().get_logger()

    def log_uncaught_exceptions(exc_type, exc_value, exc_tb):
        """Log uncaught exceptions.

        Args:
            exc_type: The type of the exception
            exc_value: The value of the exception
            exc_tb: The traceback of the exception
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't log keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_tb)
        else:
            logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    sys.excepthook = log_uncaught_exceptions


class LoggerManager:
    """Centralized logger manager with shared console output.

    This manager allows multiple modules to:
    - Share a unified console output (avoiding conflicts)
    - Have individual or shared file outputs
    - Maintain proper time ordering

    Usage:
        # Create manager with shared console
        manager = LoggerManager(shared_console=True)

        # Register loggers for different modules
        logger1 = manager.register_logger("module1",
            file_strategy="separate",
            log_file="logs/module1.log"
        )
        logger2 = manager.register_logger("module2",
            file_strategy="separate",
            log_file="logs/module2.log"
        )

        # Both loggers output to console, but separate files
        logger1.info("Message from module 1")
        logger2.info("Message from module 2")

        # Or use merged file strategy
        logger3 = manager.register_logger("module3",
            file_strategy="merged",
            shared_file="logs/all.log"
        )
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure one manager per application."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        shared_console: bool = True,
        shared_file: Optional[str] = None,
        console_log_level: int = logging.INFO,
        file_log_level: int = logging.DEBUG,
        use_color: bool = True,
        show_location: bool = False,
        file_mode: str = "w",
    ):
        """Initialize the logger manager.

        Args:
            shared_console: Whether all loggers share the same console handler
            shared_file: Optional path to shared log file for all loggers
            console_log_level: Log level for console output
            file_log_level: Log level for file output
            use_color: Enable colored console output
            show_location: Show source location (file:line) in console sidebar
            file_mode: File opening mode ('w' for overwrite, 'a' for append)
        """
        # Avoid re-initialization
        if hasattr(self, "_initialized"):
            return

        self._initialized = True
        self.shared_console = shared_console
        self.shared_file = shared_file
        self.console_log_level = console_log_level
        self.file_log_level = file_log_level
        self.use_color = use_color
        self.show_location = show_location
        self.file_mode = file_mode

        # Storage for registered loggers
        self.loggers: Dict[str, logging.Logger] = {}

        # Shared handlers
        self._console_handler: Optional[logging.Handler] = None
        self._shared_file_handler: Optional[logging.Handler] = None
        self._console: Optional["Console"] = None

        # Initialize shared console if needed
        if shared_console:
            self._init_shared_console()

        # Initialize shared file if provided
        if shared_file:
            self._init_shared_file()

    def _init_shared_console(self):
        """Initialize shared console handler."""
        if RICH_AVAILABLE:
            self._console = get_shared_console()

        self._console_handler = create_console_handler(
            use_color=self.use_color,
            use_rich=RICH_AVAILABLE,
            log_level=self.console_log_level,
            show_location=self.show_location,
            console=self._console,
        )

    def _init_shared_file(self):
        """Initialize shared file handler."""
        if self.shared_file:
            self._shared_file_handler = create_file_handler(
                log_file=self.shared_file,
                mode=self.file_mode,
                log_level=self.file_log_level,
                show_location=self.show_location,
            )

    def register_logger(
        self,
        name: str,
        log_level: int = logging.DEBUG,
        file_strategy: str = "separate",
        log_file: Optional[str] = None,
        use_console: bool = True,
        config: Optional[LoggerConfig] = None,
    ) -> logging.Logger:
        """Register a new logger with the manager.

        Args:
            name: Logger name (usually module name)
            log_level: Logger level
            file_strategy: "separate" (own file), "merged" (shared), or "none"
            log_file: Path to log file (for separate strategy)
            use_console: Whether to output to console
            config: Optional LoggerConfig for advanced configuration

        Returns:
            Configured logging.Logger instance

        Example:
            # Separate file, shared console
            logger = manager.register_logger(
                "mymodule",
                file_strategy="separate",
                log_file="logs/mymodule.log"
            )

            # Merged file, shared console
            logger = manager.register_logger(
                "another",
                file_strategy="merged"
            )

            # No file, console only
            logger = manager.register_logger(
                "console_only",
                file_strategy="none"
            )
        """
        # Return existing logger if already registered
        if name in self.loggers:
            return self.loggers[name]

        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.propagate = False

        # Clear any existing handlers
        logger.handlers.clear()

        # Add console handler
        if use_console and self.shared_console and self._console_handler:
            logger.addHandler(self._console_handler)
        elif use_console and not self.shared_console:
            # Create individual console handler
            console_handler = create_console_handler(
                use_color=self.use_color,
                log_level=self.console_log_level,
                show_location=self.show_location,
            )
            logger.addHandler(console_handler)

        # Add file handler based on strategy
        if file_strategy == "separate" and log_file:
            file_handler = create_file_handler(
                log_file=log_file,
                mode="a",
                log_level=self.file_log_level,
                show_location=self.show_location,
            )
            logger.addHandler(file_handler)
        elif file_strategy == "merged" and self._shared_file_handler:
            logger.addHandler(self._shared_file_handler)

        # Store logger
        self.loggers[name] = logger

        return logger

    def get_logger(self, name: str) -> Optional[logging.Logger]:
        """Get a registered logger by name.

        Args:
            name: Logger name

        Returns:
            Logger instance or None if not registered
        """
        return self.loggers.get(name)

    def get_all_loggers(self) -> Dict[str, logging.Logger]:
        """Get all registered loggers.

        Returns:
            Dictionary of logger name to logger instance
        """
        return self.loggers.copy()

    def set_console_level(self, level: int):
        """Change console log level for all loggers.

        Args:
            level: New log level (e.g., logging.DEBUG)
        """
        if self._console_handler:
            self._console_handler.setLevel(level)

    def set_file_level(self, level: int):
        """Change file log level for shared file handler.

        Args:
            level: New log level
        """
        if self._shared_file_handler:
            self._shared_file_handler.setLevel(level)

    def unregister_logger(self, name: str):
        """Unregister and cleanup a logger.

        Args:
            name: Logger name to unregister
        """
        if name in self.loggers:
            logger = self.loggers[name]
            # Remove handlers that are not shared
            handlers_to_remove = []
            for handler in logger.handlers:
                if handler != self._console_handler and handler != self._shared_file_handler:
                    handlers_to_remove.append(handler)

            for handler in handlers_to_remove:
                logger.removeHandler(handler)
                handler.close()

            del self.loggers[name]

    def shutdown(self):
        """Shutdown all loggers and close handlers."""
        for logger in self.loggers.values():
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()

        self.loggers.clear()

        if self._console_handler:
            self._console_handler.close()
            self._console_handler = None

        if self._shared_file_handler:
            self._shared_file_handler.close()
            self._shared_file_handler = None

    @classmethod
    def reset(cls):
        """Reset the singleton instance. Useful for testing."""
        if cls._instance:
            cls._instance.shutdown()
        cls._instance = None


# Convenience function
def create_logger_group(
    module_names: List[str],
    shared_console: bool = True,
    shared_file: Optional[str] = None,
    file_strategy: str = "separate",
    log_dir: str = "logs",
    use_color: bool = True,
) -> Dict[str, logging.Logger]:
    """Create a group of loggers with coordinated output.

    Args:
        module_names: List of module names
        shared_console: Share console output
        shared_file: Optional shared file path
        file_strategy: "separate", "merged", or "none"
        log_dir: Directory for separate log files
        use_color: Enable colored output

    Returns:
        Dictionary mapping module names to logger instances

    Example:
        loggers = create_logger_group(
            ["api", "database", "auth"],
            shared_console=True,
            shared_file="logs/app.log",
            file_strategy="merged"
        )

        loggers["api"].info("API started")
        loggers["database"].info("DB connected")
    """
    manager = LoggerManager(shared_console=shared_console, shared_file=shared_file, use_color=use_color)

    loggers = {}
    for name in module_names:
        if file_strategy == "separate":
            log_file = f"{log_dir}/{name}.log"
        else:
            log_file = None

        loggers[name] = manager.register_logger(name=name, file_strategy=file_strategy, log_file=log_file)

    return loggers
