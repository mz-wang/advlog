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
from dataclasses import dataclass
from typing import Any


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
        use_color: Enable colored console output
        console_output: Enable console output
        enable_rich_tracebacks: Enable rich formatted tracebacks
        show_location: Show source file/line in console sidebar
        date_format: Date format string for file log messages
        log_format: Format string for file log messages
        encoding: File encoding
        propagate: Whether log records propagate to the root logger
        use_accelerate: Suppress output on non-main processes (distributed training)

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
    log_file: str | None = None
    log_level: str = "INFO"
    file_mode: str = "a"

    # Console behaviour
    use_color: bool = True
    console_output: bool = True
    enable_rich_tracebacks: bool = True
    show_location: bool = False

    # File formatting
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_format: str = "%(asctime)s [%(levelname)s] %(message)s"
    encoding: str = "utf-8"

    # Misc
    propagate: bool = False
    use_accelerate: bool = False  # For distributed training

    def __post_init__(self):
        """Validate and normalize configuration."""
        self.log_level = self.log_level.upper()
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log level: {self.log_level}")

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
        return {
            "name": self.name,
            "log_file": self.log_file,
            "log_level": self.log_level,
            "file_mode": self.file_mode,
            "use_color": self.use_color,
            "console_output": self.console_output,
            "show_location": self.show_location,
            "propagate": self.propagate,
        }

    @classmethod
    def from_dict(cls, config_dict: dict[str, Any]) -> "LoggerConfig":
        """Create config from dictionary."""
        return cls(**config_dict)
