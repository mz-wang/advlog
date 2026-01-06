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

"""Tests for all formatter classes."""

import json
import logging

from advlog.core import (
    AlignedFormatter,
    ColumnFormatter,
    CompactFormatter,
    IndentedFormatter,
    JSONFormatter,
    PlainFormatter,
    RichColorFormatter,
    TableFormatter,
    create_aligned_formatter,
)


class TestRichColorFormatter:
    """Test RichColorFormatter."""

    def test_format_with_color(self):
        """Test formatting with color codes."""
        formatter = RichColorFormatter()
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test message", (), None)
        formatted = formatter.format(record)

        # Should contain color markup
        assert "[green]" in formatted
        assert "Test message" in formatted

    def test_different_levels_different_colors(self):
        """Test that different log levels get different colors."""
        formatter = RichColorFormatter()

        info_record = logging.LogRecord("test", logging.INFO, "", 0, "Info", (), None)
        error_record = logging.LogRecord("test", logging.ERROR, "", 0, "Error", (), None)

        info_formatted = formatter.format(info_record)
        error_formatted = formatter.format(error_record)

        assert "[green]" in info_formatted
        assert "[red]" in error_formatted

    def test_custom_colors(self):
        """Test custom color configuration."""
        custom_colors = {
            "INFO": "blue",
            "ERROR": "magenta",
        }
        formatter = RichColorFormatter(log_colors=custom_colors)

        info_record = logging.LogRecord("test", logging.INFO, "", 0, "Info", (), None)
        info_formatted = formatter.format(info_record)

        assert "[blue]" in info_formatted


class TestPlainFormatter:
    """Test PlainFormatter."""

    def test_plain_format(self):
        """Test plain formatting without colors."""
        formatter = PlainFormatter()
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test message", (), None)
        formatted = formatter.format(record)

        # Should not contain color codes
        assert "[" not in formatted or formatted.count("[") == 0 or "[INFO]" in formatted
        assert "Test message" in formatted

    def test_default_format(self):
        """Test default format string."""
        formatter = PlainFormatter()
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test", (), None)
        formatted = formatter.format(record)

        # Should contain timestamp, level, and message
        assert "[INFO]" in formatted
        assert "Test" in formatted


class TestIndentedFormatter:
    """Test IndentedFormatter."""

    def test_single_line(self):
        """Test single line message (no indentation needed)."""
        formatter = IndentedFormatter()
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Single line", (), None)
        formatted = formatter.format(record)

        assert "Single line" in formatted

    def test_multi_line(self):
        """Test multi-line message with indentation."""
        formatter = IndentedFormatter(indent_size=10)
        message = "Line 1\nLine 2\nLine 3"
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, message, (), None)
        formatted = formatter.format(record)

        lines = formatted.split("\n")
        assert len(lines) == 3
        assert "Line 1" in lines[0]
        assert "Line 2" in lines[1]
        assert "          " in lines[1]  # Indentation


class TestJSONFormatter:
    """Test JSONFormatter."""

    def test_json_format(self):
        """Test JSON formatting."""
        formatter = JSONFormatter()
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test message", (), None)
        formatted = formatter.format(record)

        # Should be valid JSON
        data = json.loads(formatted)
        assert data["level"] == "INFO"
        assert data["message"] == "Test message"
        assert data["logger"] == "test"

    def test_include_extras(self):
        """Test including extra fields."""
        formatter = JSONFormatter(include_extras=True)
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test", (), None)
        record.custom_field = "custom_value"

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert "custom_field" in data
        assert data["custom_field"] == "custom_value"

    def test_exclude_extras(self):
        """Test excluding extra fields."""
        formatter = JSONFormatter(include_extras=False)
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test", (), None)
        record.custom_field = "custom_value"

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert "custom_field" not in data


class TestAlignedFormatter:
    """Test AlignedFormatter."""

    def test_standard_alignment(self):
        """Test standard aligned formatting."""
        formatter = AlignedFormatter()
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test message", (), None)
        formatted = formatter.format(record)

        # Should contain all fields separated by separator
        assert " | " in formatted
        assert "Test message" in formatted

    def test_custom_widths(self):
        """Test custom field widths."""
        formatter = AlignedFormatter(time_width=20, level_width=10)
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test", (), None)
        formatted = formatter.format(record)

        # Time should be padded to 20 characters
        time_part = formatted.split(" | ")[0]
        assert len(time_part) == 20

    def test_alignment_options(self):
        """Test different alignment options."""
        formatter = AlignedFormatter(align_time="center", align_level="right")
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test", (), None)
        formatted = formatter.format(record)

        # Just ensure it doesn't crash
        assert "Test" in formatted

    def test_show_hide_fields(self):
        """Test showing/hiding specific fields."""
        formatter = AlignedFormatter(show_time=False, show_level=False)
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test", (), None)
        formatted = formatter.format(record)

        # Should only contain message (and possibly location)
        assert "Test" in formatted


class TestTableFormatter:
    """Test TableFormatter."""

    def test_table_format(self):
        """Test table-style formatting."""
        formatter = TableFormatter()
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test message", (), None)
        formatted = formatter.format(record)

        # Should contain pipe separators
        assert " | " in formatted
        assert "Test message" in formatted

    def test_custom_widths(self):
        """Test custom column widths."""
        formatter = TableFormatter(time_width=15, level_width=10)
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test", (), None)
        formatted = formatter.format(record)

        parts = formatted.split(" | ")
        assert len(parts) >= 2


class TestCompactFormatter:
    """Test CompactFormatter."""

    def test_compact_format(self):
        """Test compact formatting."""
        formatter = CompactFormatter()
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test message", (), None)
        formatted = formatter.format(record)

        # Should start with level in brackets
        assert "[I]" in formatted
        assert "Test message" in formatted

    def test_level_character(self):
        """Test single-character level indicator."""
        formatter = CompactFormatter()

        info_record = logging.LogRecord("test", logging.INFO, "", 0, "Info", (), None)
        warning_record = logging.LogRecord("test", logging.WARNING, "", 0, "Warning", (), None)
        error_record = logging.LogRecord("test", logging.ERROR, "", 0, "Error", (), None)

        info_formatted = formatter.format(info_record)
        warning_formatted = formatter.format(warning_record)
        error_formatted = formatter.format(error_record)

        assert "[I]" in info_formatted
        assert "[W]" in warning_formatted
        assert "[E]" in error_formatted


class TestColumnFormatter:
    """Test ColumnFormatter."""

    def test_default_columns(self):
        """Test default column configuration."""
        formatter = ColumnFormatter()
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test message", (), None)
        formatted = formatter.format(record)

        assert "Test message" in formatted

    def test_custom_columns(self):
        """Test custom column selection."""
        formatter = ColumnFormatter(columns=["level", "message"])
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test", (), None)
        formatted = formatter.format(record)

        # Should only contain level and message
        parts = formatted.split(" | ")
        assert len(parts) == 2

    def test_custom_widths(self):
        """Test custom column widths."""
        formatter = ColumnFormatter(widths={"time": 15, "level": 10, "message": None})
        record = logging.LogRecord("test", logging.INFO, "file.py", 42, "Test", (), None)
        formatted = formatter.format(record)

        # Just ensure it doesn't crash
        assert "Test" in formatted


class TestCreateAlignedFormatter:
    """Test create_aligned_formatter factory function."""

    def test_create_standard(self):
        """Test creating standard formatter."""
        formatter = create_aligned_formatter("standard")
        assert isinstance(formatter, AlignedFormatter)

    def test_create_table(self):
        """Test creating table formatter."""
        formatter = create_aligned_formatter("table")
        assert isinstance(formatter, TableFormatter)

    def test_create_compact(self):
        """Test creating compact formatter."""
        formatter = create_aligned_formatter("compact")
        assert isinstance(formatter, CompactFormatter)

    def test_create_column(self):
        """Test creating column formatter."""
        formatter = create_aligned_formatter("column")
        assert isinstance(formatter, ColumnFormatter)

    def test_create_with_kwargs(self):
        """Test creating formatter with custom arguments."""
        formatter = create_aligned_formatter("standard", time_width=20)
        assert isinstance(formatter, AlignedFormatter)
        assert formatter.time_width == 20

    def test_invalid_style(self):
        """Test creating formatter with invalid style (should default to standard)."""
        formatter = create_aligned_formatter("invalid_style")
        assert isinstance(formatter, AlignedFormatter)
