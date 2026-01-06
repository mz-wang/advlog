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

"""Data processing module.

Demonstrates using advlog's get_logger in a processing module.
Shows how to log at different levels and track progress for long-running tasks.
"""
import time

from advlog import get_logger

# Get logger for this module
log = get_logger(__name__)


def process(data, progress):
    """Process loaded data.

    Args:
        data: Data dictionary from data_loader
        progress: ProgressTracker instance

    Returns:
        dict: Processing results
    """
    log.info("Starting data processing")

    total_rows = sum(file_data["rows"] for file_data in data.values())
    log.debug(f"Total rows to process: {total_rows}")

    task = progress.add_task("Processing data", total=100)

    results = {
        "processed_files": 0,
        "total_rows": 0,
        "errors": 0,
    }

    for i, (filename, file_data) in enumerate(data.items()):
        log.debug(f"Processing: {filename}")

        # Simulate processing
        for step in range(5):
            time.sleep(0.1)
            progress.update(task, advance=100 / (len(data) * 5))

        results["processed_files"] += 1
        results["total_rows"] += file_data["rows"]

        # Simulate occasional warning
        if file_data["rows"] > 300:
            log.warning(f"Large file detected: {filename} ({file_data['rows']} rows)")

    progress.remove_task(task)

    log.info(
        f"Processing complete: {results['processed_files']} files, "
        f"{results['total_rows']} rows processed"
    )

    return results
