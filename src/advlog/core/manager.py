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
import os
import threading
from collections.abc import Iterable
from typing import Any

from advlog.core.config import LoggerConfig
from advlog.core.filters import ContextFilter, MainProcessFilter
from advlog.handlers.console import create_console_handler
from advlog.handlers.file import FILE_FORMATS, create_file_handlers
from advlog.utils.console import get_shared_console
from advlog.utils.path import StrPath
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
        shared_file: StrPath | None = None,
        console_log_level: int = logging.INFO,
        file_log_level: int = logging.DEBUG,
        use_color: bool = True,
        show_location: bool = False,
        file_mode: str = "w",
        file_format: str = "text",
        max_file_size: int | None = None,
        backup_count: int = 5,
        context: dict[str, Any] | None = None,
        capture: str | Iterable[str] = (),
    ):
        """Initialize the logger manager.

        Supports re-initialization to update global settings mid-run.
        If already initialized, existing loggers will be updated to use
        the new shared handlers. Every call applies the full set of
        arguments: re-initializing without ``shared_file`` detaches and
        closes the shared file.

        Args:
            shared_console: Whether all loggers share the same console handler
            shared_file: Optional path to shared log file for all loggers
            console_log_level: Log level for console output
            file_log_level: Log level for file output
            use_color: Enable colored console output
            show_location: Show source location (file:line) in console sidebar
            file_mode: File opening mode ('w' for overwrite, 'a' for append)
            file_format: File output format: "text" (human-readable), "json"
                         (JSON Lines, written with a ``.jsonl`` extension), or
                         "both" (text file plus a ``.jsonl`` file next to it)
            max_file_size: Rotate log files when they reach this many bytes
                           (None = no rotation). Rotating files are always
                           appended to, regardless of file_mode.
            backup_count: Number of rotated files to keep
            context: Fields attached to every record (e.g. run id). None
                     keeps the context already bound; see bind_context().
            capture: Names of standard library loggers (usually top-level
                     package names) whose records, and their children's,
                     go to the shared console and file. See capture().
        """
        # Initialize internal storage ONLY ONCE
        if not hasattr(self, "_internal_init"):
            self.loggers: dict[str, logging.Logger] = {}
            self._logger_strategies: dict[str, dict] = {}
            self._console_handler: logging.Handler | None = None
            self._shared_file_handlers: list[logging.Handler] = []
            self._console: Console | None = None
            self._context_filter = ContextFilter()
            # Captured logger name -> its level before capture, restored on release
            self._captured: dict[str, int] = {}
            self._internal_init = True

        if file_format not in FILE_FORMATS:
            raise ValueError(f"Invalid file format: {file_format!r} (expected one of {FILE_FORMATS})")

        if context is not None:
            replacement = ContextFilter()
            replacement.bind(**context)  # validates before anything is changed
            self._context_filter.fields = replacement.fields

        # Capture old handlers for cleanup if re-initializing
        old_console = self._console_handler
        old_files = list(self._shared_file_handlers)

        self.shared_console = shared_console
        self.shared_file = os.fspath(shared_file) if shared_file is not None else None
        self.console_log_level = console_log_level
        self.file_log_level = file_log_level
        self.use_color = use_color
        self.show_location = show_location
        self.file_mode = file_mode
        self.file_format = file_format
        self.max_file_size = max_file_size
        self.backup_count = backup_count

        # The shared console has a single color setting, used by every
        # handler (and progress bar) that draws on it
        if RICH_AVAILABLE:
            get_shared_console().no_color = not use_color

        # Initialize shared console if needed
        if shared_console:
            self._init_shared_console()

        # Initialize shared file if provided; otherwise drop the previous one
        # (_refresh_loggers detaches and closes it)
        if shared_file:
            self._init_shared_file()
        else:
            self._shared_file_handlers = []

        # Captured loggers are moved to the new handlers (and released if no
        # longer listed) before _refresh_loggers closes the old files
        names = [logging.getLogger(n).name for n in ([capture] if isinstance(capture, str) else capture)]
        stale = [old_console, *old_files]
        for name in list(self._captured):
            if name not in names:
                self._release(name, stale)
        for name in names:
            self._capture(name, stale)

        # If already initialized previously, we need to refresh all existing loggers
        if hasattr(self, "_initialized") and self._initialized:
            self._refresh_loggers(old_console, old_files)

        self._initialized = True

    def _refresh_loggers(self, old_console=None, old_files=()):
        """Update all registered loggers with new handlers."""
        for name, logger in self.loggers.items():
            # Remove old handlers if they are still attached
            if old_console and old_console in logger.handlers:
                logger.removeHandler(old_console)
            for old_file in old_files:
                if old_file in logger.handlers:
                    logger.removeHandler(old_file)

            # Get the strategy used when this logger was registered
            strategy = self._logger_strategies.get(name, {})
            use_console = strategy.get("use_console", True)
            file_strategy = strategy.get("file_strategy", "merged")

            # Add new console handler if applicable
            if use_console and self.shared_console and self._console_handler:
                if self._console_handler not in logger.handlers:
                    logger.addHandler(self._console_handler)

            # Add new merged file handlers if applicable
            if file_strategy == "merged":
                for handler in self._shared_file_handlers:
                    if handler not in logger.handlers:
                        logger.addHandler(handler)

        # Close old file handlers that were replaced
        for old_file in old_files:
            if old_file not in self._shared_file_handlers:
                old_file.close()

    def _init_shared_console(self):
        """Initialize shared console handler."""
        if RICH_AVAILABLE:
            self._console = get_shared_console()

        self._console_handler = self._own(
            create_console_handler(
                use_color=self.use_color,
                use_rich=RICH_AVAILABLE,
                log_level=self.console_log_level,
                show_location=self.show_location,
                console=self._console,
            )
        )

    def _init_shared_file(self):
        """Initialize shared file handler(s)."""
        if self.shared_file:
            self._shared_file_handlers = [
                self._own(handler)
                for handler in create_file_handlers(
                    log_file=self.shared_file,
                    file_format=self.file_format,
                    mode=self.file_mode,
                    max_file_size=self.max_file_size,
                    backup_count=self.backup_count,
                    log_level=self.file_log_level,
                    show_location=self.show_location,
                )
            ]

    def _own(self, handler: logging.Handler) -> logging.Handler:
        """Add the manager's filters to a handler it creates.

        The context filter also sits on each managed logger, but a logger's
        filters only see records logged on that very logger. Records that
        propagate up from child loggers (the captured-package case) are seen
        by the handlers alone, so the handlers carry the filter too.

        Args:
            handler: Handler created by this manager

        Returns:
            The same handler
        """
        handler.addFilter(self._context_filter)
        return handler

    def capture(self, name: str) -> logging.Logger:
        """Send a standard library logger's records to the shared console and file.

        Meant for packages that log through ``logging.getLogger(__name__)``
        rather than through advlog: capturing the package name routes the
        records of all its modules here. Unlike register_logger(), the logger
        keeps its handlers and keeps propagating, so the host's own handlers
        (and pytest's ``caplog``) still receive the records. Its level is
        lowered to the lowest level the shared handlers accept, and restored
        by release().

        Args:
            name: Logger name, usually a top-level package ("mylib").
                  "" or "root" captures the root logger, i.e. every library.

        Returns:
            The captured logger

        Example:
            manager.capture("mylib")  # mylib.io, mylib.core, ... are all captured
        """
        return self._capture(name)

    def release(self, name: str) -> None:
        """Undo capture(): detach the shared handlers and restore the level.

        Args:
            name: Logger name passed to capture() (unknown names are ignored)
        """
        self._release(logging.getLogger(name).name)

    def get_captured(self) -> list[str]:
        """Get the names of the captured loggers.

        Returns:
            Logger names ("root" for the root logger)
        """
        return list(self._captured)

    def _capture(self, name: str, stale: Iterable[logging.Handler | None] = ()) -> logging.Logger:
        """Attach the current shared handlers to a logger, replacing stale ones."""
        logger = logging.getLogger(name)
        for handler in stale:
            if handler is not None and handler in logger.handlers:
                logger.removeHandler(handler)

        shared = [h for h in (self._console_handler, *self._shared_file_handlers) if h is not None]
        for handler in shared:
            if handler not in logger.handlers:
                logger.addHandler(handler)

        if logger.name not in self._captured:
            self._captured[logger.name] = logger.level
        if shared:
            logger.setLevel(min(h.level for h in shared))
        return logger

    def _release(self, name: str, stale: Iterable[logging.Handler | None] = ()) -> None:
        """Detach shared (current and stale) handlers from a captured logger."""
        if name not in self._captured:
            return
        logger = logging.getLogger(name)
        for handler in (self._console_handler, *self._shared_file_handlers, *stale):
            if handler is not None and handler in logger.handlers:
                logger.removeHandler(handler)
        logger.setLevel(self._captured.pop(name))

    def bind_context(self, **fields: Any) -> None:
        """Attach fields to every record of every managed logger.

        Bound fields behave like ``extra=`` passed on each call; an explicit
        ``extra=`` on a call wins over the bound value.

        Args:
            **fields: Field names and values (e.g. run_id="exp-42")

        Example:
            manager.bind_context(run_id="exp-42", git_sha="ab6e876")
        """
        self._context_filter.bind(**fields)

    def unbind_context(self, *keys: str) -> None:
        """Stop attaching the given context fields.

        Args:
            *keys: Field names to remove
        """
        self._context_filter.unbind(*keys)

    def clear_context(self) -> None:
        """Stop attaching any context fields."""
        self._context_filter.clear()

    def get_context(self) -> dict[str, Any]:
        """Get the currently bound context fields.

        Returns:
            Copy of the bound fields
        """
        return dict(self._context_filter.fields)

    def register_logger(
        self,
        name: str = "",
        log_level: int = logging.DEBUG,
        file_strategy: str = "separate",
        log_file: StrPath | None = None,
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

        # Clear any existing handlers and filters left by an earlier registration
        logger.handlers.clear()
        for old_filter in logger.filters[:]:
            if isinstance(old_filter, (ContextFilter, MainProcessFilter)):
                logger.removeFilter(old_filter)

        logger.addFilter(self._context_filter)
        if config is not None and config.use_accelerate:
            logger.addFilter(MainProcessFilter())

        # Add console handler
        if use_console and self.shared_console and self._console_handler:
            logger.addHandler(self._console_handler)
        elif use_console and not self.shared_console:
            use_color = self.use_color and (config is None or config.use_color)
            # Same color setting as the manager: draw on the shared console
            # (keeps progress bars intact). Otherwise the handler makes its own.
            console = get_shared_console() if RICH_AVAILABLE and use_color == self.use_color else None
            console_handler = create_console_handler(
                use_color=use_color,
                log_level=self.console_log_level,
                show_location=effective_show_location,
                enable_rich_tracebacks=config.enable_rich_tracebacks if config is not None else True,
                console=console,
            )
            logger.addHandler(self._own(console_handler))

        # Add file handler based on strategy
        if file_strategy == "separate" and log_file:
            # Per-logger file settings: config wins where it sets a value
            file_options: dict[str, Any] = {
                "file_format": self.file_format,
                "mode": "a",
                "max_file_size": self.max_file_size,
                "backup_count": self.backup_count,
            }
            if config is not None:
                file_options["mode"] = config.file_mode
                file_options["encoding"] = config.encoding
                file_options["date_format"] = config.date_format
                file_options["log_format"] = config.log_format
                for key in ("file_format", "max_file_size", "backup_count"):
                    if getattr(config, key) is not None:
                        file_options[key] = getattr(config, key)

            file_handlers = create_file_handlers(
                log_file=log_file,
                log_level=self.file_log_level,
                show_location=effective_show_location,
                **file_options,
            )
            for file_handler in file_handlers:
                logger.addHandler(self._own(file_handler))
        elif file_strategy == "merged":
            for file_handler in self._shared_file_handlers:
                logger.addHandler(file_handler)

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
        """Change file log level for shared file handler(s).

        Args:
            level: New log level
        """
        for handler in self._shared_file_handlers:
            handler.setLevel(level)

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
                if handler != self._console_handler and handler not in self._shared_file_handlers:
                    handlers_to_remove.append(handler)

            for handler in handlers_to_remove:
                logger.removeHandler(handler)
                handler.close()

            logger.removeFilter(self._context_filter)

            del self.loggers[name]

    def shutdown(self):
        """Shutdown all loggers and close handlers."""
        for name in list(self._captured):
            self._release(name)

        for logger in self.loggers.values():
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()
            logger.removeFilter(self._context_filter)

        self.loggers.clear()
        self._context_filter.clear()

        if self._console_handler:
            self._console_handler.close()
            self._console_handler = None

        for handler in self._shared_file_handlers:
            handler.close()
        self._shared_file_handlers = []

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
    shared_file: StrPath | None = None,
    file_strategy: str = "separate",
    log_dir: StrPath = "logs",
    use_color: bool = True,
    file_format: str = "text",
) -> dict[str, logging.Logger]:
    """Create a group of loggers with coordinated output.

    Args:
        module_names: List of module names
        shared_console: Share console output
        shared_file: Optional shared file path
        file_strategy: "separate", "merged", or "none"
        log_dir: Directory for separate log files
        use_color: Enable colored output
        file_format: "text", "json" (JSON Lines), or "both"

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
    manager = LoggerManager(
        shared_console=shared_console, shared_file=shared_file, use_color=use_color, file_format=file_format
    )

    loggers = {}
    for name in module_names:
        if file_strategy == "separate":
            log_file = f"{log_dir}/{name}.log"
        else:
            log_file = None

        loggers[name] = manager.register_logger(name=name, file_strategy=file_strategy, log_file=log_file)

    return loggers
