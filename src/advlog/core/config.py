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
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LoggerConfig:
    """Configuration for AdvancedLogger.

    Attributes:
        name: Logger name (used for multiple logger instances)
        log_file: Path to the main log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        file_mode: File opening mode ('w' for overwrite, 'a' for append)
        use_color: Enable colored console output
        console_output: Enable console output
        enable_progress: Enable progress bar support
        enable_rich_tracebacks: Enable rich formatted tracebacks
        max_file_size: Maximum log file size in bytes (for rotation)
        backup_count: Number of backup files to keep when rotating
        separate_error_file: Path to separate error log file
        date_format: Date format string for log messages
        log_format: Format string for log messages
        encoding: File encoding
        handlers: Custom handlers to add (advanced usage)

    Example:
        config = LoggerConfig(
            name="my_app",
            log_file="logs/app.log",
            log_level="INFO",
            use_color=True,
            separate_error_file="logs/error.log"
        )
    """

    # Basic settings
    name: str = "AppLogger"
    log_file: str = "logs/app.log"
    log_level: str = "INFO"
    file_mode: str = "w"

    # Feature toggles
    use_color: bool = True
    console_output: bool = True
    enable_progress: bool = True
    enable_rich_tracebacks: bool = True

    # File rotation
    max_file_size: Optional[int] = None  # bytes, None means no rotation
    backup_count: int = 3

    # Additional log files
    separate_error_file: Optional[str] = None
    separate_debug_file: Optional[str] = None

    # Formatting
    date_format: str = "%Y-%m-%d %H:%M:%S"
    log_format: str = "%(asctime)s [%(levelname)s] %(message)s"
    indent_size: int = 27
    encoding: str = "utf-8"

    # Advanced
    handlers: list = field(default_factory=list)
    propagate: bool = False

    # Environment-specific
    use_accelerate: bool = False  # For distributed training
    auto_detect_environment: bool = True

    def __post_init__(self):
        """Validate and normalize configuration."""
        self.log_level = self.log_level.upper()
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError(f"Invalid log level: {self.log_level}")

        # Auto-disable color in non-supporting environments
        if self.auto_detect_environment and self.use_color:
            try:
                from ..utils.environment import supports_color
            except ImportError:
                from utils.environment import supports_color
            if not supports_color():
                self.use_color = False

    def get_log_level(self) -> int:
        """Convert string log level to logging constant.

        Returns:
            Logging level constant (e.g., logging.INFO)
        """
        return getattr(logging, self.log_level)

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return {
            "name": self.name,
            "log_file": self.log_file,
            "log_level": self.log_level,
            "file_mode": self.file_mode,
            "use_color": self.use_color,
            "console_output": self.console_output,
            "enable_progress": self.enable_progress,
            "max_file_size": self.max_file_size,
            "backup_count": self.backup_count,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "LoggerConfig":
        """Create config from dictionary.

        Args:
            config_dict: Dictionary containing configuration values.

        Returns:
            LoggerConfig instance.
        """
        return cls(**config_dict)
