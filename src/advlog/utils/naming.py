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

"""Intelligent log file naming utilities."""

import os
from datetime import datetime
from typing import Optional

from .path import ensure_dir


class LogNamingStrategy:
    """Smart log file naming with timestamps and suffixes.

    Provides flexible naming strategies for log files to avoid conflicts
    and organize logs by time, module, and purpose.

    Example:
        # Basic timestamp naming
        name = LogNamingStrategy.timestamped("app")
        # Output: logs/20251028_103045_app.log

        # With custom suffix
        name = LogNamingStrategy.timestamped("app", suffix="training")
        # Output: logs/20251028_103045_app_training.log

        # Date-based directory structure
        name = LogNamingStrategy.daily("app")
        # Output: logs/2025-10-28/app.log
    """

    @staticmethod
    def timestamped(
        name: str,
        suffix: Optional[str] = None,
        directory: str = "logs",
        timestamp_format: str = "%Y%m%d_%H%M%S",
        extension: str = ".log",
        use_date_dir: bool = True,
    ) -> str:
        """Generate timestamped log file name.

        Args:
            name: Base name for the log file
            suffix: Optional suffix to add (e.g., "training", "debug")
            directory: Directory to store log files
            timestamp_format: Format string for timestamp
            extension: File extension (default: .log)
            use_date_dir: Whether to organize logs into date directories (yyyy-mm-dd)
                         Default: True (always enabled as per user requirement)

        Returns:
            Full path to the log file

        Example:
            >>> LogNamingStrategy.timestamped("app", suffix="train")
            'logs/2025-01-01/20250101_103045_app_train.log'

            >>> LogNamingStrategy.timestamped("app", use_date_dir=False)
            'logs/20250101_103045_app.log'
        """
        if use_date_dir:
            # Enable date directory structure by default (yyyy-mm-dd)
            date_dir = datetime.now().strftime("%Y-%m-%d")
            directory = os.path.join(directory, date_dir)

        timestamp = datetime.now().strftime(timestamp_format)

        if suffix:
            filename = f"{timestamp}_{name}_{suffix}{extension}"
        else:
            filename = f"{timestamp}_{name}{extension}"

        return os.path.join(directory, filename)

    @staticmethod
    def daily(
        name: str,
        suffix: Optional[str] = None,
        base_directory: str = "logs",
        date_format: str = "%Y-%m-%d",
        extension: str = ".log",
    ) -> str:
        """Generate log file name with daily directory structure.

        Organizes logs into daily subdirectories.

        Args:
            name: Base name for the log file
            suffix: Optional suffix to add
            base_directory: Base directory for logs
            date_format: Format for date directory name
            extension: File extension

        Returns:
            Full path to the log file

        Example:
            >>> LogNamingStrategy.daily("app", suffix="error")
            'logs/2025-10-28/app_error.log'
        """
        date_dir = datetime.now().strftime(date_format)
        directory = os.path.join(base_directory, date_dir)

        if suffix:
            filename = f"{name}_{suffix}{extension}"
        else:
            filename = f"{name}{extension}"

        return os.path.join(directory, filename)

    @staticmethod
    def hourly(
        name: str,
        suffix: Optional[str] = None,
        base_directory: str = "logs",
        datetime_format: str = "%Y-%m-%d/%H",
        extension: str = ".log",
    ) -> str:
        """Generate log file name with hourly directory structure.

        Organizes logs into date/hour subdirectories.

        Args:
            name: Base name for the log file
            suffix: Optional suffix to add
            base_directory: Base directory for logs
            datetime_format: Format for datetime directory structure
            extension: File extension

        Returns:
            Full path to the log file

        Example:
            >>> LogNamingStrategy.hourly("app")
            'logs/2025-10-28/10/app.log'
        """
        datetime_dir = datetime.now().strftime(datetime_format)
        directory = os.path.join(base_directory, datetime_dir)

        if suffix:
            filename = f"{name}_{suffix}{extension}"
        else:
            filename = f"{name}{extension}"

        return os.path.join(directory, filename)

    @staticmethod
    def incremental(
        name: str,
        suffix: Optional[str] = None,
        directory: str = "logs",
        extension: str = ".log",
        max_attempts: int = 1000,
    ) -> str:
        """Generate log file name with incremental numbering.

        If file exists, adds a number suffix (1, 2, 3...) to avoid conflicts.

        Args:
            name: Base name for the log file
            suffix: Optional suffix to add
            directory: Directory to store log files
            extension: File extension
            max_attempts: Maximum number of attempts to find available name

        Returns:
            Full path to the log file

        Example:
            >>> LogNamingStrategy.incremental("app")
            'logs/app.log'  # or app_1.log if app.log exists
        """
        ensure_dir(directory)

        # Try base name first
        if suffix:
            base_filename = f"{name}_{suffix}"
        else:
            base_filename = name

        filepath = os.path.join(directory, f"{base_filename}{extension}")

        if not os.path.exists(filepath):
            return filepath

        # Try numbered versions
        for i in range(1, max_attempts):
            filepath = os.path.join(directory, f"{base_filename}_{i}{extension}")
            if not os.path.exists(filepath):
                return filepath

        # Fallback to timestamp if all numbered versions exist
        return LogNamingStrategy.timestamped(name, suffix, directory, extension=extension)

    @staticmethod
    def session_based(
        name: str,
        session_id: Optional[str] = None,
        suffix: Optional[str] = None,
        directory: str = "logs",
        extension: str = ".log",
    ) -> str:
        """Generate log file name with session ID.

        Useful for tracking logs across a specific session or run.

        Args:
            name: Base name for the log file
            session_id: Session identifier (auto-generated if None)
            suffix: Optional suffix to add
            directory: Directory to store log files
            extension: File extension

        Returns:
            Full path to the log file

        Example:
            >>> LogNamingStrategy.session_based("app", "abc123")
            'logs/app_session_abc123.log'
        """
        if session_id is None:
            # Generate session ID from timestamp
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        parts = [name, "session", session_id]
        if suffix:
            parts.append(suffix)

        filename = "_".join(parts) + extension
        return os.path.join(directory, filename)


def get_timestamped_name(name: str, suffix: Optional[str] = None, strategy: str = "timestamped") -> str:
    """Convenience function to get a timestamped log file name.

    Args:
        name: Base name
        suffix: Optional suffix
        strategy: Naming strategy ("timestamped", "daily", "hourly", "incremental")

    Returns:
        Log file path

    Example:
        >>> get_timestamped_name("myapp", "training")
        'logs/20251028_103045_myapp_training.log'
    """
    strategies = {
        "timestamped": LogNamingStrategy.timestamped,
        "daily": LogNamingStrategy.daily,
        "hourly": LogNamingStrategy.hourly,
        "incremental": LogNamingStrategy.incremental,
    }

    strategy_func = strategies.get(strategy, LogNamingStrategy.timestamped)
    return strategy_func(name, suffix)
