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

import pytest

from advlog.core import (
    IndentedFormatter,
    JSONFormatter,
    PlainFormatter,
    RichColorFormatter,
)
from advlog.core.formatter import strip_rich_markup


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


class TestStripRichMarkup:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("[bold red]alert[/bold red] done", "alert done"),
            ("[red]a[/] and [b]b[/b]", "a and b"),
            ("[bold][red]nested[/red][/bold]", "nested"),
            ("[link=https://example.com]docs[/link]", "docs"),
            # Lone or non-style brackets are ordinary text and must survive
            ("arr[i] = x[j]", "arr[i] = x[j]"),
            ("[1/3][2/4] loss: 0.5", "[1/3][2/4] loss: 0.5"),
            ("names: [alice, bob]", "names: [alice, bob]"),
            ("[epoch 1] started [/epoch 1]", "[epoch 1] started [/epoch 1]"),
            ("[bold]unclosed", "[bold]unclosed"),
            ("path [/usr/bin]", "path [/usr/bin]"),
            (r"\[bold]escaped[/bold]", r"\[bold]escaped[/bold]"),
            ("no markup at all", "no markup at all"),
        ],
    )
    def test_strips_only_paired_style_tags(self, text, expected):
        assert strip_rich_markup(text) == expected

    def test_formatters_strip_when_enabled(self):
        record = _record("[bold red]alert[/bold red] done")
        assert PlainFormatter(strip_markup=True).format(record).endswith("alert done")
        assert IndentedFormatter(fmt="%(message)s", strip_markup=True).format(record) == "alert done"
        assert json.loads(JSONFormatter(strip_markup=True).format(record))["message"] == "alert done"

    def test_formatters_keep_markup_by_default(self):
        record = _record("[bold red]alert[/bold red] done")
        assert "[bold red]" in PlainFormatter().format(record)
        assert "[bold red]" in json.loads(JSONFormatter().format(record))["message"]

    def test_stripping_does_not_alter_the_record(self):
        record = _record("[bold]x[/bold]")
        PlainFormatter(strip_markup=True).format(record)
        assert record.msg == "[bold]x[/bold]"
        assert record.getMessage() == "[bold]x[/bold]"


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

    def test_complex_numbers_written_as_real_and_imag(self):
        class Part:
            def __init__(self, values):
                self.values = values

            def tolist(self):
                return self.values

        class ComplexArray:  # numpy-like: dtype.kind == "c", .real / .imag arrays
            size, shape = 2, (2,)
            dtype = type("dtype", (), {"kind": "c"})()
            real, imag = Part([1.0, 0.0]), Part([2.0, float("nan")])

            def tolist(self):
                raise AssertionError("complex array converted element by element")

        class ComplexTensor:  # torch-like: dtype.is_complex
            size, shape = 1, (1, 1)
            dtype = type("dtype", (), {"is_complex": True})()
            real, imag = Part([[3.0]]), Part([[-1.0]])

            def numel(self):
                return 1

            def tolist(self):
                raise AssertionError("complex tensor converted element by element")

        record = _record()
        record.z = 1 + 2j
        record.zs = [0.5j]
        record.array = ComplexArray()
        record.tensor = ComplexTensor()
        data = json.loads(JSONFormatter().format(record))
        assert data["extra"] == {
            "z": {"real": 1.0, "imag": 2.0},
            "zs": [{"real": 0.0, "imag": 0.5}],
            "array": {"real": [1.0, 0.0], "imag": [2.0, None]},  # NaN -> null as elsewhere
            "tensor": {"real": [[3.0]], "imag": [[-1.0]]},
        }

    def test_large_arrays_written_as_summary(self):
        class NumpyLike:
            def __init__(self, n):
                self.size, self.shape, self.dtype = n, (n,), "float64"

            def tolist(self):
                return [0.0] * self.size

        class TensorLike:
            shape, dtype = (2, 3, 1000), "torch.float32"

            def numel(self):
                return 6000

            def size(self):  # torch: a method returning the shape
                return self.shape

            def tolist(self):
                raise AssertionError("large tensor converted in full")

        record = _record()
        record.small = NumpyLike(1000)
        record.large = NumpyLike(1001)
        record.tensor = TensorLike()
        data = json.loads(JSONFormatter().format(record))
        assert data["extra"]["small"] == [0.0] * 1000
        assert data["extra"]["large"] == {"_type": "array_summary", "shape": [1001], "dtype": "float64", "size": 1001}
        assert data["extra"]["tensor"] == {
            "_type": "array_summary",
            "shape": [2, 3, 1000],
            "dtype": "torch.float32",
            "size": 6000,
        }

        full = json.loads(JSONFormatter(max_array_size=None).format(record))
        assert full["extra"]["large"] == [0.0] * 1001

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
