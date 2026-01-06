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

"""Minimal demo - Quick overview of core features in 3 minutes"""

import sys
import time

from advlog.plugins import ProgressTracker, create_progress_bar

if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

print("\n" + "=" * 70)
print("Core Features Demo - Quick Overview")
print("=" * 70)

# ============ Scenario 1: Progress bar at bottom, logs above ============
print("\n[Scenario 1] Progress bar stays at bottom, logs scroll above")
print("-" * 70)
time.sleep(1)


with ProgressTracker() as progress:
    task = progress.add_task("[cyan]Downloading files", total=20)

    for i in range(20):
        progress.update(task, advance=1)

        if i % 5 == 0:
            # Note: logs are displayed above the progress bar!
            progress.console.log(f"[blue]✓ Downloaded {i} files")

        time.sleep(0.1)

print("✓ Progress bar stays at bottom, logs above")
time.sleep(1)

# ============ Scenario 2: Auto-remove completed tasks ============
print("\n[Scenario 2] Auto-remove completed tasks")
print("-" * 70)
time.sleep(1)


with create_progress_bar(auto_remove_completed=True) as progress:
    for i in range(1, 4):
        task = progress.add_task(f"[cyan]Task {i}", total=8)

        for j in range(8):
            progress.update(task, advance=1)
            time.sleep(0.08)

        # Auto-removed after completion!
        progress.log(f"[green]✓ Task {i} completed [dim](auto-removed)")
        time.sleep(0.3)

print("✓ Completed tasks auto-disappear, clean interface")
time.sleep(1)

# ============ Scenario 3: Keep main task, remove subtasks ============
print("\n[Scenario 3] Mixed strategy: Keep main task, auto-remove subtasks")
print("-" * 70)
time.sleep(1)

with create_progress_bar(auto_remove_completed=True) as progress:
    # Main task - persistent=True, won't auto-remove
    main = progress.add_task(
        "[red bold]Overall Progress",
        total=30,
        persistent=True,  # Keep displayed
    )

    # 3 subtasks
    for i in range(1, 4):
        sub = progress.add_task(f"[cyan]Stage {i}", total=10)

        for j in range(10):
            progress.update(sub, advance=1)
            progress.update(main, advance=1)
            time.sleep(0.05)

        progress.log(f"[green]✓ Stage {i} completed [dim](auto-removed)")

    progress.log("[green bold]✓ All stages completed! Main task kept")

print("✓ Main task kept, subtasks auto-removed")
time.sleep(1)

# ============ Summary ============
print("\n" + "=" * 70)
print("Core Features Summary")
print("=" * 70)
print()
print("Requirement 1: Progress bar at bottom + logs above -> Done")
print("   - Progress bar stays at bottom")
print("   - Logs scroll above automatically")
print("   - Smooth updates, no flicker")
print()
print("Requirement 2: Flexible lifecycle management -> Done")
print("   - Auto-close: auto_remove_completed=True")
print("   - Manual close: progress.remove_task(task)")
print("   - Transient: transient=True")
print("   - Selective keep: persistent=True")
print()
print("More examples:")
print("   - python examples_progress_advanced.py - 7 detailed examples")
print()
print("=" * 70)
print("Demo complete! All features ready to use!")
print("=" * 70)
