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
from typing import Dict, List, Optional

from core.config import LoggerConfig
from handlers.console import create_console_handler
from handlers.file import create_file_handler
from utils.console import get_shared_console
from utils.rich_compat import RICH_AVAILABLE, Console


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
    ):
        """Initialize the logger manager.

        Args:
            shared_console: Whether all loggers share the same console handler
            shared_file: Optional path to shared log file for all loggers
            console_log_level: Log level for console output
            file_log_level: Log level for file output
            use_color: Enable colored console output
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
            use_color=self.use_color, use_rich=RICH_AVAILABLE, log_level=self.console_log_level, console=self._console
        )

    def _init_shared_file(self):
        """Initialize shared file handler."""
        if self.shared_file:
            self._shared_file_handler = create_file_handler(
                log_file=self.shared_file,
                mode="a",  # Append mode for shared file
                log_level=self.file_log_level,
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
            console_handler = create_console_handler(use_color=self.use_color, log_level=self.console_log_level)
            logger.addHandler(console_handler)

        # Add file handler based on strategy
        if file_strategy == "separate" and log_file:
            file_handler = create_file_handler(log_file=log_file, mode="a", log_level=self.file_log_level)
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
