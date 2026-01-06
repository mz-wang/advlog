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

"""Main entry point - initialize logging and run workflow.

This is the entry point for the real-world demo. It demonstrates:
1. Initializing the global logging system
2. Getting a logger for the current module
3. Running a multi-step workflow with progress tracking
4. Cross-module logging with shared singleton

Usage:
    python -m examples.real_world_demo.main
"""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from advlog import get_logger, get_progress, initialize


def main():
    """Main workflow function."""
    # Initialize logging with file location info
    #
    # IMPORTANT: For breakpoint continue, you MUST specify the exact log file path!
    #
    # Example 1: Normal usage (auto-generate filename with timestamp)
    # initialize(
    #     output_dir="./logs",
    #     session_name="demo_workflow",
    #     log_level="DEBUG",
    #     show_location=True,
    # )
    #
    # Example 2: Breakpoint continue (specify exact file to append to)
    # initialize(
    #     log_file="./logs/2026-01-02/20260102_102551_demo_workflow.log",  # TARGET SPECIFIC FILE
    #     file_mode="a"  # Append to this file
    # )
    #
    # Example 3: Force overwrite mode
    # initialize(
    #     session_name="demo_workflow",
    #     file_mode="w"  # Overwrite existing log file
    # )
    #
    initialize(
        output_dir="./logs",
        session_name="demo_workflow",
        log_level="DEBUG",
        show_location=True,
        log_file="D:/Workspace/m_wang/codelib/advlog/logs/breakpoint_test.log",
        file_mode="a",
    )

    log = get_logger(__name__)
    log.info("=" * 60)
    log.info("Starting real-world demo workflow")
    log.info("=" * 60)

    # Import modules after initialization to ensure they get the same logger
    from examples.real_world_demo import data_loader, error_handler, processor, reporter

    # Get global progress tracker
    progress = get_progress()

    # Run workflow with progress tracking
    with progress:
        # Step 1: Load data
        log.info("Step 1: Loading data...")
        data = data_loader.load_data(progress)

        # Step 2: Process data with error handling
        log.info("Step 2: Processing data...")
        result = processor.process(data, progress)

        # Step 3: Demonstrate error handling
        log.info("Step 3: Demonstrating error handling...")
        log.info("-" * 60)

        # Test 1: Valid data processing
        log.info("Test 1: Processing valid data...")
        valid_result = error_handler.process_with_error_handling(data)
        log.info(f"Result: {valid_result['status']}")

        # Test 2: Invalid data (missing files)
        log.info("\nTest 2: Processing invalid data (missing files)...")
        invalid_data = {"users.csv": {"rows": 100, "columns": 10}}
        invalid_result = error_handler.process_with_error_handling(invalid_data)
        log.info(f"Result: {invalid_result['status']}")
        if invalid_result["status"] == "error":
            log.info(f"Error: {invalid_result['error_message']}")

        # Test 3: Empty data
        log.info("\nTest 3: Processing empty data...")
        empty_result = error_handler.process_with_error_handling({})
        log.info(f"Result: {empty_result['status']}")
        if empty_result["status"] == "error":
            log.info(f"Error: {empty_result['error_message']}")

        log.info("-" * 60)

        # Step 4: Generate report
        log.info("Step 4: Generating report...")
        reporter.generate_report(result, progress)

    log.info("=" * 60)
    log.info("Workflow completed successfully!")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
