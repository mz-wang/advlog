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

"""Configuration management for the logging system."""

import logging
from dataclasses import asdict, dataclass
from typing import Any

from advlog.handlers.file import DEFAULT_DATE_FORMAT, DEFAULT_LOG_FORMAT
from advlog.utils.path import StrPath


@dataclass
class LoggerConfig:
    """Configuration for LoggerManager.register_logger().

    Provides fine-grained per-logger control. Pass as the ``config`` argument
    to ``LoggerManager.register_logger()`` to override the manager's defaults
    for that specific logger.

    Attributes:
        name: Logger name (module name or custom identifier)
        log_file: Path to an individual log file for this logger
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        file_mode: File opening mode ('w' for overwrite, 'a' for append)
        file_format: "text", "json" (JSON Lines), or "both". None inherits
                     the manager's setting.
        max_file_size: Rotate the log file when it reaches this many bytes.
                       None inherits the manager's setting.
        backup_count: Number of rotated files to keep. None inherits the
                      manager's setting.
        use_color: Enable colored console output. Applies only when the
                   manager does not use a shared console (a shared console
                   has one color setting for everyone).
        console_output: Enable console output
        enable_rich_tracebacks: Enable rich formatted tracebacks. Applies only
                                when the manager does not use a shared console.
        show_location: Show source file/line in console sidebar
        date_format: Date format string for this logger's own log file
        log_format: Format string for this logger's own log file
        encoding: Encoding of this logger's own log file
        propagate: Whether log records propagate to the root logger
        use_accelerate: Suppress output on non-main processes of an
                        ``accelerate`` run (distributed training)

    The file settings (``file_mode``, ``file_format``, ``max_file_size``,
    ``backup_count``, ``date_format``, ``log_format``, ``encoding``) apply to
    the file named by ``log_file``; without ``log_file`` the logger has no
    file of its own.

    Example:
        config = LoggerConfig(
            name="my_module",
            log_file="logs/my_module.log",
            log_level="DEBUG",
            show_location=True,
        )
        logger = manager.register_logger(config=config)
    """

    # Identity & file
    name: str = "AppLogger"
    log_file: StrPath | None = None
    log_level: str = "INFO"
    file_mode: str = "a"
    file_format: str | None = None
    max_file_size: int | None = None
    backup_count: int | None = None

    # Console behaviour
    use_color: bool = True
    console_output: bool = True
    enable_rich_tracebacks: bool = True
    show_location: bool = False

    # File formatting
    date_format: str = DEFAULT_DATE_FORMAT
    log_format: str = DEFAULT_LOG_FORMAT
    encoding: str = "utf-8"

    # Misc
    propagate: bool = False
    use_accelerate: bool = False  # For distributed training

    def __post_init__(self):
        """Validate and normalize configuration."""
        self.log_level = self.log_level.upper()
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log level: {self.log_level}")

        if self.file_format is not None and self.file_format not in ["text", "json", "both"]:
            raise ValueError(f"Invalid file format: {self.file_format}")

        if self.use_color:
            from advlog.utils.environment import supports_color

            if not supports_color():
                self.use_color = False

    def get_log_level(self) -> int:
        """Convert string log level to logging constant.

        Returns:
            Logging level constant (e.g., logging.INFO)
        """
        return getattr(logging, self.log_level)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "LoggerConfig":
        """Create config from dictionary."""
        return cls(**config_dict)
