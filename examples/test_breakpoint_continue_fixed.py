#!/usr/bin/env python3
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

"""
Test script to demonstrate CORRECT breakpoint continue functionality.

This demonstrates:
1. Creating a log file
2. Continuing to the SAME log file by specifying its exact path
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import os

from advlog import get_logger, initialize


def test_correct_breakpoint_continue():
    """Test breakpoint continue with specific file path."""
    print("=" * 70)
    print("Testing BREAKPOINT CONTINUE (Correct Implementation)")
    print("=" * 70)
    print()

    # Step 1: Create a specific log file
    log_file_path = "./logs/breakpoint_test.log"
    print(f"Step 1: Creating log file: {log_file_path}")
    initialize(
        log_file=log_file_path,  # Specify exact file path
        file_mode="w",  # Overwrite to create new file
    )
    log = get_logger(__name__)
    log.info("=== FIRST RUN ===")
    log.info("This is the first run - creating a new log file")
    log.info("=" * 70)
    print(f"[OK] Created: {log_file_path}")
    print()

    # Check file size
    size_after_first = os.path.getsize(log_file_path)
    print(f"File size after first run: {size_after_first} bytes")
    print()

    # Step 2: Continue to the SAME file
    print("Step 2: Continuing to the same file (breakpoint continue)")
    initialize(
        log_file=log_file_path,  # SAME file path
        file_mode="a",  # Append mode
    )
    log = get_logger(__name__)
    log.info("=== SECOND RUN (BREAKPOINT CONTINUE) ===")
    log.info("This is the second run - continuing from where we left off")
    log.info("=" * 70)
    print(f"[OK] Continued to: {log_file_path}")
    print()

    # Check file size
    size_after_second = os.path.getsize(log_file_path)
    print(f"File size after second run: {size_after_second} bytes")
    print(f"Added: {size_after_second - size_after_first} bytes")
    print()

    # Display the log file content
    print("Content of the log file:")
    print("-" * 70)
    with open(log_file_path, encoding="utf-8") as f:
        content = f.read()
        print(content)
    print("-" * 70)
    print()

    # Verify the content
    if "FIRST RUN" in content and "SECOND RUN" in content:
        print("[SUCCESS] Both runs are in the same file.")
        print("[SUCCESS] Breakpoint continue works correctly!")
        return True
    else:
        print("[FAILED] Content not found in the same file.")
        return False


if __name__ == "__main__":
    success = test_correct_breakpoint_continue()
    sys.exit(0 if success else 1)
