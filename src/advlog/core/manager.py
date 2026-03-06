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

"""Logger manager for coordinating multiple loggers with shared console output."""

import logging
import threading

from advlog.core.config import LoggerConfig
from advlog.handlers.console import create_console_handler
from advlog.handlers.file import create_file_handler
from advlog.utils.console import get_shared_console
from advlog.utils.rich_compat import RICH_AVAILABLE, Console


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
        shared_file: str | None = None,
        console_log_level: int = logging.INFO,
        file_log_level: int = logging.DEBUG,
        use_color: bool = True,
        show_location: bool = False,
        file_mode: str = "w",
    ):
        """Initialize the logger manager.

        Supports re-initialization to update global settings mid-run.
        If already initialized, existing loggers will be updated to use
        the new shared handlers.

        Args:
            shared_console: Whether all loggers share the same console handler
            shared_file: Optional path to shared log file for all loggers
            console_log_level: Log level for console output
            file_log_level: Log level for file output
            use_color: Enable colored console output
            show_location: Show source location (file:line) in console sidebar
            file_mode: File opening mode ('w' for overwrite, 'a' for append)
        """
        # Initialize internal storage ONLY ONCE
        if not hasattr(self, "_internal_init"):
            self.loggers: dict[str, logging.Logger] = {}
            self._logger_strategies: dict[str, dict] = {}
            self._console_handler: logging.Handler | None = None
            self._shared_file_handler: logging.Handler | None = None
            self._console: Console | None = None
            self._internal_init = True

        # Capture old handlers for cleanup if re-initializing
        old_console = self._console_handler
        old_file = self._shared_file_handler

        self.shared_console = shared_console
        self.shared_file = shared_file
        self.console_log_level = console_log_level
        self.file_log_level = file_log_level
        self.use_color = use_color
        self.show_location = show_location
        self.file_mode = file_mode

        # Initialize shared console if needed
        if shared_console:
            self._init_shared_console()

        # Initialize shared file if provided
        if shared_file:
            self._init_shared_file()

        # If already initialized previously, we need to refresh all existing loggers
        if hasattr(self, "_initialized") and self._initialized:
            self._refresh_loggers(old_console, old_file)

        self._initialized = True

    def _refresh_loggers(self, old_console=None, old_file=None):
        """Update all registered loggers with new handlers."""
        for name, logger in self.loggers.items():
            # Remove old handlers if they are still attached
            if old_console and old_console in logger.handlers:
                logger.removeHandler(old_console)
            if old_file and old_file in logger.handlers:
                logger.removeHandler(old_file)

            # Get the strategy used when this logger was registered
            strategy = self._logger_strategies.get(name, {})
            use_console = strategy.get("use_console", True)
            file_strategy = strategy.get("file_strategy", "merged")

            # Add new console handler if applicable
            if use_console and self.shared_console and self._console_handler:
                if self._console_handler not in logger.handlers:
                    logger.addHandler(self._console_handler)

            # Add new merged file handler if applicable
            if file_strategy == "merged" and self._shared_file_handler:
                if self._shared_file_handler not in logger.handlers:
                    logger.addHandler(self._shared_file_handler)

        # Close old file handler if it was replaced
        if old_file and old_file != self._shared_file_handler:
            old_file.close()

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
        name: str = "",
        log_level: int = logging.DEBUG,
        file_strategy: str = "separate",
        log_file: str | None = None,
        use_console: bool = True,
        config: LoggerConfig | None = None,
    ) -> logging.Logger:
        """Register a new logger with the manager.

        Args:
            name: Logger name (usually module __name__). Overridden by config.name
                  if a config is provided.
            log_level: Logger level. Overridden by config.log_level if config provided.
            file_strategy: \"separate\" (own file), \"merged\" (shared), or \"none\".
                  When using config, \"separate\" is inferred automatically if
                  config.log_file is set.
            log_file: Path to log file (for separate strategy). Overridden by
                      config.log_file if config provided.
            use_console: Whether to output to console. Overridden by
                         config.console_output if config provided.
            config: Optional LoggerConfig for per-logger overrides. When provided,
                    fields in config take precedence over the flat keyword arguments.

        Returns:
            Configured logging.Logger instance

        Example:
            # Simple merged usage (share the manager's shared file)
            logger = manager.register_logger("mymodule", file_strategy="merged")

            # Separate file
            logger = manager.register_logger(
                "mymodule",
                file_strategy="separate",
                log_file="logs/mymodule.log",
            )

            # Advanced per-logger config
            from advlog import LoggerConfig
            logger = manager.register_logger(
                config=LoggerConfig(
                    name="mymodule",
                    log_file="logs/mymodule.log",
                    log_level="DEBUG",
                    show_location=True,
                )
            )
        """
        # Resolve effective values from config (if provided)
        if config is not None:
            name = config.name
            log_level = config.get_log_level()
            use_console = config.console_output
            if config.log_file:
                log_file = config.log_file
                file_strategy = "separate"

        if not name:
            raise ValueError("Logger name must be provided either via 'name' or 'config.name'")

        # Return existing logger if already registered
        if name in self.loggers:
            return self.loggers[name]

        # Determine show_location per logger (config overrides manager default)
        effective_show_location = config.show_location if config is not None else self.show_location

        # Store logger metadata for potential re-initialization
        self._logger_strategies[name] = {
            "use_console": use_console,
            "file_strategy": file_strategy,
        }

        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.propagate = config.propagate if config is not None else False

        # Clear any existing handlers
        logger.handlers.clear()

        # Add console handler
        if use_console and self.shared_console and self._console_handler:
            logger.addHandler(self._console_handler)
        elif use_console and not self.shared_console:
            console_handler = create_console_handler(
                use_color=self.use_color,
                log_level=self.console_log_level,
                show_location=effective_show_location,
            )
            logger.addHandler(console_handler)

        # Add file handler based on strategy
        if file_strategy == "separate" and log_file:
            file_handler = create_file_handler(
                log_file=log_file,
                mode=config.file_mode if config is not None else "a",
                log_level=self.file_log_level,
                show_location=effective_show_location,
            )
            logger.addHandler(file_handler)
        elif file_strategy == "merged" and self._shared_file_handler:
            logger.addHandler(self._shared_file_handler)

        # Store logger
        self.loggers[name] = logger

        return logger

    def get_logger(self, name: str) -> logging.Logger | None:
        """Get a registered logger by name.

        Args:
            name: Logger name

        Returns:
            Logger instance or None if not registered
        """
        return self.loggers.get(name)

    def get_all_loggers(self) -> dict[str, logging.Logger]:
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
    module_names: list[str],
    shared_console: bool = True,
    shared_file: str | None = None,
    file_strategy: str = "separate",
    log_dir: str = "logs",
    use_color: bool = True,
) -> dict[str, logging.Logger]:
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
