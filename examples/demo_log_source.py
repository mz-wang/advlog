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

"""Demonstration of log source information display - Shows function name, file name, line number"""

import sys

if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

import logging

from advlog.core import AdvancedLogger, LoggerConfig
from advlog.core.formatter import PlainFormatter


def example1_basic_source_info():
    """Example 1: Basic source information display"""
    print("\n" + "=" * 70)
    print("Example 1: Display file name and line number")
    print("=" * 70)

    # Create custom formatter with source information
    formatter = PlainFormatter(
        fmt="%(asctime)s | %(levelname)-8s | [%(filename)s:%(lineno)d] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create logger
    logger = logging.getLogger("source_demo1")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Add console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Test log
    logger.info("This log will show file name and line number")
    logger.debug("Debug information")
    logger.warning("Warning information")


def example2_function_name():
    """Example 2: Display function name"""
    print("\n" + "=" * 70)
    print("Example 2: Display function name")
    print("=" * 70)

    formatter = PlainFormatter(fmt="%(asctime)s | %(levelname)-8s | [%(funcName)s] | %(message)s", datefmt="%H:%M:%S")

    logger = logging.getLogger("source_demo2")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def inner_function():
        logger.info("This log comes from inner_function")

    def another_function():
        logger.info("This log comes from another_function")

    logger.info("This log comes from example2_function_name")
    inner_function()
    another_function()


def example3_full_path():
    """Example 3: Display full path information"""
    print("\n" + "=" * 70)
    print("Example 3: Display full path information")
    print("=" * 70)

    formatter = PlainFormatter(
        fmt="%(asctime)s | %(levelname)-8s | [%(pathname)s:%(lineno)d:%(funcName)s] | %(message)s",
        datefmt="%H:%M:%S",
    )

    logger = logging.getLogger("source_demo3")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("Display full path, line number, and function name")


def example4_module_info():
    """Example 4: Display module information"""
    print("\n" + "=" * 70)
    print("Example 4: Display module information")
    print("=" * 70)

    formatter = PlainFormatter(
        fmt="%(asctime)s | %(name)s | %(module)s.%(funcName)s:%(lineno)d | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    logger = logging.getLogger("source_demo4")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.info("Display module name, function name, and line number")


def example5_compact_format():
    """Example 5: Compact format (suitable for development environment)"""
    print("\n" + "=" * 70)
    print("Example 5: Compact format (recommended for development)")
    print("=" * 70)

    # Compact but complete information format
    formatter = PlainFormatter(fmt="[%(levelname).1s] %(filename)s:%(lineno)d:%(funcName)s() | %(message)s")

    logger = logging.getLogger("source_demo5")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    def process_data():
        logger.debug("Starting to process data")
        logger.info("Data processing in progress...")
        logger.warning("Abnormal values detected")

    def validate_input():
        logger.info("Validating input")

    process_data()
    validate_input()


def example6_with_rich():
    """Example 6: Use Rich to display source information (colored)"""
    print("\n" + "=" * 70)
    print("Example 6: Rich colored source information")
    print("=" * 70)

    from advlog.handlers.console import create_console_handler

    # Rich's RichHandler automatically displays source information
    handler = create_console_handler(
        use_color=True,
        use_rich=True,
        log_level=logging.DEBUG,
    )

    logger = logging.getLogger("source_demo6")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.addHandler(handler)

    def api_handler():
        logger.info("API request processing - Rich will automatically show file name and line number")
        logger.debug("Validating token")

    def database_query():
        logger.info("Executing database query")
        logger.warning("Query taking too long")

    api_handler()
    database_query()

    print("\n✓ Rich's RichHandler automatically includes source information (file name and line number shown on the right)")


def example7_file_output_with_source():
    """Example 7: File output with source information"""
    print("\n" + "=" * 70)
    print("Example 7: File output with source information")
    print("=" * 70)

    from advlog.handlers.file import create_file_handler

    # Create file handler
    handler = create_file_handler(
        log_file="logs/source_info.log",
        mode="w",  # Overwrite mode
        log_level=logging.DEBUG,
    )

    # Custom format - includes detailed source information
    formatter = PlainFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | [%(filename)s:%(lineno)d:%(funcName)s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    logger = logging.getLogger("source_demo7")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.addHandler(handler)

    # Also add console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    def main_process():
        logger.info("Starting main process")
        sub_process()

    def sub_process():
        logger.debug("Executing subprocess")
        logger.info("Subprocess completed")

    main_process()
    logger.info("All processes completed")

    print("\n✓ Log written to: logs/source_info.log")


def example8_advanced_logger_with_source():
    """Example 8: Use AdvancedLogger to configure source information"""
    print("\n" + "=" * 70)
    print("Example 8: AdvancedLogger with source information")
    print("=" * 70)

    # Method 1: Configure through LoggerConfig
    config = LoggerConfig(
        name="advanced_source",
        log_file="logs/advanced_source.log",
        log_level="DEBUG",
        console_output=True,
        use_color=False,  # Use plain format for customization
    )

    logger_obj = AdvancedLogger(config)
    logger = logger_obj.get_logger()

    # Modify formatter to include source information
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            formatter = PlainFormatter(
                fmt="%(asctime)s | %(levelname)-8s | [%(filename)s:%(funcName)s:%(lineno)d] | %(message)s",
                datefmt="%H:%M:%S",
            )
            handler.setFormatter(formatter)

    def calculate():
        logger.debug("Starting calculation")
        result = 42
        logger.info(f"Calculation result: {result}")
        return result

    def save_result(data):
        logger.info(f"Saving result: {data}")
        logger.debug("Write completed")

    result = calculate()
    save_result(result)

    print("\n✓ Log written to: logs/advanced_source.log")


def example9_custom_source_formatter():
    """Example 9: Custom source information formatter"""
    print("\n" + "=" * 70)
    print("Example 9: Custom source information formatter")
    print("=" * 70)

    class SourceFormatter(logging.Formatter):
        """Custom formatter, intelligently displays source information"""

        def format(self, record):
            # Short path name (only show last two levels)
            path_parts = record.pathname.replace("\\", "/").split("/")
            short_path = "/".join(path_parts[-2:]) if len(path_parts) >= 2 else record.pathname

            # Custom format
            record.short_path = short_path
            record.location = f"{short_path}:{record.lineno}:{record.funcName}()"

            # Use custom fields
            fmt = "%(asctime)s | %(levelname)-8s | [%(location)s] | %(message)s"
            formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")
            return formatter.format(record)

    logger = logging.getLogger("source_demo9")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(SourceFormatter())
    logger.addHandler(handler)

    def test_function():
        logger.info("Using custom formatter")

    logger.info("Main function log")
    test_function()


def example10_production_format():
    """Example 10: Production environment recommended format"""
    print("\n" + "=" * 70)
    print("Example 10: Production environment recommended format")
    print("=" * 70)

    # Console: concise format
    console_formatter = PlainFormatter(fmt="%(asctime)s | %(levelname).1s | %(name)s | %(message)s", datefmt="%H:%M:%S")

    # File: detailed format (includes source information)
    file_formatter = PlainFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | [%(filename)s:%(lineno)d:%(funcName)s] | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("production")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # Console handler (concise)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)  # Console only shows INFO and above
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (detailed)
    from advlog.handlers.file import create_file_handler

    file_handler = create_file_handler(log_file="logs/production.log", mode="w", log_level=logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    def api_endpoint():
        logger.debug("DEBUG information (only in file)")
        logger.info("INFO information (console + file)")
        logger.warning("WARNING information (console + file)")

    api_endpoint()

    print("\n✓ Console: concise format")
    print("✓ File: detailed format (with source information) - logs/production.log")


# Run all examples
if __name__ == "__main__":
    print("=" * 70)
    print("🔍 Log source information display feature demonstration")
    print("=" * 70)

    examples = [
        example1_basic_source_info,
        example2_function_name,
        example3_full_path,
        example4_module_info,
        example5_compact_format,
        example6_with_rich,
        example7_file_output_with_source,
        example8_advanced_logger_with_source,
        example9_custom_source_formatter,
        example10_production_format,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n[Error] {example.__name__}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("✅ All examples completed!")
    print("=" * 70)
    print("\n📝 Common format variables:")
    print("  - %(filename)s    : File name")
    print("  - %(pathname)s    : Full path")
    print("  - %(module)s      : Module name")
    print("  - %(funcName)s    : Function name")
    print("  - %(lineno)d      : Line number")
    print("  - %(levelname)s   : Log level")
    print("  - %(name)s        : Logger name")
    print("  - %(message)s     : Log message")
    print("\n💡 Recommended formats:")
    print("  Development: [%(levelname).1s] %(filename)s:%(lineno)d:%(funcName)s() | %(message)s")
    print("  Production: %(asctime)s | %(levelname)-8s | [%(filename)s:%(lineno)d] | %(message)s")
    print("=" * 70)
