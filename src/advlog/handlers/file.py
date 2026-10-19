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
import os
from logging.handlers import RotatingFileHandler as StdRotatingFileHandler

from advlog.utils.path import StrPath, ensure_dir

FILE_FORMATS = ("text", "json", "both")
DEFAULT_LOG_FORMAT = "%(asctime)s |%(levelname)-8s| %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LOCATION = "[%(filename)s:%(lineno)d:%(funcName)s]"


class _SkipTextOnly(logging.Filter):
    """Keep display-only records out of JSON files.

    Records logged with ``extra={"text_only": True}`` (separators, banners,
    pretty-printed lines) still reach the console and text files.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return not getattr(record, "text_only", False)


def _build_formatter(
    use_json_format: bool,
    use_indented_format: bool,
    show_location: bool,
    indent_size: int,
    date_format: str,
    log_format: str,
    strip_markup: bool,
) -> logging.Formatter:
    """Choose the formatter for a file handler.

    Args:
        use_json_format: Output logs as JSON instead
        use_indented_format: Use indented formatter for multi-line messages
        show_location: Include source location (file:line) in log
        indent_size: Indentation size for continuation lines
        date_format: Date format string
        log_format: Log message format string
        strip_markup: Remove paired Rich style tags from messages

    Returns:
        Configured formatter
    """
    # Lazy import formatters to avoid circular imports
    from advlog.core.formatter import IndentedFormatter, JSONFormatter, PlainFormatter

    if use_json_format:
        return JSONFormatter(strip_markup=strip_markup)

    if show_location and use_indented_format:
        # Location goes right before the message; appended if the format has no message field
        if "%(message)s" in log_format:
            location_fmt = log_format.replace("%(message)s", f"{_LOCATION} %(message)s")
        else:
            location_fmt = f"{log_format} {_LOCATION}"
        return IndentedFormatter(
            fmt=location_fmt, datefmt=date_format, indent_size=indent_size, strip_markup=strip_markup
        )

    if use_indented_format:
        return IndentedFormatter(
            fmt=log_format, datefmt=date_format, indent_size=indent_size, strip_markup=strip_markup
        )

    if show_location:
        return PlainFormatter(fmt=f"{log_format} {_LOCATION}", datefmt=date_format, strip_markup=strip_markup)

    return PlainFormatter(fmt=log_format, datefmt=date_format, strip_markup=strip_markup)


class FileHandler:
    """Factory for creating file handlers.

    This class creates file handlers with appropriate formatters
    and handles directory creation.
    """

    @staticmethod
    def create(
        log_file: StrPath,
        mode: str = "w",
        encoding: str = "utf-8",
        log_level: int = logging.DEBUG,
        use_indented_format: bool = True,
        show_location: bool = False,
        location_width: int = 50,
        indent_size: int = 27,
        date_format: str = DEFAULT_DATE_FORMAT,
        log_format: str = DEFAULT_LOG_FORMAT,
        use_json_format: bool = False,
        strip_markup: bool = True,
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
            strip_markup: Remove paired Rich style tags (``[bold]..[/bold]``)
                          so the file holds the text the console displays

        Returns:
            Configured file handler
        """
        # Create directory if it doesn't exist
        if log_file:
            ensure_dir(log_file)

        # Create handler. delay=True defers opening (and creating) the file
        # until the first record is emitted, so a handler that never receives a
        # record leaves no empty file behind.
        handler = logging.FileHandler(log_file, mode=mode, encoding=encoding, delay=True)

        formatter = _build_formatter(
            use_json_format=use_json_format,
            use_indented_format=use_indented_format,
            show_location=show_location,
            indent_size=indent_size,
            date_format=date_format,
            log_format=log_format,
            strip_markup=strip_markup,
        )

        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        if use_json_format:
            handler.addFilter(_SkipTextOnly())

        return handler


class RotatingFileHandler:
    """Factory for creating rotating file handlers.

    This handler automatically rotates log files when they reach
    a certain size, keeping a specified number of backup files.
    """

    @staticmethod
    def create(
        log_file: StrPath,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5,
        encoding: str = "utf-8",
        log_level: int = logging.DEBUG,
        use_indented_format: bool = True,
        show_location: bool = False,
        location_width: int = 50,
        indent_size: int = 27,
        date_format: str = DEFAULT_DATE_FORMAT,
        log_format: str = DEFAULT_LOG_FORMAT,
        use_json_format: bool = False,
        strip_markup: bool = True,
    ) -> logging.Handler:
        """Create a rotating file handler.

        The file is always appended to: rotation, not truncation, is what
        keeps it from growing.

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
            use_json_format: Output logs as JSON instead
            strip_markup: Remove paired Rich style tags (``[bold]..[/bold]``)
                          so the file holds the text the console displays

        Returns:
            Configured rotating file handler
        """
        # Create directory if it doesn't exist
        ensure_dir(log_file)

        # Create handler. delay=True: see FileHandler.create
        handler = StdRotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count, encoding=encoding, delay=True
        )

        formatter = _build_formatter(
            use_json_format=use_json_format,
            use_indented_format=use_indented_format,
            show_location=show_location,
            indent_size=indent_size,
            date_format=date_format,
            log_format=log_format,
            strip_markup=strip_markup,
        )

        handler.setFormatter(formatter)
        handler.setLevel(log_level)
        if use_json_format:
            handler.addFilter(_SkipTextOnly())

        return handler


def create_file_handler(
    log_file: StrPath, mode: str = "w", max_file_size: int | None = None, backup_count: int = 5, **kwargs
) -> logging.Handler:
    """Convenience function to create a file handler.

    This function automatically chooses between a regular file handler
    and a rotating file handler based on the max_file_size parameter.

    Args:
        log_file: Path to the log file
        mode: File opening mode ('w' or 'a'). Ignored with rotation, which
              always appends.
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


def _resolve_log_paths(log_file: str, file_format: str) -> tuple[str | None, str | None]:
    """Work out where the text and JSON Lines files go for a given format.

    The JSON Lines file sits next to the text file with a ``.jsonl`` extension.

    Args:
        log_file: Path to the log file
        file_format: "text", "json", or "both"

    Returns:
        Tuple of (text path, JSON Lines path); an entry is None when unused
    """
    if file_format not in FILE_FORMATS:
        raise ValueError(f"Invalid file format: {file_format!r} (expected one of {FILE_FORMATS})")

    stem, ext = os.path.splitext(log_file)
    is_json_path = ext.lower() in (".jsonl", ".json")
    json_file = log_file if is_json_path else f"{stem}.jsonl"
    text_file = f"{stem}.log" if is_json_path else log_file

    if file_format == "text":
        return log_file, None
    if file_format == "json":
        return None, json_file
    return text_file, json_file


def create_file_handlers(
    log_file: StrPath,
    file_format: str = "text",
    mode: str = "w",
    max_file_size: int | None = None,
    backup_count: int = 5,
    **kwargs,
) -> list[logging.Handler]:
    """Create the file handler(s) for a log file in the requested format.

    Args:
        log_file: Path to the log file
        file_format: "text" (human-readable), "json" (JSON Lines, written to
                     the same path with a ``.jsonl`` extension), or "both"
        mode: File opening mode ('w' or 'a')
        max_file_size: Maximum file size in bytes (None = no rotation)
        backup_count: Number of backup files to keep
        **kwargs: Additional arguments passed to handler creation

    Returns:
        List of configured file handlers (one per output file)

    Example:
        # logs/app.log (text) and logs/app.jsonl (one JSON object per line)
        handlers = create_file_handlers("logs/app.log", file_format="both")
    """
    text_file, json_file = _resolve_log_paths(os.fspath(log_file), file_format)

    handlers = []
    if text_file:
        handlers.append(
            create_file_handler(text_file, mode=mode, max_file_size=max_file_size, backup_count=backup_count, **kwargs)
        )
    if json_file:
        handlers.append(
            create_file_handler(
                json_file,
                mode=mode,
                max_file_size=max_file_size,
                backup_count=backup_count,
                **{**kwargs, "use_json_format": True},
            )
        )

    return handlers
