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

"""Simplest log source information example - Learn in 3 minutes"""

import logging
import sys

if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

from advlog.core.formatter import PlainFormatter

print("=" * 70)
print("🔍 Log source information display - simplest example")
print("=" * 70)

# ========== Example 1: Display file name and line number (most commonly used) ==========
print("\n[Example 1] Display file name and line number")
print("-" * 70)

# Create formatter - the key is this line!
formatter1 = PlainFormatter(
    fmt="%(asctime)s | %(levelname)-8s | [%(filename)s:%(lineno)d] | %(message)s", datefmt="%H:%M:%S"
)

logger1 = logging.getLogger("demo1")
logger1.setLevel(logging.DEBUG)
logger1.handlers.clear()

handler1 = logging.StreamHandler(sys.stdout)
handler1.setFormatter(formatter1)
logger1.addHandler(handler1)

# Use - will automatically show file name and line number!
logger1.info("This log shows file name and line number")
logger1.warning("You can see which line the log is from")


# ========== Example 2: Display function name ==========
print("\n[Example 2] Display function name")
print("-" * 70)

formatter2 = PlainFormatter(fmt="%(asctime)s | [%(funcName)s] | %(message)s", datefmt="%H:%M:%S")

logger2 = logging.getLogger("demo2")
logger2.setLevel(logging.DEBUG)
logger2.handlers.clear()

handler2 = logging.StreamHandler(sys.stdout)
handler2.setFormatter(formatter2)
logger2.addHandler(handler2)


def process_data():
    logger2.info("This log comes from process_data function")


def save_result():
    logger2.info("This log comes from save_result function")


process_data()
save_result()


# ========== Example 3: Complete information (recommended!) ==========
print("\n[Example 3] Complete information: file name:line number:function name (recommended)")
print("-" * 70)

formatter3 = PlainFormatter(
    fmt="%(asctime)s | [%(filename)s:%(lineno)d:%(funcName)s] | %(message)s", datefmt="%H:%M:%S"
)

logger3 = logging.getLogger("demo3")
logger3.setLevel(logging.DEBUG)
logger3.handlers.clear()

handler3 = logging.StreamHandler(sys.stdout)
handler3.setFormatter(formatter3)
logger3.addHandler(handler3)


def main():
    logger3.info("Main function starting")
    calculate()


def calculate():
    logger3.debug("Executing calculation")
    result = 42
    logger3.info(f"Calculation result: {result}")
    return result


main()


# ========== Example 4: Compact format (recommended for development environment) ==========
print("\n[Example 4] Compact format - recommended for development environment")
print("-" * 70)

formatter4 = PlainFormatter(fmt="[%(levelname).1s] %(filename)s:%(lineno)d:%(funcName)s() | %(message)s")

logger4 = logging.getLogger("demo4")
logger4.setLevel(logging.DEBUG)
logger4.handlers.clear()

handler4 = logging.StreamHandler(sys.stdout)
handler4.setFormatter(formatter4)
logger4.addHandler(handler4)


def api_handler():
    logger4.debug("Received API request")
    logger4.info("Processing request")
    logger4.warning("Request taking too long")


api_handler()


# ========== Summary ==========
print("\n" + "=" * 70)
print("✅ Summary")
print("=" * 70)
print()
print("Displaying log source information is very simple, just add to the format string:")
print()
print("  %(filename)s   - File name")
print("  %(lineno)d     - Line number")
print("  %(funcName)s   - Function name")
print()
print("💡 Recommended formats:")
print()
print("  Development environment:")
print('    "[%(levelname).1s] %(filename)s:%(lineno)d:%(funcName)s() | %(message)s"')
print()
print("  Production environment:")
print('    "%(asctime)s | %(levelname)-8s | [%(filename)s:%(lineno)d] | %(message)s"')
print()
print("=" * 70)
print("🎉 It's that simple!")
print("=" * 70)
print()
print("📖 View more examples: python demo_log_source.py")
print("📖 Complete guide: LOG_SOURCE_GUIDE.md")
