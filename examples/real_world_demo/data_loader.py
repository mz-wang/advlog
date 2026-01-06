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

"""Data loading module.

Demonstrates using advlog's get_logger and get_progress in a separate module.
The logger is automatically shared with the main module via the global singleton.
"""
import time

from advlog import get_logger

# Get logger for this module - uses the same LoggerManager as main.py
log = get_logger(__name__)


def load_data(progress):
    """Load data from multiple sources.

    Args:
        progress: ProgressTracker instance for displaying progress

    Returns:
        dict: Loaded data
    """
    log.info("Starting data loading process")

    # Simulate loading multiple files
    files = [
        "users.csv",
        "products.csv",
        "orders.csv",
        "reviews.csv",
        "inventory.csv",
    ]

    task = progress.add_task("Loading files", total=len(files))

    data = {}
    for i, filename in enumerate(files):
        log.debug(f"Loading file: {filename}")
        time.sleep(0.2)  # Simulate file loading

        # Simulate loaded data
        data[filename] = {"rows": 100 * (i + 1), "columns": 10}

        log.debug(f"Loaded {data[filename]['rows']} rows from {filename}")
        progress.update(task, advance=1)

    progress.remove_task(task)
    log.info(f"Data loading complete: {len(files)} files loaded")

    return data
