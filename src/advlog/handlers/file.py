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

"""File handlers for logging to files."""

import logging
from logging.handlers import RotatingFileHandler as StdRotatingFileHandler
from typing import Optional

from advlog.utils.path import ensure_dir


class FileHandler:
    """Factory for creating file handlers.

    This class creates file handlers with appropriate formatters
    and handles directory creation.
    """

    @staticmethod
    def create(
        log_file: str,
        mode: str = "w",
        encoding: str = "utf-8",
        log_level: int = logging.DEBUG,
        use_indented_format: bool = True,
        show_location: bool = False,
        location_width: int = 50,
        indent_size: int = 27,
        date_format: str = "%Y-%m-%d %H:%M:%S",
        log_format: str = "%(asctime)s [%(levelname)s] %(message)s",
        use_json_format: bool = False,
    ) -> logging.Handler:
        """Create a file handler.

        Args:
            log_file: Path to the log file
            mode: File opening mode ('w' for overwrite, 'a' for append)
            encoding: File encoding
            log_level: Minimum log level to handle
            use_indented_format: Use indented formatter for multi-line messages
            show_location: Include source location (file:line) in log
            location_width: Width for location field alignment (default 50)
            indent_size: Indentation size for continuation lines
            date_format: Date format string
            log_format: Log message format string
            use_json_format: Output logs as JSON instead

        Returns:
            Configured file handler
        """
        # Lazy import formatters to avoid circular imports
        from advlog.core.formatter import IndentedFormatter, JSONFormatter, PlainFormatter, AlignedFormatter

        # Create directory if it doesn't exist
        if log_file:
            ensure_dir(log_file)

        # Create handler
        handler = logging.FileHandler(log_file, mode=mode, encoding=encoding)

        # Choose formatter
        if use_json_format:
            formatter = JSONFormatter()
        elif show_location and use_indented_format:
            # Use AlignedFormatter for better location alignment
            # File format: yyyy/mm/dd hh:mm:ss (long format)
            formatter = AlignedFormatter(
                time_width=19,  # yyyy/mm/dd hh:mm:ss
                level_width=8,
                location_width=location_width,
                align_time="left",
                align_level="left",
                align_location="right",
                datefmt="%Y/%m/%d %H:%M:%S",
            )
        elif use_indented_format:
            formatter = IndentedFormatter(fmt=log_format, datefmt=date_format, indent_size=indent_size)
        else:
            if show_location:
                formatter = PlainFormatter(fmt=f"{log_format} (%(pathname)s:%(lineno)d)", datefmt=date_format)
            else:
                formatter = PlainFormatter(fmt=log_format, datefmt=date_format)

        handler.setFormatter(formatter)
        handler.setLevel(log_level)

        return handler


class RotatingFileHandler:
    """Factory for creating rotating file handlers.

    This handler automatically rotates log files when they reach
    a certain size, keeping a specified number of backup files.
    """

    @staticmethod
    def create(
        log_file: str,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        encoding: str = "utf-8",
        log_level: int = logging.DEBUG,
        use_indented_format: bool = True,
        show_location: bool = False,
        location_width: int = 50,
        indent_size: int = 27,
        date_format: str = "%Y-%m-%d %H:%M:%S",
        log_format: str = "%(asctime)s [%(levelname)s] %(message)s",
    ) -> logging.Handler:
        """Create a rotating file handler.

        Args:
            log_file: Path to the log file
            max_bytes: Maximum file size before rotation
            backup_count: Number of backup files to keep
            encoding: File encoding
            log_level: Minimum log level to handle
            use_indented_format: Use indented formatter for multi-line messages
            show_location: Include source location (file:line) in log
            location_width: Width for location field alignment (default 50)
            indent_size: Indentation size for continuation lines
            date_format: Date format string
            log_format: Log message format string

        Returns:
            Configured rotating file handler
        """
        # Lazy import formatters to avoid circular imports
        from advlog.core.formatter import IndentedFormatter, PlainFormatter, AlignedFormatter

        # Create directory if it doesn't exist
        ensure_dir(log_file)

        # Create handler
        handler = StdRotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count, encoding=encoding)

        # Choose formatter
        if show_location and use_indented_format:
            # Use AlignedFormatter for better location alignment
            # File format: yyyy/mm/dd hh:mm:ss (long format)
            formatter = AlignedFormatter(
                time_width=19,  # yyyy/mm/dd hh:mm:ss
                level_width=8,
                location_width=location_width,
                align_time="left",
                align_level="left",
                align_location="right",
                datefmt="%Y/%m/%d %H:%M:%S",
            )
        elif use_indented_format:
            formatter = IndentedFormatter(fmt=log_format, datefmt=date_format, indent_size=indent_size)
        else:
            if show_location:
                formatter = PlainFormatter(fmt=f"{log_format} (%(pathname)s:%(lineno)d)", datefmt=date_format)
            else:
                formatter = PlainFormatter(fmt=log_format, datefmt=date_format)

        handler.setFormatter(formatter)
        handler.setLevel(log_level)

        return handler


def create_file_handler(
    log_file: str, mode: str = "w", max_file_size: Optional[int] = None, backup_count: int = 5, **kwargs
) -> logging.Handler:
    """Convenience function to create a file handler.

    This function automatically chooses between a regular file handler
    and a rotating file handler based on the max_file_size parameter.

    Args:
        log_file: Path to the log file
        mode: File opening mode ('w' or 'a')
        max_file_size: Maximum file size in bytes (None = no rotation)
        backup_count: Number of backup files to keep
        **kwargs: Additional arguments passed to handler creation

    Returns:
        Configured file handler

    Example:
        # Regular file handler
        handler = create_file_handler("app.log", mode="a")

        # Rotating file handler (10 MB max)
        handler = create_file_handler("app.log", max_file_size=10*1024*1024)
    """
    if max_file_size:
        return RotatingFileHandler.create(
            log_file=log_file, max_bytes=max_file_size, backup_count=backup_count, **kwargs
        )
    else:
        return FileHandler.create(log_file=log_file, mode=mode, **kwargs)
