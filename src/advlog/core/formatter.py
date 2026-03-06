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

"""Custom formatters for log messages."""

import logging
from datetime import datetime
from typing import Literal

__all__ = [
    "RichColorFormatter",
    "PlainFormatter",
    "IndentedFormatter",
    "JSONFormatter",
]

# === Base Formatters ===


class RichColorFormatter(logging.Formatter):
    """Formatter that adds Rich markup for colored output.

    This formatter wraps log messages with Rich color markup tags
    based on the log level.

    Args:
        fmt: Format string for log messages
        datefmt: Date format string
        log_colors: Dictionary mapping log levels to Rich color names

    Example:
        formatter = RichColorFormatter(
            fmt="%(levelname)-8s %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold red",
            }
        )
    """

    def __init__(
        self,
        fmt: str = "%(levelname)-8s %(message)s",
        datefmt: str | None = None,
        log_colors: dict[str, str] | None = None,
    ):
        super().__init__(fmt, datefmt)
        self.log_colors = log_colors or {
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold red",
        }

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with color markup.

        Args:
            record: Log record to format

        Returns:
            Formatted log message with Rich color markup
        """
        message = super().format(record)

        color = self.log_colors.get(record.levelname, "")
        if color:
            message = f"[{color}]{message}[/{color}]"

        return message


class PlainFormatter(logging.Formatter):
    """Plain formatter without any color codes.

    This is useful for file output where color codes would be unreadable.

    Args:
        fmt: Format string for log messages
        datefmt: Date format string (defaults based on use case)

    Note:
        - For console output: defaults to yy/mm/dd HH:MM:SS
        - For file output: defaults to yyyy/mm/dd HH:MM:SS
    """

    def __init__(self, fmt: str = "%(asctime)s [%(levelname)s] %(message)s", datefmt: str | None = None):
        if datefmt is None:
            datefmt = "%y/%m/%d %H:%M:%S"
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as plain text.

        Args:
            record: Log record to format

        Returns:
            Formatted log message
        """
        return super().format(record)


class IndentedFormatter(logging.Formatter):
    """Formatter that indents multi-line log messages.

    For multi-line log messages, this formatter indents all lines after
    the first to align with the message content.

    Args:
        fmt: Format string for log messages
        datefmt: Date format string
        style: Format style ('%', '{', or '$')
        indent_size: Number of spaces to indent continuation lines

    Example:
        formatter = IndentedFormatter(
            fmt="%(asctime)s [%(levelname)s] %(message)s",
            indent_size=27
        )

        # Output:
        # 2024-01-01 12:00:00 [INFO] First line
        #                            Second line
        #                            Third line
    """

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        style: Literal["%", "{", "$"] = "%",
        indent_size: int = 27,
    ):
        super().__init__(fmt, datefmt, style)
        self.indent_size = indent_size

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with indentation for multi-line messages.

        Args:
            record: Log record to format

        Returns:
            Formatted log message with indented continuation lines
        """
        message = super().format(record)

        lines = message.splitlines()
        if len(lines) > 1:
            indent = " " * self.indent_size
            indented_message = lines[0] + "\n" + "\n".join(indent + line for line in lines[1:])
            return indented_message
        return message


class JSONFormatter(logging.Formatter):
    """Formatter that outputs log records as JSON.

    This is useful for structured logging and log aggregation systems.

    Args:
        include_extras: Whether to include extra fields from the log record

    Example:
        formatter = JSONFormatter(include_extras=True)
        # Output: {"time": "2024-01-01 12:00:00", "level": "INFO", "message": "test"}
    """

    def __init__(self, include_extras: bool = True):
        super().__init__()
        self.include_extras = include_extras

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log message
        """
        import json

        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if self.include_extras:
            for key, value in record.__dict__.items():
                if key not in [
                    "name",
                    "msg",
                    "args",
                    "created",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "module",
                    "msecs",
                    "message",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "thread",
                    "threadName",
                    "exc_info",
                    "exc_text",
                    "stack_info",
                ]:
                    log_data[key] = value

        return json.dumps(log_data, ensure_ascii=False)
