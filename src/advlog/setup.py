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
Global logging setup module.

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
from typing import Optional

from advlog.core import LoggerManager
from advlog.plugins import ProgressTracker
from advlog.utils import LogNamingStrategy

# Try to import Rich for console detection
try:
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Global singleton instances
_LOGGER_MANAGER: Optional[LoggerManager] = None
_PROGRESS_TRACKER: Optional[ProgressTracker] = None
_INITIALIZED: bool = False
_INIT_CONFIG: dict = {}


def _should_force_terminal_width() -> bool:
    """
    Determine if we should force a wide console for file output.

    Returns True when output is being redirected to a file (non-interactive),
    so Rich uses a wide width instead of narrow terminal detection.
    """
    return not sys.stdout.isatty()


def initialize(
    output_dir: str = "./logs",
    session_name: str = "app",
    log_level: str = "INFO",
    use_color: bool = True,
    enable_file_logging: bool = True,
    show_location: bool = False,
    file_mode: str = "a",
    log_file: Optional[str] = None,
) -> LoggerManager:
    """
    Initialize the global logging system.

    This should be called once at application startup. If not called explicitly,
    get_logger() will auto-initialize with default settings.

    Args:
        output_dir: Directory for log files
        session_name: Name prefix for log files (ignored if log_file is provided)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_color: Enable colored console output
        enable_file_logging: Enable file logging
        show_location: Show source location (file:line) in console sidebar
        file_mode: File opening mode ('w' for overwrite, 'a' for append/continue)
                   Default is 'a' (append), which allows breakpoint continue.
                   If file doesn't exist, it will be created automatically.
        log_file: Specific log file path. If provided, overrides session_name-based naming.
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
        ...     log_file="./logs/reconstruction.log",  # Target specific file
        ...     file_mode="a"  # Append to this file
        ... )
        >>> # Force overwrite mode
        >>> manager = initialize(
        ...     session_name="reconstruction",
        ...     file_mode="w"  # Overwrite existing log file
        ... )
    """
    global _LOGGER_MANAGER, _INITIALIZED, _INIT_CONFIG

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

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
        if log_file:
            # Use the specified log file path (for breakpoint continue)
            shared_file = log_file
            # Ensure the directory exists
            os.makedirs(os.path.dirname(shared_file), exist_ok=True)
        else:
            # Auto-generate filename with timestamp
            log_filename = LogNamingStrategy.timestamped(session_name)
            shared_file = os.path.join(output_dir, log_filename)
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
        "log_level": log_level,
        "use_color": use_color,
        "enable_file_logging": enable_file_logging,
        "show_location": show_location,
        "file_mode": file_mode,
        "log_file": log_file,
    }

    _INITIALIZED = True
    return _LOGGER_MANAGER


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get or create a logger for a specific module.

    Auto-initializes the global logging system if not already done.

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

    # Auto-initialize if not done
    if not _INITIALIZED:
        initialize()

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
    kwargs = {
        "name": name,
        "file_strategy": "merged",
    }
    if level_int is not None:
        kwargs["log_level"] = level_int

    logger = _LOGGER_MANAGER.register_logger(**kwargs)

    return logger


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


# Export public API
__all__ = [
    "initialize",
    "get_logger",
    "get_progress",
    "reset",
]
