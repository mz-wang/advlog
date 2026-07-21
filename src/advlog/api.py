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

"""
Global logging API module.

Provides singleton-based global logging management for easy cross-module usage.
This module simplifies external project integration by providing a simple API
for initializing and using loggers across multiple modules.

Usage:
    # Simple usage (auto-initializes with defaults)
    from advlog import get_logger
    log = get_logger(__name__)
    log.info("Hello world")

    # With explicit initialization
    from advlog import initialize, get_logger, get_progress
    initialize(output_dir="./logs", session_name="myapp", log_level="DEBUG")
    log = get_logger(__name__)
    progress = get_progress()
"""

import logging
import os
import sys

from advlog.core import LoggerManager
from advlog.plugins import ProgressTracker
from advlog.utils import LogNamingStrategy

# Global singleton instances
_LOGGER_MANAGER: LoggerManager | None = None
_PROGRESS_TRACKER: ProgressTracker | None = None
_INITIALIZED: bool = False
_INIT_CONFIG: dict = {}


def initialize(
    output_dir: str = "./logs",
    use_date_dir: bool = True,
    session_name: str = "app",
    suffix: str | None = None,
    log_level: str = "INFO",
    use_color: bool = True,
    enable_file_logging: bool = True,
    show_location: bool = False,
    file_mode: str = "a",
    log_file_path: str | None = None,
) -> LoggerManager:
    """
    Initialize the global logging system.

    This should be called once at application startup. If not called explicitly,
    get_logger() will auto-initialize with default settings.

    Args:
        output_dir: Directory for log files. Ignored if log_file_path is provided.
        use_date_dir: Whether to create a subdirectory with the current date (YYYY-MM-DD).
        session_name: Name prefix for log files. Ignored if log_file_path is provided.
        suffix: Optional suffix to append to the log filename. Ignored if log_file_path is provided.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_color: Enable colored console output
        enable_file_logging: Enable file logging
        show_location: Show source location (file:line) in console sidebar
        file_mode: File opening mode ('w' for overwrite, 'a' for append/continue)
                   Default is 'a' (append), which allows breakpoint continue.
                   If file doesn't exist, it will be created automatically.
        log_file_path: Specific log file path. If provided, it will COMPLETELY OVERRIDE
                       output_dir, session_name and suffix related naming logic.
                       This is essential for breakpoint continue - specify the exact file to append to.

    Returns:
        LoggerManager instance

    Example:
        >>> from advlog import initialize
        >>> # Normal usage (auto-generate filename with timestamp)
        >>> manager = initialize(
        ...     output_dir="./results/logs",
        ...     session_name="reconstruction",
        ...     log_level="DEBUG",
        ...     show_location=True
        ... )
        >>> # Breakpoint continue (specify exact file to append to)
        >>> manager = initialize(
        ...     log_file_path="./logs/reconstruction.log",  # Target specific file
        ...     file_mode="a"  # Append to this file
        ... )
        >>> # Force overwrite mode
        >>> manager = initialize(
        ...     session_name="reconstruction",
        ...     file_mode="w"  # Overwrite existing log file
        ... )
    """
    global _LOGGER_MANAGER, _INITIALIZED, _INIT_CONFIG

    # Convert log level string to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level_int = level_map.get(log_level.upper(), logging.INFO)

    # Create main log file path if file logging is enabled
    shared_file = None
    if enable_file_logging:
        if log_file_path:
            # Use the specified log file path (for breakpoint continue)
            # This COMPLETELY overrides output_dir and session_name
            shared_file = log_file_path
            # Ensure the directory exists
            log_dir = os.path.dirname(os.path.abspath(shared_file))
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
        else:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Auto-generate filename with timestamp
            # Pass directory and suffix to the naming strategy
            shared_file = LogNamingStrategy.timestamped(
                name=session_name, suffix=suffix, directory=output_dir, use_date_dir=use_date_dir
            )
            # Ensure the date directory exists
            os.makedirs(os.path.dirname(shared_file), exist_ok=True)

    # Initialize logger manager
    _LOGGER_MANAGER = LoggerManager(
        shared_console=True,
        shared_file=shared_file,
        console_log_level=log_level_int,
        file_log_level=logging.DEBUG,
        use_color=use_color,
        show_location=show_location,
        file_mode=file_mode,
    )

    # Store configuration for later reference
    _INIT_CONFIG = {
        "output_dir": output_dir,
        "session_name": session_name,
        "suffix": suffix,
        "log_level": log_level,
        "use_color": use_color,
        "enable_file_logging": enable_file_logging,
        "show_location": show_location,
        "file_mode": file_mode,
        "log_file_path": log_file_path,
    }

    _INITIALIZED = True
    return _LOGGER_MANAGER


def get_logger(name: str, log_level: str | None = None) -> logging.Logger:
    """
    Get or create a logger for a specific module.

    Auto-initializes the global logging system if not already done. This
    implicit initialization is console-only; no log file is created until
    initialize() is called explicitly. This avoids creating a stray log file
    in the current working directory before the application has configured its
    output location.

    Args:
        name: Name of the module (typically __name__)
        log_level: Optional override for log level

    Returns:
        Configured logging.Logger instance

    Example:
        >>> from advlog import get_logger
        >>> log = get_logger(__name__)
        >>> log.info("Hello world")
    """
    global _LOGGER_MANAGER, _INITIALIZED

    # Auto-initialize if not done.
    # Implicit auto-init is console-only: at this point the application has not
    # yet told us where log files should live, so writing one into the current
    # working directory (the project root) would be wrong. File logging is
    # enabled later, when the application calls initialize() explicitly, which
    # re-attaches a shared file handler to loggers registered during this phase.
    if not _INITIALIZED:
        initialize(enable_file_logging=False)

    # Convert log level if provided
    level_int = None
    if log_level:
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        level_int = level_map.get(log_level.upper(), None)

    # Register logger with the manager
    # Only pass log_level if explicitly specified
    assert _LOGGER_MANAGER is not None

    if level_int is not None:
        return _LOGGER_MANAGER.register_logger(
            name=name,
            file_strategy="merged",
            log_level=level_int,
        )

    return _LOGGER_MANAGER.register_logger(
        name=name,
        file_strategy="merged",
    )


def get_progress() -> ProgressTracker:
    """
    Get the global ProgressTracker instance.

    Returns:
        ProgressTracker instance (singleton)

    Example:
        >>> from advlog import get_progress
        >>> progress = get_progress()
        >>> with progress.get_progress():
        ...     task = progress.add_task("Processing", total=100)
        ...     for i in range(100):
        ...         progress.update(task, advance=1)
    """
    global _PROGRESS_TRACKER

    if _PROGRESS_TRACKER is None:
        _PROGRESS_TRACKER = ProgressTracker()

    return _PROGRESS_TRACKER


def reset():
    """
    Reset the global logging system.

    This is mainly useful for testing. It clears all global state and
    allows re-initialization with different settings.
    """
    global _LOGGER_MANAGER, _PROGRESS_TRACKER, _INITIALIZED, _INIT_CONFIG

    if _LOGGER_MANAGER is not None:
        _LOGGER_MANAGER.shutdown()

    _LOGGER_MANAGER = None
    _PROGRESS_TRACKER = None
    _INITIALIZED = False
    _INIT_CONFIG = {}


def setup_exception_logging(logger: logging.Logger | None = None) -> None:
    """Install a global handler to log uncaught exceptions.

    Args:
        logger: Logger to use. Defaults to ``logging.getLogger("advlog")``.

    Example:
        >>> from advlog import setup_exception_logging
        >>> setup_exception_logging()
    """
    if logger is None:
        logger = logging.getLogger("advlog")

    def _log_uncaught(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
        else:
            logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    sys.excepthook = _log_uncaught


# Export public API
__all__ = [
    "initialize",
    "get_logger",
    "get_progress",
    "reset",
    "setup_exception_logging",
]
