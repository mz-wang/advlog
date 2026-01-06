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

"""Demonstration of aligned formatting features"""

import logging
import sys

if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

from advlog.core.formatter import (
    AlignedFormatter,
    ColumnFormatter,
    CompactFormatter,
    TableFormatter,
    create_aligned_formatter,
)


def example1_standard_aligned():
    """Example 1: Standard aligned format"""
    print("\n" + "=" * 80)
    print("Example 1: Standard aligned format")
    print("=" * 80)

    formatter = AlignedFormatter(
        time_width=12,
        level_width=8,
        location_width=35,
        align_time="left",
        align_level="left",
        align_location="right",
    )

    logger = logging.getLogger("aligned_demo1")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Logs of different lengths
    logger.debug("Debug information")
    logger.info("This is an info log")
    logger.warning("Warning: Potential issue detected")
    logger.error("Error: Operation failed")


def example2_table_format():
    """Example 2: Table format"""
    print("\n" + "=" * 80)
    print("Example 2: Table format (like a data table)")
    print("=" * 80)

    formatter = TableFormatter(
        time_width=12,
        level_width=8,
        location_width=35,
    )

    logger = logging.getLogger("table_demo")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def process_data():
        logger.info("Starting data processing")
        logger.debug("Loading configuration file")

    def validate_input():
        logger.info("Validating input parameters")
        logger.warning("Parameters may be incomplete")

    def save_result():
        logger.info("Saving processed results")
        logger.error("Insufficient disk space")

    process_data()
    validate_input()
    save_result()


def example3_compact_format():
    """Example 3: Compact format"""
    print("\n" + "=" * 80)
    print("Example 3: Compact format (recommended for development)")
    print("=" * 80)

    formatter = CompactFormatter(location_width=30)

    logger = logging.getLogger("compact_demo")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def api_handler():
        logger.debug("Receiving API request")
        logger.info("Processing request")
        logger.warning("Request taking too long")

    api_handler()


def example4_column_format():
    """Example 4: Column format"""
    print("\n" + "=" * 80)
    print("Example 4: Column format (custom columns)")
    print("=" * 80)

    formatter = ColumnFormatter(
        columns=["time", "level", "name", "location", "message"],
        widths={
            "time": 12,
            "level": 8,
            "name": 15,
            "location": 35,
            "message": None,
        },
    )

    logger = logging.getLogger("column_demo")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("Log with logger name included")
    logger.warning("Can display more column information")


def example5_different_alignments():
    """Example 5: Different alignment methods"""
    print("\n" + "=" * 80)
    print("Example 5: Different alignment methods")
    print("=" * 80)

    print("\n--- Left alignment ---")
    formatter_left = AlignedFormatter(
        time_width=12,
        level_width=10,
        location_width=30,
        align_time="left",
        align_level="left",
        align_location="left",
    )

    logger_left = logging.getLogger("left_align")
    logger_left.setLevel(logging.DEBUG)
    logger_left.handlers.clear()
    handler_left = logging.StreamHandler(sys.stdout)
    handler_left.setFormatter(formatter_left)
    logger_left.addHandler(handler_left)

    logger_left.info("Left aligned format")
    logger_left.warning("All fields are left aligned")

    print("\n--- Right alignment ---")
    formatter_right = AlignedFormatter(
        time_width=12,
        level_width=10,
        location_width=30,
        align_time="right",
        align_level="right",
        align_location="right",
    )

    logger_right = logging.getLogger("right_align")
    logger_right.setLevel(logging.DEBUG)
    logger_right.handlers.clear()
    handler_right = logging.StreamHandler(sys.stdout)
    handler_right.setFormatter(formatter_right)
    logger_right.addHandler(handler_right)

    logger_right.info("Right aligned format")
    logger_right.warning("All fields are right aligned")

    print("\n--- Center alignment ---")
    formatter_center = AlignedFormatter(
        time_width=12,
        level_width=10,
        location_width=30,
        align_time="center",
        align_level="center",
        align_location="center",
    )

    logger_center = logging.getLogger("center_align")
    logger_center.setLevel(logging.DEBUG)
    logger_center.handlers.clear()
    handler_center = logging.StreamHandler(sys.stdout)
    handler_center.setFormatter(formatter_center)
    logger_center.addHandler(handler_center)

    logger_center.info("Center aligned format")
    logger_center.warning("All fields are center aligned")


def example6_custom_widths():
    """Example 6: Custom field widths"""
    print("\n" + "=" * 80)
    print("Example 6: Custom field widths")
    print("=" * 80)

    print("\n--- Narrow width (compact) ---")
    formatter_narrow = AlignedFormatter(
        time_width=8,
        level_width=5,
        location_width=20,
    )

    logger_narrow = logging.getLogger("narrow")
    logger_narrow.setLevel(logging.DEBUG)
    logger_narrow.handlers.clear()
    handler_narrow = logging.StreamHandler(sys.stdout)
    handler_narrow.setFormatter(formatter_narrow)
    logger_narrow.addHandler(handler_narrow)

    logger_narrow.info("Compact format")
    logger_narrow.warning("Narrow width")

    print("\n--- Wide width (loose) ---")
    formatter_wide = AlignedFormatter(
        time_width=15,
        level_width=12,
        location_width=45,
    )

    logger_wide = logging.getLogger("wide")
    logger_wide.setLevel(logging.DEBUG)
    logger_wide.handlers.clear()
    handler_wide = logging.StreamHandler(sys.stdout)
    handler_wide.setFormatter(formatter_wide)
    logger_wide.addHandler(handler_wide)

    logger_wide.info("Loose format")
    logger_wide.warning("Wide width, easier to read")


def example7_with_without_fields():
    """Example 7: Selective field display"""
    print("\n" + "=" * 80)
    print("Example 7: Selective field display")
    print("=" * 80)

    print("\n--- Only show level and message ---")
    formatter_minimal = AlignedFormatter(
        level_width=8,
        show_time=False,
        show_location=False,
    )

    logger_minimal = logging.getLogger("minimal")
    logger_minimal.setLevel(logging.DEBUG)
    logger_minimal.handlers.clear()
    handler_minimal = logging.StreamHandler(sys.stdout)
    handler_minimal.setFormatter(formatter_minimal)
    logger_minimal.addHandler(handler_minimal)

    logger_minimal.info("Minimal format")
    logger_minimal.warning("Only show necessary information")

    print("\n--- Show all fields ---")
    formatter_full = AlignedFormatter(
        time_width=12,
        level_width=8,
        name_width=15,
        location_width=35,
        show_time=True,
        show_level=True,
        show_name=True,
        show_location=True,
    )

    logger_full = logging.getLogger("full_display")
    logger_full.setLevel(logging.DEBUG)
    logger_full.handlers.clear()
    handler_full = logging.StreamHandler(sys.stdout)
    handler_full.setFormatter(formatter_full)
    logger_full.addHandler(handler_full)

    logger_full.info("Full format")
    logger_full.warning("Show all fields")


def example8_real_world_scenario():
    """Example 8: Real-world scenario"""
    print("\n" + "=" * 80)
    print("Example 8: Real-world scenario - Web application logs")
    print("=" * 80)

    formatter = TableFormatter(
        time_width=12,
        level_width=8,
        location_width=40,
    )

    logger = logging.getLogger("webapp")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def handle_request():
        logger.info("Received HTTP request: GET /api/users")
        logger.debug("Parsing request parameters")
        validate_auth()
        query_database()
        logger.info("Returning response: 200 OK")

    def validate_auth():
        logger.debug("Validating user token")
        logger.info("User authentication successful")

    def query_database():
        logger.debug("Executing database query")
        logger.warning("Query took 1.2s, approaching threshold")
        logger.info("Query completed, returning 150 records")

    handle_request()


def example9_factory_function():
    """Example 9: Using factory function to create"""
    print("\n" + "=" * 80)
    print("Example 9: Using factory function to create formatter")
    print("=" * 80)

    # Create different styles
    styles = ["standard", "table", "compact"]

    for style in styles:
        print(f"\n--- {style.upper()} style ---")

        formatter = create_aligned_formatter(style)

        logger = logging.getLogger(f"factory_{style}")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        logger.info(f"This is a {style} style log")
        logger.warning(f"{style} style warning message")


# Run all examples
if __name__ == "__main__":
    print("=" * 80)
    print("🎨 Log aligned formatting feature demonstration")
    print("=" * 80)

    examples = [
        example1_standard_aligned,
        example2_table_format,
        example3_compact_format,
        example4_column_format,
        example5_different_alignments,
        example6_custom_widths,
        example7_with_without_fields,
        example8_real_world_scenario,
        example9_factory_function,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n[Error] {example.__name__}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)
