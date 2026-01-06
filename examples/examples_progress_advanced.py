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

"""Advanced progress bar examples - working with logging.

Demonstrates various scenarios of progress bars with logging.
"""

import sys
import time

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

from advlog.core import AdvancedLogger, LoggerConfig
from advlog.plugins import ProgressTracker, create_progress_bar


def example1_basic_progress_with_logging():
    """Example 1: Progress bar at bottom, logs scrolling above"""
    print("\n" + "=" * 70)
    print("Example 1: Progress Bar + Logging (bar stays at bottom)")
    print("=" * 70)

    # Create logger (without Rich handler to avoid conflicts)
    config = LoggerConfig(
        name="ProgressExample1",
        log_file="logs/progress_example1.log",
        console_output=False,  # Disable default console output
        use_color=True,
    )
    logger = AdvancedLogger(config).get_logger()

    # Create progress bar
    progress = ProgressTracker()

    # Start progress bar context
    with progress:
        task1 = progress.add_task("[cyan]Downloading files...", total=50)
        task2 = progress.add_task("[green]Processing data...", total=100)

        for i in range(100):
            # Update progress
            if i < 50:
                progress.update(task1, advance=1)
            progress.update(task2, advance=1)

            # Output logs simultaneously (shown above progress bar)
            if i % 20 == 0:
                progress.console.log(f"[blue]Processed {i} items")

            time.sleep(0.05)

    print("\n✓ Progress bar auto-disappears after completion, logs preserved")
    print("✓ Progress bar stays at bottom, logs scroll above")


def example2_persistent_progress():
    """Example 2: Persistent progress bar (doesn't disappear after completion)"""
    print("\n" + "=" * 70)
    print("Example 2: Persistent Progress Bar (transient=False)")
    print("=" * 70)

    # Create persistent progress bar (doesn't auto-clear after completion)
    progress = create_progress_bar(
        transient=False,  # Don't clear after completion
    )

    with progress:
        task1 = progress.add_task("[cyan]Task 1", total=30)
        task2 = progress.add_task("[green]Task 2", total=50)

        # Complete task 1
        for i in range(30):
            progress.update(task1, advance=1)
            if i % 10 == 0:
                progress.console.log(f"[blue]Task 1 progress: {i}/30")
            time.sleep(0.03)

        progress.console.log("[green]✓ Task 1 completed")

        # Complete task 2
        for i in range(50):
            progress.update(task2, advance=1)
            if i % 15 == 0:
                progress.console.log(f"[blue]Task 2 progress: {i}/50")
            time.sleep(0.02)

        progress.console.log("[green]✓ Task 2 completed")

    print("\n✓ All progress bars remain displayed")
    print("✓ Can see final state of completed tasks")


def example3_auto_remove_completed():
    """Example 3: Auto-remove completed progress bars"""
    print("\n" + "=" * 70)
    print("Example 3: Auto-Remove Completed Progress Bars")
    print("=" * 70)

    progress = create_progress_bar(transient=False)

    with progress:
        # Create multiple tasks
        tasks = []
        for i in range(1, 4):
            task = progress.add_task(f"[cyan]Task {i}", total=20)
            tasks.append((task, f"Task {i}"))

        # Complete tasks one by one
        for task_id, task_name in tasks:
            progress.console.log(f"[yellow]Starting {task_name}")

            for i in range(20):
                progress.update(task_id, advance=1)
                time.sleep(0.05)

            progress.console.log(f"[green]✓ {task_name} completed")

            # Manually remove completed task
            progress.remove_task(task_id)
            progress.console.log(f"[dim]Removed progress bar for {task_name}")

            time.sleep(0.5)

    print("\n✓ Completed progress bars are auto-removed")
    print("✓ Only showing tasks in progress")


def example4_mixed_strategies():
    """Example 4: Mixed strategies - keep important, remove temporary"""
    print("\n" + "=" * 70)
    print("Example 4: Mixed Strategies - Keep Important, Remove Temporary")
    print("=" * 70)

    progress = create_progress_bar(transient=False)

    with progress:
        # Important task - keep displayed
        important_task = progress.add_task("[red bold]Main Task (persistent)", total=100)

        # Temporary tasks
        temp_tasks = []
        for i in range(1, 4):
            task = progress.add_task(f"[cyan]Subtask {i} (temporary)", total=30)
            temp_tasks.append(task)

        # Execution flow
        for i in range(100):
            # Update main task
            progress.update(important_task, advance=1)

            # Update and complete subtasks
            for idx, temp_task in enumerate(temp_tasks):
                if i < 30:
                    progress.update(temp_task, advance=1)
                elif i == 30 + idx * 5:
                    # Remove temporary task after completion
                    progress.remove_task(temp_task)
                    progress.console.log(f"[dim]✓ Subtask {idx + 1} completed and removed")

            if i % 25 == 0:
                progress.console.log(f"[blue]Main task progress: {i}%")

            time.sleep(0.03)

    print("\n✓ Main task remains displayed")
    print("✓ Subtasks auto-removed after completion")


def example5_logger_integration():
    """Example 5: Integration with LoggerManager"""
    print("\n" + "=" * 70)
    print("Example 5: Progress Bar + LoggerManager Integration")
    print("=" * 70)

    from core import LoggerManager

    # Note: Don't use shared_console to avoid conflicts with Progress
    manager = LoggerManager(shared_console=False)

    # Create loggers for different modules, output to files
    api_logger = manager.register_logger(
        "API", file_strategy="separate", log_file="logs/progress_api.log", use_console=False
    )

    db_logger = manager.register_logger(
        "Database", file_strategy="separate", log_file="logs/progress_db.log", use_console=False
    )

    # Create progress bar
    progress = create_progress_bar(transient=False)

    with progress:
        task1 = progress.add_task("[cyan]API Request Processing", total=50)
        task2 = progress.add_task("[green]Database Operations", total=30)

        for i in range(50):
            progress.update(task1, advance=1)

            # Use progress.console.log to output to console (no conflict)
            if i % 10 == 0:
                progress.console.log(f"[blue]API: Processing request {i}/50")
                # Also write to log file
                api_logger.info(f"Processing request {i}/50")

            if i < 30:
                progress.update(task2, advance=1)
                if i % 10 == 0:
                    progress.console.log(f"[green]DB: Executing query {i}/30")
                    db_logger.info(f"Executing query {i}/30")

            time.sleep(0.05)

        progress.console.log("[green]✓ All tasks completed")

    print("\n✓ Progress bar displayed in console")
    print("✓ Detailed logs written to files")
    print("✓ No output conflicts")


def example6_dynamic_task_management():
    """Example 6: Dynamic task management - add/remove tasks at runtime"""
    print("\n" + "=" * 70)
    print("Example 6: Dynamic Task Management")
    print("=" * 70)

    progress = create_progress_bar(transient=False)

    with progress:
        active_tasks = {}

        # Simulate dynamic workflow
        for round in range(1, 4):
            progress.console.log(f"[yellow bold]Starting round {round}")

            # Dynamically add task
            task_id = progress.add_task(f"[cyan]Round {round} Task", total=20)
            active_tasks[round] = task_id

            # Process task
            for i in range(20):
                progress.update(task_id, advance=1)
                time.sleep(0.05)

            progress.console.log(f"[green]✓ Round {round} completed")

            # Decide whether to remove based on strategy
            if round < 3:
                # Remove completed old task
                progress.remove_task(task_id)
                progress.console.log(f"[dim]  Removed round {round} progress bar")
            else:
                # Keep the last task
                progress.console.log(f"[yellow]  Kept round {round} progress bar")

            time.sleep(0.5)

    print("\n✓ Dynamically add and remove tasks")
    print("✓ Flexible control over display content")


def example7_nested_progress():
    """Example 7: Nested progress - overall + subtask progress"""
    print("\n" + "=" * 70)
    print("Example 7: Nested Progress Display")
    print("=" * 70)

    progress = create_progress_bar(transient=False)

    with progress:
        # Overall progress (persistent)
        total_task = progress.add_task("[red bold]Overall Progress", total=100)

        # Process multiple stages
        stages = ["Data Preparation", "Model Training", "Result Evaluation"]

        for stage_idx, stage_name in enumerate(stages):
            progress.console.log(f"\n[yellow bold]Stage {stage_idx + 1}: {stage_name}")

            # Stage task (temporary)
            stage_task = progress.add_task(f"[cyan]{stage_name}", total=30)

            for i in range(30):
                # Update stage progress
                progress.update(stage_task, advance=1)

                # Update overall progress
                progress.update(total_task, advance=1)

                if i % 10 == 0:
                    progress.console.log(f"  [dim]{stage_name}: {i}/30")

                time.sleep(0.03)

            # Remove stage task
            progress.remove_task(stage_task)
            progress.console.log(f"[green]✓ {stage_name} completed")
            time.sleep(0.3)

        progress.console.log("\n[green bold]✓ All stages completed!")

    print("\n✓ Overall progress remains displayed")
    print("✓ Subtasks removed after completion")


def run_all_examples():
    """Run all examples"""
    examples = [
        example1_basic_progress_with_logging,
        example2_persistent_progress,
        example3_auto_remove_completed,
        example4_mixed_strategies,
        example5_logger_integration,
        example6_dynamic_task_management,
        example7_nested_progress,
    ]

    for example in examples:
        try:
            example()
            time.sleep(1)  # Pause between examples
        except Exception as e:
            print(f"\n[Error] {example.__name__}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("All progress bar examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
