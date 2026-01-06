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
from typing import Dict, Optional


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
        datefmt: Optional[str] = None,
        log_colors: Optional[Dict[str, str]] = None,
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

    def __init__(self, fmt: str = "%(asctime)s [%(levelname)s] %(message)s", datefmt: Optional[str] = None):
        # Use default datefmt based on context or provided value
        if datefmt is None:
            # Try to determine if this is for console or file from the calling context
            # If not specified, use the shorter format
            datefmt = "%y/%m/%d %H:%M:%S"
        super().__init__(fmt, datefmt)


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
        self, fmt: Optional[str] = None, datefmt: Optional[str] = None, style: str = "%", indent_size: int = 27
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
        # Get the original log message
        message = super().format(record)

        # If the log message has multiple lines, indent each line
        lines = message.splitlines()
        if len(lines) > 1:
            indent = " " * self.indent_size
            # Add indentation to all lines after the first
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
        from datetime import datetime

        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra fields if requested
        if self.include_extras:
            # Add any extra fields that were passed to the log call
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


# === Aligned Formatters ===

class AlignedFormatter(logging.Formatter):
    """Formatter with precise field alignment control.

    Provides precise control over field width and alignment for clean,
    well-organized log output.

    Usage:
        formatter = AlignedFormatter(
            time_width=12,
            level_width=8,
            name_width=20,
            location_width=30,
            align_time="left",
            align_level="left",
            align_name="left",
            align_location="right"
        )
    """

    def __init__(
        self,
        # Field widths
        time_width: int = 12,
        level_width: int = 8,
        name_width: Optional[int] = None,
        location_width: Optional[int] = None,
        message_width: Optional[int] = None,
        # Alignment: "left", "right", "center"
        align_time: str = "left",
        align_level: str = "left",
        align_name: str = "left",
        align_location: str = "right",
        align_message: str = "left",
        # Separator
        separator: str = " | ",
        # Time format
        datefmt: str = "%H:%M:%S",
        # Whether to show each field
        show_time: bool = True,
        show_level: bool = True,
        show_name: bool = False,
        show_location: bool = True,
    ):
        """Initialize aligned formatter

        Args:
            time_width: Time field width
            level_width: Log level width
            name_width: Logger name width (None=unlimited)
            location_width: Source location width (None=unlimited)
            message_width: Message width (None=unlimited)
            align_time: Time alignment
            align_level: Level alignment
            align_name: Name alignment
            align_location: Location alignment
            align_message: Message alignment
            separator: Field separator
            datefmt: Time format
            show_time: Whether to show time
            show_level: Whether to show level
            show_name: Whether to show name
            show_location: Whether to show location
        """
        super().__init__(datefmt=datefmt)

        self.time_width = time_width
        self.level_width = level_width
        self.name_width = name_width
        self.location_width = location_width
        self.message_width = message_width

        self.align_time = align_time
        self.align_level = align_level
        self.align_name = align_name
        self.align_location = align_location
        self.align_message = align_message

        self.separator = separator

        self.show_time = show_time
        self.show_level = show_level
        self.show_name = show_name
        self.show_location = show_location

    def _align_field(self, text: str, width: Optional[int], align: str) -> str:
        """Align field

        Args:
            text: Text content
            width: Width (None=no alignment)
            align: Alignment method

        Returns:
            Aligned text
        """
        if width is None:
            return text

        # When text exceeds width, don't truncate, return original text
        if len(text) > width:
            return text

        if align == "left":
            return text.ljust(width)
        elif align == "right":
            return text.rjust(width)
        elif align == "center":
            return text.center(width)
        else:
            return text.ljust(width)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record"""
        parts = []

        # Time
        if self.show_time:
            time_str = self.formatTime(record, self.datefmt)
            time_str = self._align_field(time_str, self.time_width, self.align_time)
            parts.append(time_str)

        # Log level
        if self.show_level:
            level_str = self._align_field(record.levelname, self.level_width, self.align_level)
            parts.append(level_str)

        # Logger name
        if self.show_name:
            name_str = self._align_field(record.name, self.name_width, self.align_name)
            parts.append(name_str)

        # Source location
        if self.show_location:
            location = f"{record.filename}:{record.lineno}:{record.funcName}"
            location_str = self._align_field(location, self.location_width, self.align_location)
            parts.append(f"[{location_str}]")

        # Message
        message = record.getMessage()
        if self.message_width:
            message = self._align_field(message, self.message_width, self.align_message)
        parts.append(message)

        return self.separator.join(parts)


class TableFormatter(logging.Formatter):
    """Table formatter - outputs aligned log like a table.

    Usage:
        formatter = TableFormatter()
        # Output:
        # TIME       | LEVEL   | LOCATION                        | MESSAGE
        # 11:30:45   | INFO    | [demo.py:42:main]              | Starting process
        # 11:30:46   | WARNING | [process.py:128:validate]      | Validation failed
    """

    def __init__(
        self,
        time_width: int = 12,
        level_width: int = 8,
        location_width: int = 35,
        datefmt: str = "%H:%M:%S",
    ):
        """Initialize table formatter"""
        super().__init__(datefmt=datefmt)
        self.time_width = time_width
        self.level_width = level_width
        self.location_width = location_width
        self._header_printed = False

    def format(self, record: logging.LogRecord) -> str:
        """Format log record"""
        # Format fields
        time_str = self.formatTime(record, self.datefmt).ljust(self.time_width)
        level_str = record.levelname.ljust(self.level_width)

        location = f"{record.filename}:{record.lineno}:{record.funcName}"
        location_str = location.ljust(self.location_width)

        message = record.getMessage()

        # Combine output
        return f"{time_str} | {level_str} | [{location_str}] | {message}"


class CompactFormatter(logging.Formatter):
    """Compact formatter - optimized aligned compact format.

    Usage:
        formatter = CompactFormatter()
        # Output: [I] demo.py:42        | Processing data
        #      [W] validator.py:128  | Validation failed
    """

    def __init__(
        self,
        location_width: int = 25,
        datefmt: str = "%H:%M:%S",
    ):
        """Initialize compact formatter"""
        super().__init__(datefmt=datefmt)
        self.location_width = location_width

    def format(self, record: logging.LogRecord) -> str:
        """Format log record"""
        # Level (single character)
        level_char = record.levelname[0]

        # Location
        location = f"{record.filename}:{record.lineno}"
        location_str = location.ljust(self.location_width)

        message = record.getMessage()

        return f"[{level_char}] {location_str} | {message}"


class ColumnFormatter(logging.Formatter):
    """Column formatter - all fields aligned by columns.

    Supports dynamic column width adjustment to fit the longest content.

    Usage:
        formatter = ColumnFormatter(
            columns=["time", "level", "name", "location", "message"],
            widths={"time": 12, "level": 8, "name": 15, "location": 30}
        )
    """

    def __init__(
        self,
        columns: list = None,
        widths: dict = None,
        separator: str = " | ",
        datefmt: str = "%H:%M:%S",
    ):
        """Initialize column formatter

        Args:
            columns: Columns to show, optional: time, level, name, location, message
            widths: Width dictionary for each column
            separator: Column separator
            datefmt: Time format
        """
        super().__init__(datefmt=datefmt)

        if columns is None:
            columns = ["time", "level", "location", "message"]

        if widths is None:
            widths = {
                "time": 12,
                "level": 8,
                "name": 20,
                "location": 35,
                "message": None,  # None means no limit
            }

        self.columns = columns
        self.widths = widths
        self.separator = separator

    def format(self, record: logging.LogRecord) -> str:
        """Format log record"""
        parts = []

        for col in self.columns:
            width = self.widths.get(col)

            if col == "time":
                text = self.formatTime(record, self.datefmt)
            elif col == "level":
                text = record.levelname
            elif col == "name":
                text = record.name
            elif col == "location":
                text = f"[{record.filename}:{record.lineno}:{record.funcName}]"
            elif col == "message":
                text = record.getMessage()
            else:
                text = ""

            # Apply width
            if width is not None:
                text = text.ljust(width)

            parts.append(text)

        return self.separator.join(parts)


def create_aligned_formatter(style: str = "standard", **kwargs) -> logging.Formatter:
    """Create aligned formatter

    Args:
        style: Format style
            - "standard": Standard aligned format
            - "table": Table format
            - "compact": Compact format
            - "column": Column format
        **kwargs: Arguments passed to the specific formatter

    Returns:
        Formatter instance

    Example:
        # Standard format
        formatter = create_aligned_formatter("standard")

        # Table format
        formatter = create_aligned_formatter("table", time_width=15)

        # Compact format
        formatter = create_aligned_formatter("compact", location_width=30)
    """
    if style == "standard":
        return AlignedFormatter(**kwargs)
    elif style == "table":
        return TableFormatter(**kwargs)
    elif style == "compact":
        return CompactFormatter(**kwargs)
    elif style == "column":
        return ColumnFormatter(**kwargs)
    else:
        return AlignedFormatter(**kwargs)
