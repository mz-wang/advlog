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

"""Tests for formatter classes."""

import json
import logging

from advlog.core import (
    IndentedFormatter,
    JSONFormatter,
    PlainFormatter,
    RichColorFormatter,
)


def _record(msg="Test message", level=logging.INFO):
    return logging.LogRecord("test", level, "file.py", 42, msg, (), None)


class TestRichColorFormatter:
    def test_wraps_with_color_markup(self):
        formatter = RichColorFormatter()
        formatted = formatter.format(_record("Hello", logging.INFO))
        assert "[green]" in formatted
        assert "Hello" in formatted

    def test_different_levels_get_different_colors(self):
        formatter = RichColorFormatter()
        info = formatter.format(_record(level=logging.INFO))
        error = formatter.format(_record(level=logging.ERROR))
        assert "[green]" in info
        assert "[red]" in error

    def test_custom_colors(self):
        formatter = RichColorFormatter(log_colors={"INFO": "blue"})
        formatted = formatter.format(_record(level=logging.INFO))
        assert "[blue]" in formatted


class TestPlainFormatter:
    def test_no_color_codes(self):
        formatter = PlainFormatter()
        formatted = formatter.format(_record("Plain text"))
        assert "Plain text" in formatted
        assert "[green]" not in formatted

    def test_contains_level_and_message(self):
        formatter = PlainFormatter()
        formatted = formatter.format(_record("Hello"))
        assert "[INFO]" in formatted
        assert "Hello" in formatted


class TestIndentedFormatter:
    def test_single_line_unchanged(self):
        formatter = IndentedFormatter()
        formatted = formatter.format(_record("Single line"))
        assert "Single line" in formatted
        assert "\n" not in formatted

    def test_multiline_continuation_indented(self):
        formatter = IndentedFormatter(indent_size=10)
        record = _record("Line 1\nLine 2\nLine 3")
        formatted = formatter.format(record)
        lines = formatted.split("\n")
        assert len(lines) == 3
        assert "Line 1" in lines[0]
        assert lines[1].startswith("          "), f"Expected indentation, got: {repr(lines[1])}"


class TestJSONFormatter:
    def test_valid_json_with_required_fields(self):
        formatter = JSONFormatter()
        data = json.loads(formatter.format(_record("JSON test")))
        assert data["level"] == "INFO"
        assert data["message"] == "JSON test"
        assert data["logger"] == "test"
        assert "timestamp" in data

    def test_exception_included(self):
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = _record("Error")
            record.exc_info = sys.exc_info()
            data = json.loads(JSONFormatter().format(record))
            assert "exception" in data
            assert "ValueError" in data["exception"]

    def test_extras_included_when_enabled(self):
        record = _record()
        record.my_field = "my_value"
        data = json.loads(JSONFormatter(include_extras=True).format(record))
        assert data.get("my_field") == "my_value"

    def test_extras_excluded_when_disabled(self):
        record = _record()
        record.my_field = "my_value"
        data = json.loads(JSONFormatter(include_extras=False).format(record))
        assert "my_field" not in data
