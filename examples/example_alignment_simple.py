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

"""Simplest alignment example - ready to use"""

import logging
import sys

if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

from advlog.core.formatter import AlignedFormatter, CompactFormatter, TableFormatter

print("=" * 80)
print("Alignment format example")
print("=" * 80)

# ========== Example 1: Standard alignment (most commonly used) ==========
print("\n[Example 1] Standard alignment - recommended for daily use")
print("-" * 80)

formatter1 = AlignedFormatter(
    time_width=12,  # Time field width
    level_width=8,  # Level field width
    location_width=35,  # Location field width
)

logger1 = logging.getLogger("standard")
logger1.setLevel(logging.DEBUG)
logger1.handlers.clear()
handler1 = logging.StreamHandler(sys.stdout)
handler1.setFormatter(formatter1)
logger1.addHandler(handler1)

logger1.info("User login successful")
logger1.warning("Memory usage reached 80%")
logger1.error("Database connection failed")
logger1.debug("Debug information: variable x=42")


# ========== Example 2: Table format ==========
print("\n[Example 2] Table format - suitable for log review")
print("-" * 80)

formatter2 = TableFormatter()

logger2 = logging.getLogger("table")
logger2.setLevel(logging.DEBUG)
logger2.handlers.clear()
handler2 = logging.StreamHandler(sys.stdout)
handler2.setFormatter(formatter2)
logger2.addHandler(handler2)


def process_request():
    logger2.info("Received HTTP request")
    logger2.debug("Validating token")
    logger2.info("Returning response: 200 OK")


process_request()


# ========== Example 3: Compact format ==========
print("\n[Example 3] Compact format - recommended for development environment")
print("-" * 80)

formatter3 = CompactFormatter(location_width=30)

logger3 = logging.getLogger("compact")
logger3.setLevel(logging.DEBUG)
logger3.handlers.clear()
handler3 = logging.StreamHandler(sys.stdout)
handler3.setFormatter(formatter3)
logger3.addHandler(handler3)

logger3.debug("Starting processing")
logger3.info("Processing in progress...")
logger3.warning("Abnormalities detected")
logger3.error("Processing failed")


# ========== Comparison: Left alignment vs Right alignment ==========
print("\n[Comparison] Left alignment vs Right alignment")
print("-" * 80)

print("\nLeft alignment (default):")
formatter_left = AlignedFormatter(
    time_width=12,
    level_width=8,
    location_width=30,
    align_time="left",
    align_level="left",
    align_location="left",
)

logger_left = logging.getLogger("left")
logger_left.setLevel(logging.INFO)
logger_left.handlers.clear()
handler_left = logging.StreamHandler(sys.stdout)
handler_left.setFormatter(formatter_left)
logger_left.addHandler(handler_left)

logger_left.info("Left alignment example")
logger_left.warning("All fields left aligned")

print("\nRight alignment:")
formatter_right = AlignedFormatter(
    time_width=12,
    level_width=8,
    location_width=30,
    align_time="right",
    align_level="right",
    align_location="right",
)

logger_right = logging.getLogger("right")
logger_right.setLevel(logging.INFO)
logger_right.handlers.clear()
handler_right = logging.StreamHandler(sys.stdout)
handler_right.setFormatter(formatter_right)
logger_right.addHandler(handler_right)

logger_right.info("Right alignment example")
logger_right.warning("All fields right aligned")


# ========== Summary ==========
print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print()
print("Alignment functionality is complete, supporting:")
print("  ✓ Custom field widths")
print("  ✓ Three alignment methods (left/right/center)")
print("  ✓ Multiple preset formats (standard/table/compact/column)")
print("  ✓ Flexible field display control")
print()
print("Usage:")
print("  from core import AlignedFormatter, TableFormatter, CompactFormatter")
print("  formatter = AlignedFormatter(time_width=12, level_width=8, location_width=35)")
print()
print("View complete examples: python demo_aligned_logging.py")
print("=" * 80)
