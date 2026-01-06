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

"""Error handling and validation module.

Demonstrates how to catch, log, and handle errors properly with advlog.
Shows structured error logging with context and validation.
"""
import time

from advlog import get_logger, get_progress

# Get logger for this module
log = get_logger(__name__)


def validate_data(data):
    """Validate data with proper error handling.

    Args:
        data: Data dictionary to validate

    Returns:
        bool: True if valid

    Raises:
        ValueError: If data is invalid
    """
    log.info("Starting data validation")

    task = get_progress().add_task("Validating data", total=3)

    try:
        # Check if data exists
        log.debug("Checking if data exists...")
        time.sleep(0.2)
        if not data:
            raise ValueError("Data is empty")
        get_progress().update(task, advance=1)

        # Check required fields
        log.debug("Checking required fields...")
        time.sleep(0.2)
        required_fields = ["users.csv", "products.csv"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required files: {', '.join(missing)}")
        get_progress().update(task, advance=1)

        # Check data integrity
        log.debug("Checking data integrity...")
        time.sleep(0.2)
        for filename, file_data in data.items():
            if not isinstance(file_data, dict) or "rows" not in file_data:
                raise ValueError(f"Invalid data structure in {filename}")
            if file_data["rows"] <= 0:
                raise ValueError(f"Invalid row count in {filename}: {file_data['rows']}")

        get_progress().update(task, advance=1)
        get_progress().remove_task(task)

        log.info("Data validation successful")
        return True

    except ValueError as e:
        get_progress().remove_task(task)
        log.error(f"Validation failed: {e}")
        raise


def process_with_error_handling(data):
    """Process data with comprehensive error handling.

    Args:
        data: Data dictionary to process

    Returns:
        dict: Processing results or None if failed
    """
    log.info("Starting processing with error handling")

    try:
        # Validate data first
        log.debug("Validating input data...")
        validate_data(data)

        # Simulate processing that might fail
        log.debug("Simulating data processing...")
        time.sleep(0.3)

        # Simulate a potential error condition
        total_rows = sum(file_data["rows"] for file_data in data.values())
        if total_rows > 1000:
            log.warning(f"Large dataset detected: {total_rows} rows")

        # Simulate processing errors
        for filename, file_data in data.items():
            if file_data["rows"] > 400:
                log.warning(f"Large file may cause performance issues: {filename}")
                # In a real scenario, you might handle this differently

        log.info("Processing completed successfully")
        return {
            "status": "success",
            "processed_files": len(data),
            "total_rows": total_rows,
            "warnings": 0,
        }

    except ValueError as e:
        log.error(f"Processing failed due to validation error: {e}", exc_info=True)
        return {
            "status": "error",
            "error_type": "ValidationError",
            "error_message": str(e),
        }
    except Exception as e:
        log.critical(f"Unexpected error during processing: {e}", exc_info=True)
        return {
            "status": "error",
            "error_type": "UnexpectedError",
            "error_message": str(e),
        }


def recover_from_error(error_info):
    """Attempt to recover from an error.

    Args:
        error_info: Error information dictionary

    Returns:
        bool: True if recovery successful
    """
    log.info(f"Attempting to recover from error: {error_info.get('error_type')}")

    task = get_progress().add_task("Recovering from error", total=3)

    try:
        # Analyze error
        log.debug("Analyzing error type...")
        time.sleep(0.2)
        error_type = error_info.get("error_type")

        if error_type == "ValidationError":
            log.info("Attempting to fix validation issues...")
            time.sleep(0.2)
            get_progress().update(task, advance=1)

            # Attempt to recover
            log.info("Applying recovery strategy...")
            time.sleep(0.2)
            get_progress().update(task, advance=1)

            # Validate recovery
            log.debug("Verifying recovery...")
            time.sleep(0.2)
            get_progress().update(task, advance=1)

            log.info("Recovery successful")
            get_progress().remove_task(task)
            return True

        else:
            log.error(f"Cannot recover from error type: {error_type}")
            get_progress().remove_task(task)
            return False

    except Exception as e:
        log.error(f"Recovery attempt failed: {e}", exc_info=True)
        get_progress().remove_task(task)
        return False
