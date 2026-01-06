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
Test script to demonstrate breakpoint continue (append) functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Find the latest log file
import glob
import os

from advlog import get_logger, initialize

log_files = glob.glob("logs/logs/2026-01-02/*demo_workflow.log")
if not log_files:
    print("No existing log file found. Creating a new one...")
    latest_log = None
else:
    latest_log = max(log_files, key=os.path.getctime)
    print(f"Found existing log file: {latest_log}")
    print(f"Size before: {os.path.getsize(latest_log)} bytes")

print("\n" + "=" * 70)
print("Testing Breakpoint Continue (Append Mode)")
print("=" * 70)
print("\nInitializing logger with same session_name...")
print("This will append to the existing log file.\n")

# Use same session_name to target the same file
initialize(
    output_dir="./logs",
    session_name="demo_workflow",  # Same session_name = same file
    log_level="INFO",
    show_location=True,
    # file_mode="a" is default, so we don't need to specify it
)

log = get_logger(__name__)
log.info("=" * 70)
log.info("BREAKPOINT CONTINUE TEST - This entry was appended!")
log.info("If you see this in the log file, the feature works correctly.")
log.info("=" * 70)

if latest_log:
    print("\n[OK] New log entries written!")
    print(f"Size after: {os.path.getsize(latest_log)} bytes")
    print("\nLast 5 lines of the log file:")
    print("-" * 70)
    with open(latest_log, encoding="utf-8") as f:
        lines = f.readlines()
        for line in lines[-5:]:
            print(line.rstrip())
    print("-" * 70)
    print("\n[SUCCESS] Breakpoint continue (append mode) test PASSED!")
else:
    print("\n[SUCCESS] New log file created successfully!")
