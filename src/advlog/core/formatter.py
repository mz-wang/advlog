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

import json
import logging
from datetime import datetime
from typing import Any, Literal

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


# Attributes logging itself puts on a record. Anything else came from ``extra=``.
# "message" and "asctime" are added by other formatters handling the same record;
# "taskName" only exists on Python 3.12+.
_RESERVED_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}


def _json_default(obj: Any) -> Any:
    """Convert values json cannot serialize natively.

    Args:
        obj: Value rejected by the JSON encoder

    Returns:
        A JSON-serializable stand-in
    """
    if isinstance(obj, (set, frozenset)):
        return list(obj)

    # numpy scalars/arrays and torch tensors
    tolist = getattr(obj, "tolist", None)
    if callable(tolist):
        try:
            return tolist()
        except Exception:
            pass

    return str(obj)


class JSONFormatter(logging.Formatter):
    """Formatter that outputs log records as JSON.

    This is useful for structured logging and log aggregation systems.
    Fields passed via ``extra=`` are collected under the ``"extra"`` key so
    they can never overwrite the standard fields. Non-finite floats (NaN,
    Infinity) are written as ``null`` to keep every line valid JSON.

    Args:
        include_extras: Whether to include extra fields from the log record

    Example:
        formatter = JSONFormatter(include_extras=True)
        logger.info("start", extra={"lr": 1e-3})
        # Output: {"timestamp": "2024-01-01T12:00:00+08:00", "level": "INFO", ...,
        #          "message": "start", "extra": {"lr": 0.001}}
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
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).astimezone().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_data["stack"] = self.formatStack(record.stack_info)

        if self.include_extras:
            extras = {key: value for key, value in record.__dict__.items() if key not in _RESERVED_ATTRS}
            if extras:
                log_data["extra"] = extras

        try:
            text = json.dumps(log_data, ensure_ascii=False, default=_json_default)
        except (TypeError, ValueError):
            # Unserializable keys or circular references: keep the record anyway
            log_data["extra"] = repr(log_data.get("extra"))
            text = json.dumps(log_data, ensure_ascii=False, default=_json_default)

        # NaN/Infinity are not valid JSON and make strict parsers reject the
        # line, so write them as null. The substring test only gates the
        # re-encode; a message that merely contains the word passes through intact.
        if "NaN" in text or "Infinity" in text:
            text = json.dumps(json.loads(text, parse_constant=lambda _: None), ensure_ascii=False)

        return text
