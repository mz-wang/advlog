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

"""Examples demonstrating the usage of the Advanced Logging System.

Run this file to see various features in action:
    python examples.py
"""

import time

from advlog.core import AdvancedLogger, LoggerConfig
from advlog.plugins import ProgressTracker, TrainingLogger, create_progress_bar
from advlog.utils import detect_environment


def example_basic_logging():
    """Example 1: Basic logging usage."""
    print("\n" + "=" * 60)
    print("Example 1: Basic Logging")
    print("=" * 60)

    # Simple usage with defaults
    logger = AdvancedLogger().get_logger()
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")


def example_custom_configuration():
    """Example 2: Custom configuration."""
    print("\n" + "=" * 60)
    print("Example 2: Custom Configuration")
    print("=" * 60)

    config = LoggerConfig(
        name="MyApp",
        log_file="logs/example_app.log",
        log_level="DEBUG",
        use_color=True,
        separate_error_file="logs/example_errors.log",
        max_file_size=1024 * 1024,  # 1 MB
        backup_count=3,
    )

    logger = AdvancedLogger(config).get_logger()
    logger.info("Logger with custom configuration initialized")
    logger.debug("Debug messages are now visible")
    logger.error("Errors are also logged to separate file")


def example_multiple_loggers():
    """Example 3: Multiple logger instances."""
    print("\n" + "=" * 60)
    print("Example 3: Multiple Logger Instances")
    print("=" * 60)

    # Create separate loggers for different modules
    logger1 = AdvancedLogger(LoggerConfig(name="Module1", log_file="logs/module1.log", use_color=True)).get_logger()

    logger2 = AdvancedLogger(LoggerConfig(name="Module2", log_file="logs/module2.log", use_color=True)).get_logger()

    logger1.info("Message from Module 1")
    logger2.info("Message from Module 2")


def example_progress_tracking():
    """Example 4: Progress bar usage."""
    print("\n" + "=" * 60)
    print("Example 4: Progress Tracking")
    print("=" * 60)

    try:
        with ProgressTracker() as progress:
            # Task 1: Processing items
            task1 = progress.add_task("[cyan]Processing items...", total=50)
            for i in range(50):
                time.sleep(0.02)
                progress.update(task1, advance=1)

            # Task 2: Downloading files
            task2 = progress.add_task("[green]Downloading files...", total=30)
            for i in range(30):
                time.sleep(0.03)
                progress.update(task2, advance=1)

        print("Progress tracking completed!")
    except ImportError as e:
        print(f"Progress tracking requires Rich: {e}")


def example_custom_progress_bar():
    """Example 5: Custom progress bar."""
    print("\n" + "=" * 60)
    print("Example 5: Custom Progress Bar")
    print("=" * 60)

    try:
        # Create a custom progress bar
        progress = create_progress_bar(
            transient=True,  # Auto-clear when done
        )

        with progress:
            task = progress.add_task("Custom task", total=100)
            for i in range(100):
                time.sleep(0.01)
                progress.update(task, advance=1)

        print("Custom progress bar completed!")
    except ImportError as e:
        print(f"Progress bars require Rich: {e}")


def example_training_logger():
    """Example 6: Training logger for ML/DL."""
    print("\n" + "=" * 60)
    print("Example 6: Training Logger")
    print("=" * 60)

    # Setup logger
    logger = AdvancedLogger(
        LoggerConfig(name="TrainingExample", log_file="logs/training.log", use_color=True)
    ).get_logger()

    trainer = TrainingLogger(logger)

    # Log configuration
    config = {"learning_rate": 0.001, "batch_size": 32, "epochs": 10, "optimizer": "Adam"}
    trainer.log_configuration(config, title="Training Configuration")

    # Simulate training
    for epoch in range(1, 4):
        for batch in range(1, 6):
            loss_dict = {"loss": 1.0 / (epoch * batch), "accuracy": min(0.5 + (epoch * batch) * 0.05, 0.99)}
            trainer.log_train_step(
                epoch=epoch,
                total_epochs=3,
                batch=batch,
                total_batches=5,
                loss_dict=loss_dict,
                time_elapsed=0.5,
                csv_path="logs/training_metrics.csv",
            )
            time.sleep(0.1)

    # Log evaluation results
    trainer.log_evaluation_results({"accuracy": 0.95, "f1_score": 0.93, "precision": 0.94}, epoch=3)


def example_environment_detection():
    """Example 7: Environment detection."""
    print("\n" + "=" * 60)
    print("Example 7: Environment Detection")
    print("=" * 60)

    env_info = detect_environment()

    print("Environment Information:")
    for key, value in env_info.items():
        print(f"  {key}: {value}")


def example_exception_logging():
    """Example 8: Exception logging."""
    print("\n" + "=" * 60)
    print("Example 8: Exception Logging")
    print("=" * 60)

    from advlog.core.logger import setup_exception_logging

    logger = AdvancedLogger(LoggerConfig(name="ExceptionExample", log_file="logs/exceptions.log")).get_logger()

    setup_exception_logging(logger)

    # This exception will be automatically logged
    try:
        raise ValueError("This is a test exception")
    except ValueError:
        logger.exception("Caught exception:")


def example_no_color_mode():
    """Example 9: Logging without colors."""
    print("\n" + "=" * 60)
    print("Example 9: No-Color Mode")
    print("=" * 60)

    config = LoggerConfig(
        name="NoColorLogger",
        log_file="logs/no_color.log",
        use_color=False,  # Disable colors
        console_output=True,
    )

    logger = AdvancedLogger(config).get_logger()
    logger.info("This message has no color")
    logger.warning("This warning has no color")
    logger.error("This error has no color")


def example_json_logging():
    """Example 10: JSON format logging."""
    print("\n" + "=" * 60)
    print("Example 10: JSON Format Logging")
    print("=" * 60)

    import logging

    from advlog.core.formatter import JSONFormatter

    # Create a logger with JSON formatter
    logger = logging.getLogger("JSONLogger")
    logger.setLevel(logging.DEBUG)

    # Create a handler with JSON formatter
    handler = logging.FileHandler("logs/json_logs.log", mode="w", encoding="utf-8")
    handler.setFormatter(JSONFormatter(include_extras=True))
    logger.addHandler(handler)

    logger.info("Regular message")
    logger.warning("Warning with extra data", extra={"user_id": 123, "action": "login"})
    logger.error("Error occurred", extra={"error_code": 500})

    print("JSON logs written to logs/json_logs.log")


def run_all_examples():
    """Run all examples."""
    examples = [
        example_basic_logging,
        example_custom_configuration,
        example_multiple_loggers,
        example_progress_tracking,
        example_custom_progress_bar,
        example_training_logger,
        example_environment_detection,
        example_exception_logging,
        example_no_color_mode,
        example_json_logging,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("Check the 'logs/' directory for log files.")
    print("=" * 60)


if __name__ == "__main__":
    run_all_examples()
