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

"""Progress bar management - auto cleanup and lifecycle management."""

from typing import Dict, Optional

from rich.progress import Progress, TaskID

from advlog.utils.console import get_shared_console
from advlog.utils.rich_compat import RICH_AVAILABLE, Console


class ProgressTracker:
    """Progress tracker with auto cleanup and lifecycle management.

    Provides advanced progress bar management:
    - Auto-remove completed tasks
    - Keep important tasks
    - Dynamic task management
    - Work with logging

    Usage:
        with ProgressTracker(auto_remove_completed=True) as progress:
            task = progress.add_task("Processing", total=100)
            for i in range(100):
                progress.update(task, advance=1)
            # Auto-removed after completion
    """

    def __init__(
        self,
        console: Optional["Console"] = None,
        transient: bool = False,
        auto_remove_completed: bool = False,
        keep_recent: int = 0,  # Keep N recent completed tasks, 0 = don't keep
    ):
        """Initialize progress tracker.

        Args:
            console: Rich Console instance
            transient: Auto-clear progress bar after completion
            auto_remove_completed: Auto-remove completed tasks
            keep_recent: Keep N recent completed tasks (0 = don't keep)
        """
        if not RICH_AVAILABLE:
            raise ImportError("Rich is required. Install with: pip install rich")

        if console is None:
            console = get_shared_console()

        self.console = console
        self.transient = transient
        self.auto_remove_completed = auto_remove_completed
        self.keep_recent = keep_recent

        # Import Progress components
        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            SpinnerColumn,
            TaskProgressColumn,
            TextColumn,
            TimeElapsedColumn,
            TimeRemainingColumn,
        )

        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[cyan]{task.description}"),
            MofNCompleteColumn(),
            BarColumn(),
            TaskProgressColumn("[progress.percentage]{task.percentage:>3.2f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=transient,
        )

        # Track task status
        self.tasks: Dict[TaskID, dict] = {}
        self.persistent_tasks: set = set()  # Tasks to keep
        self.completed_tasks: list = []  # Completed task history

    def __enter__(self):
        """Enter context manager."""
        self.progress.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        return self.progress.__exit__(exc_type, exc_val, exc_tb)

    def add_task(
        self,
        description: str,
        total: Optional[float] = 100.0,
        persistent: bool = False,
        **kwargs,
    ) -> TaskID:
        """Add a task.

        Args:
            description: Task description
            total: Total amount
            persistent: Keep (not auto-remove)
            **kwargs: Additional args passed to Progress.add_task

        Returns:
            Task ID
        """
        task_id = self.progress.add_task(description, total=total, **kwargs)

        # Record task info
        self.tasks[task_id] = {
            "description": description,
            "total": total,
            "persistent": persistent,
            "completed": False,
        }

        if persistent:
            self.persistent_tasks.add(task_id)

        return task_id

    def update(self, task_id: TaskID, **kwargs):
        """Update task progress.

        Args:
            task_id: Task ID
            **kwargs: Args passed to Progress.update
        """
        self.progress.update(task_id, **kwargs)

        # Check if task is completed
        if self.auto_remove_completed and task_id in self.tasks:
            # Get task object
            task = None
            for t in self.progress.tasks:
                if t.id == task_id:
                    task = t
                    break

            if task and task.finished and not self.tasks[task_id]["completed"]:
                self.tasks[task_id]["completed"] = True

                # If not persistent task, remove it
                if task_id not in self.persistent_tasks:
                    self._auto_remove_task(task_id)

    def _auto_remove_task(self, task_id: TaskID):
        """Auto-remove completed task.

        Args:
            task_id: Task ID
        """
        # Add to completed history
        self.completed_tasks.append(task_id)

        # Check if need to keep
        if self.keep_recent > 0:
            # Only remove tasks beyond keep count
            if len(self.completed_tasks) > self.keep_recent:
                # Remove earliest completed task
                oldest_task = self.completed_tasks[0]
                if oldest_task in self.tasks:
                    self.progress.remove_task(oldest_task)
                    del self.tasks[oldest_task]
                    self.completed_tasks.pop(0)
        else:
            # Remove immediately
            if task_id in self.tasks:
                self.progress.remove_task(task_id)
                del self.tasks[task_id]

    def remove_task(self, task_id: TaskID):
        """Manually remove task.

        Args:
            task_id: Task ID
        """
        if task_id in self.tasks:
            self.progress.remove_task(task_id)
            del self.tasks[task_id]
            if task_id in self.persistent_tasks:
                self.persistent_tasks.remove(task_id)

    def mark_persistent(self, task_id: TaskID):
        """Mark task as persistent (won't auto-remove).

        Args:
            task_id: Task ID
        """
        if task_id in self.tasks:
            self.tasks[task_id]["persistent"] = True
            self.persistent_tasks.add(task_id)

    def unmark_persistent(self, task_id: TaskID):
        """Remove persistent mark from task.

        Args:
            task_id: Task ID
        """
        if task_id in self.tasks:
            self.tasks[task_id]["persistent"] = False
            if task_id in self.persistent_tasks:
                self.persistent_tasks.remove(task_id)

    def log(self, message: str, **kwargs):
        """Log message (shown above progress bar).

        Args:
            message: Log message
            **kwargs: Args passed to console.log
        """
        self.console.log(message, **kwargs)

    def get_task_info(self, task_id: TaskID) -> Optional[dict]:
        """Get task info.

        Args:
            task_id: Task ID

        Returns:
            Task info dict, or None if task doesn't exist
        """
        return self.tasks.get(task_id)

    def get_active_tasks(self) -> Dict[TaskID, dict]:
        """Get all active tasks.

        Returns:
            Active tasks dict
        """
        return {tid: info for tid, info in self.tasks.items() if not info["completed"]}

    def get_completed_count(self) -> int:
        """Get completed task count.

        Returns:
            Completed task count
        """
        return len(self.completed_tasks)


def create_progress_bar(
    auto_remove_completed: bool = False,
    keep_recent: int = 0,
    transient: bool = False,
    console: Optional["Console"] = None,
) -> ProgressTracker:
    """Create a progress tracker.

    Args:
        auto_remove_completed: Auto-remove completed tasks
        keep_recent: Keep N recent completed tasks
        transient: Auto-clear after completion
        console: Rich Console instance

    Returns:
        ProgressTracker instance

    Example:
        # Auto-remove completed tasks
        with create_progress_bar(auto_remove_completed=True) as progress:
            task = progress.add_task("Processing", total=100)
            for i in range(100):
                progress.update(task, advance=1)

        # Keep recent 3 completed tasks
        with create_progress_bar(keep_recent=3) as progress:
            for i in range(10):
                task = progress.add_task(f"Task {i}", total=10)
                for j in range(10):
                    progress.update(task, advance=1)
    """
    return ProgressTracker(
        console=console,
        transient=transient,
        auto_remove_completed=auto_remove_completed,
        keep_recent=keep_recent,
    )
