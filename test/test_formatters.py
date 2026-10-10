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
        assert data["extra"] == {"my_field": "my_value"}
        assert "my_field" not in data

    def test_extras_excluded_when_disabled(self):
        record = _record()
        record.my_field = "my_value"
        data = json.loads(JSONFormatter(include_extras=False).format(record))
        assert "extra" not in data
        assert "my_field" not in data

    def test_no_extra_key_without_extras(self):
        data = json.loads(JSONFormatter().format(_record()))
        assert "extra" not in data
        assert "taskName" not in data

    def test_extras_cannot_overwrite_standard_fields(self):
        record = _record("real message", logging.INFO)
        record.level = "FAKE"
        record.timestamp = "never"
        data = json.loads(JSONFormatter().format(record))
        assert data["level"] == "INFO"
        assert data["timestamp"] != "never"
        assert data["extra"] == {"level": "FAKE", "timestamp": "never"}

    def test_fields_set_by_other_formatters_not_leaked(self):
        record = _record()
        PlainFormatter().format(record)  # sets record.asctime and record.message
        data = json.loads(JSONFormatter().format(record))
        assert "extra" not in data

    def test_unserializable_extras_do_not_drop_record(self):
        from pathlib import Path

        class Custom:
            def __str__(self):
                return "custom!"

        record = _record("kept")
        record.path = Path("a/b")
        record.tags = {"x"}
        record.obj = Custom()
        data = json.loads(JSONFormatter().format(record))
        assert data["message"] == "kept"
        assert data["extra"] == {"path": str(Path("a/b")), "tags": ["x"], "obj": "custom!"}

    def test_array_like_extras_use_tolist(self):
        class ArrayLike:
            def tolist(self):
                return [1, 2, 3]

        record = _record()
        record.values = ArrayLike()
        data = json.loads(JSONFormatter().format(record))
        assert data["extra"] == {"values": [1, 2, 3]}

    def test_unencodable_extras_fall_back_to_repr(self):
        record = _record("kept")
        record.bad_keys = {(1, 2): "tuple key"}
        loop = {}
        loop["self"] = loop
        record.loop = loop
        data = json.loads(JSONFormatter().format(record))
        assert data["message"] == "kept"
        assert isinstance(data["extra"], str)
        assert "tuple key" in data["extra"]

    def test_non_finite_floats_written_as_null(self):
        class ArrayLike:
            def tolist(self):
                return [1.0, float("nan")]

        record = _record("loss is NaN, not Infinity")
        record.metrics = {"loss": float("nan"), "grad": float("inf"), "floor": float("-inf"), "acc": 0.5}
        record.values = ArrayLike()
        formatted = JSONFormatter().format(record)

        def reject(constant):
            raise AssertionError(f"non-standard JSON constant: {constant}")

        data = json.loads(formatted, parse_constant=reject)
        assert data["extra"]["metrics"] == {"loss": None, "grad": None, "floor": None, "acc": 0.5}
        assert data["extra"]["values"] == [1.0, None]
        assert data["message"] == "loss is NaN, not Infinity"

    def test_timestamp_has_timezone(self):
        from datetime import datetime

        data = json.loads(JSONFormatter().format(_record()))
        assert datetime.fromisoformat(data["timestamp"]).tzinfo is not None

    def test_stack_info_included(self):
        record = _record()
        record.stack_info = "Stack (most recent call last):\n  File ..."
        data = json.loads(JSONFormatter().format(record))
        assert data["stack"].startswith("Stack")

    def test_multiline_message_stays_on_one_line(self):
        formatted = JSONFormatter().format(_record("line 1\nline 2"))
        assert "\n" not in formatted
        assert json.loads(formatted)["message"] == "line 1\nline 2"
