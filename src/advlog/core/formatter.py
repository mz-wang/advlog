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
import re
from datetime import datetime
from functools import lru_cache
from typing import Any, Literal

__all__ = [
    "RichColorFormatter",
    "PlainFormatter",
    "IndentedFormatter",
    "JSONFormatter",
]

# === Rich markup handling ===

# An opening tag ([bold red]) or a closing tag ([/bold red], [/]), as Rich parses them
_MARKUP_TAG = re.compile(r"\[(?:(/)([^\[\]]*)|([a-z#@][^\[\]]*))\]")


@lru_cache(maxsize=256)
def _is_rich_style(name: str) -> bool:
    """Check whether a markup tag name is something Rich would render as a style.

    Args:
        name: Tag content without the brackets (e.g. "bold red")

    Returns:
        True if Rich treats the tag as styling rather than text
    """
    if name.startswith("@") or name.split("=", 1)[0].strip() == "link":
        return True

    try:
        from rich.style import Style

        Style.parse(name)
    except Exception:
        return False
    return True


def strip_rich_markup(text: str) -> str:
    """Remove Rich style tags from a message so files hold what the console shows.

    Only tags that come in pairs are removed (``[bold]x[/bold]``, ``[red]x[/]``).
    A lone bracketed word such as ``arr[i]`` or ``[epoch 1]`` is left alone, so
    ordinary text is never lost.

    Args:
        text: Message that may contain Rich markup

    Returns:
        Message without paired style tags
    """
    if "[/" not in text:
        return text

    open_tags: list[tuple[str, re.Match[str]]] = []
    paired: list[re.Match[str]] = []

    for match in _MARKUP_TAG.finditer(text):
        if match.start() > 0 and text[match.start() - 1] == "\\":
            continue  # escaped bracket, literal text

        if match.group(1) is None:
            name = match.group(3).strip()
            if _is_rich_style(name):
                # [link=url] is closed by [/link]
                open_tags.append((name.split("=", 1)[0].strip(), match))
            continue

        name = match.group(2).strip()
        for index in range(len(open_tags) - 1, -1, -1):
            # A bare [/] closes the most recent tag
            if not name or open_tags[index][0] == name:
                paired += [open_tags.pop(index)[1], match]
                break

    if not paired:
        return text

    parts = []
    position = 0
    for match in sorted(paired, key=lambda m: m.start()):
        parts.append(text[position : match.start()])
        position = match.end()
    parts.append(text[position:])
    return "".join(parts)


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
        strip_markup: Remove paired Rich style tags from the message

    Note:
        - For console output: defaults to yy/mm/dd HH:MM:SS
        - For file output: defaults to yyyy/mm/dd HH:MM:SS
    """

    def __init__(
        self,
        fmt: str = "%(asctime)s [%(levelname)s] %(message)s",
        datefmt: str | None = None,
        strip_markup: bool = False,
    ):
        if datefmt is None:
            datefmt = "%y/%m/%d %H:%M:%S"
        super().__init__(fmt, datefmt)
        self.strip_markup = strip_markup

    def formatMessage(self, record: logging.LogRecord) -> str:
        """Render the format string, stripping Rich markup first if enabled."""
        if self.strip_markup:
            record.message = strip_rich_markup(record.message)
        return super().formatMessage(record)

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
        strip_markup: Remove paired Rich style tags from the message

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
        strip_markup: bool = False,
    ):
        super().__init__(fmt, datefmt, style)
        self.indent_size = indent_size
        self.strip_markup = strip_markup

    def formatMessage(self, record: logging.LogRecord) -> str:
        """Render the format string, stripping Rich markup first if enabled."""
        if self.strip_markup:
            record.message = strip_rich_markup(record.message)
        return super().formatMessage(record)

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
RESERVED_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "taskName",
}


DEFAULT_MAX_ARRAY_SIZE = 1000


def _element_count(obj: Any) -> int | None:
    """Count the elements of an array-like object without converting it.

    Args:
        obj: numpy array, torch tensor, pandas Series, ...

    Returns:
        Number of elements, or None if the object does not say
    """
    numel = getattr(obj, "numel", None)  # torch: .size is a method, .numel() the count
    if callable(numel):
        try:
            return int(numel())
        except Exception:
            return None

    size = getattr(obj, "size", None)  # numpy, pandas
    return size if isinstance(size, int) else None


def _is_complex_array(obj: Any) -> bool:
    """Check for a complex numpy array/scalar or torch tensor without importing either."""
    dtype = getattr(obj, "dtype", None)
    return getattr(dtype, "kind", None) == "c" or getattr(dtype, "is_complex", False) is True


def _json_default(obj: Any, max_array_size: int | None = None) -> Any:
    """Convert values json cannot serialize natively.

    Args:
        obj: Value rejected by the JSON encoder
        max_array_size: Arrays with more elements than this are replaced by a
                        summary (shape, dtype, size). None writes them in full.

    Returns:
        A JSON-serializable stand-in
    """
    if isinstance(obj, (set, frozenset)):
        return list(obj)

    # Also numpy.complex128, a subclass of complex
    if isinstance(obj, complex):
        return {"real": obj.real, "imag": obj.imag}

    # numpy scalars/arrays and torch tensors
    tolist = getattr(obj, "tolist", None)
    if callable(tolist):
        if max_array_size is not None:
            size = _element_count(obj)
            if size is not None and size > max_array_size:
                shape = getattr(obj, "shape", None)
                return {
                    "_type": "array_summary",
                    "shape": list(shape) if shape is not None else None,
                    "dtype": str(getattr(obj, "dtype", type(obj).__name__)),
                    "size": size,
                }
        if _is_complex_array(obj):
            # Two arrays of the input's shape rather than one {"real", "imag"} per element
            try:
                return {"real": obj.real.tolist(), "imag": obj.imag.tolist()}
            except Exception:
                pass
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
    Infinity) are written as ``null`` to keep every line valid JSON. Arrays
    and tensors larger than ``max_array_size`` elements are written as
    ``{"_type": "array_summary", "shape": [...], "dtype": "...", "size": n}``
    so one call cannot put megabytes into a single line. Complex numbers are
    written as ``{"real": ..., "imag": ...}``; for a complex array both
    fields hold an array of the input's shape.

    Args:
        include_extras: Whether to include extra fields from the log record
        strip_markup: Remove paired Rich style tags from the message
        max_array_size: Largest array (in elements) written in full. None
                        writes every array in full.

    Example:
        formatter = JSONFormatter(include_extras=True)
        logger.info("start", extra={"lr": 1e-3})
        # Output: {"timestamp": "2024-01-01T12:00:00+08:00", "level": "INFO", ...,
        #          "message": "start", "extra": {"lr": 0.001}}
    """

    def __init__(
        self,
        include_extras: bool = True,
        strip_markup: bool = False,
        max_array_size: int | None = DEFAULT_MAX_ARRAY_SIZE,
    ):
        super().__init__()
        self.include_extras = include_extras
        self.strip_markup = strip_markup
        self.max_array_size = max_array_size

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON.

        Args:
            record: Log record to format

        Returns:
            JSON-formatted log message
        """
        message = record.getMessage()
        if self.strip_markup:
            message = strip_rich_markup(message)

        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).astimezone().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_data["stack"] = self.formatStack(record.stack_info)

        if self.include_extras:
            extras = {key: value for key, value in record.__dict__.items() if key not in RESERVED_RECORD_ATTRS}
            if extras:
                log_data["extra"] = extras

        def default(obj: Any) -> Any:
            return _json_default(obj, self.max_array_size)

        try:
            text = json.dumps(log_data, ensure_ascii=False, default=default)
        except (TypeError, ValueError):
            # Unserializable keys or circular references: keep the record anyway
            log_data["extra"] = repr(log_data.get("extra"))
            text = json.dumps(log_data, ensure_ascii=False, default=default)

        # NaN/Infinity are not valid JSON and make strict parsers reject the
        # line, so write them as null. The substring test only gates the
        # re-encode; a message that merely contains the word passes through intact.
        if "NaN" in text or "Infinity" in text:
            text = json.dumps(json.loads(text, parse_constant=lambda _: None), ensure_ascii=False)

        return text
