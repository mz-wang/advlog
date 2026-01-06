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

"""Advanced examples demonstrating logger coordination and smart naming."""

import sys
import time

# Set UTF-8 encoding for Windows
if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

from advlog.core import LoggerManager, create_logger_group
from advlog.utils import LogNamingStrategy


def example_shared_console_separate_files():
    """Example 1: Multiple modules, shared console, separate files."""
    print("\n" + "=" * 70)
    print("Example 1: Shared Console + Separate Files")
    print("=" * 70)

    # Create manager with shared console
    manager = LoggerManager(shared_console=True, use_color=True)

    # Register loggers for different modules
    api_logger = manager.register_logger("API", file_strategy="separate", log_file="logs/advanced/api.log")

    db_logger = manager.register_logger("Database", file_strategy="separate", log_file="logs/advanced/database.log")

    auth_logger = manager.register_logger("Auth", file_strategy="separate", log_file="logs/advanced/auth.log")

    # All messages appear in console, but go to separate files
    api_logger.info("API server started on port 8000")
    db_logger.info("Connected to database: postgresql://localhost/mydb")
    auth_logger.info("Auth service initialized")

    api_logger.warning("High request rate detected")
    db_logger.error("Query timeout after 30s")
    auth_logger.info("User login successful: user123")

    print("\n✓ Check logs/advanced/ for separate module log files")
    print("✓ Console shows all messages from all modules")


def example_merged_logging():
    """Example 2: Multiple modules, merged into single file."""
    print("\n" + "=" * 70)
    print("Example 2: Shared Console + Merged File")
    print("=" * 70)

    # Create manager with shared console and shared file
    manager = LoggerManager(shared_console=True, shared_file="logs/advanced/all_merged.log", use_color=True)

    # Register multiple loggers, all writing to same file
    loggers = {}
    for module in ["Frontend", "Backend", "Cache", "Queue"]:
        loggers[module] = manager.register_logger(name=module, file_strategy="merged")

    # Simulate multi-module activity
    loggers["Frontend"].info("Page rendered: /dashboard")
    loggers["Backend"].info("Processing request: GET /api/users")
    loggers["Cache"].info("Cache hit for key: user:123")
    loggers["Backend"].info("Query executed in 45ms")
    loggers["Queue"].info("Job enqueued: send_email")
    loggers["Frontend"].info("WebSocket connection established")

    print("\n✓ Check logs/advanced/all_merged.log for all module messages")
    print("✓ Console shows unified output with proper time ordering")


def example_flexible_strategy():
    """Example 3: Mix of separate, merged, and console-only."""
    print("\n" + "=" * 70)
    print("Example 3: Flexible Logging Strategies")
    print("=" * 70)

    manager = LoggerManager(shared_console=True, shared_file="logs/advanced/important.log", use_color=True)

    # Critical module: separate file
    critical_logger = manager.register_logger(
        "Critical", file_strategy="separate", log_file="logs/advanced/critical.log"
    )

    # Important modules: merged file
    important1 = manager.register_logger("Important1", file_strategy="merged")
    important2 = manager.register_logger("Important2", file_strategy="merged")

    # Debug module: console only (no file)
    debug_logger = manager.register_logger("Debug", file_strategy="none")

    critical_logger.error("Critical error in payment processing")
    important1.warning("High memory usage detected")
    important2.info("Background job completed")
    debug_logger.debug("Debug: variable x = 42")

    print("\n✓ Critical logs: logs/advanced/critical.log (separate)")
    print("✓ Important logs: logs/advanced/important.log (merged)")
    print("✓ Debug logs: console only (no file)")


def example_smart_naming():
    """Example 4: Smart log file naming strategies."""
    print("\n" + "=" * 70)
    print("Example 4: Smart Log File Naming")
    print("=" * 70)

    # Timestamped naming
    log1 = LogNamingStrategy.timestamped("myapp", suffix="training")
    print(f"Timestamped: {log1}")

    # Daily directory structure
    log2 = LogNamingStrategy.daily("myapp", suffix="production")
    print(f"Daily: {log2}")

    # Hourly directory structure
    log3 = LogNamingStrategy.hourly("myapp")
    print(f"Hourly: {log3}")

    # Incremental naming (avoids conflicts)
    log4 = LogNamingStrategy.incremental("myapp", suffix="test")
    print(f"Incremental: {log4}")

    # Session-based naming
    log5 = LogNamingStrategy.session_based("myapp", session_id="run_001")
    print(f"Session: {log5}")

    # Use with LoggerManager
    manager = LoggerManager(shared_console=True)

    logger = manager.register_logger(
        "SmartNaming", file_strategy="separate", log_file=LogNamingStrategy.timestamped("experiment", suffix="v1")
    )

    logger.info("Experiment started")
    logger.info("Using smart naming for easy identification")

    print("\n✓ Log files are automatically named with timestamps")
    print("✓ Never worry about overwriting old logs")


def example_convenience_function():
    """Example 5: Quick logger group creation."""
    print("\n" + "=" * 70)
    print("Example 5: Quick Logger Group Creation")
    print("=" * 70)

    # Create multiple coordinated loggers at once
    loggers = create_logger_group(
        module_names=["API", "Database", "Cache", "Auth"],
        shared_console=True,
        shared_file="logs/advanced/app_unified.log",
        file_strategy="merged",
        use_color=True,
    )

    # Use the loggers
    loggers["API"].info("Handling request: POST /api/login")
    loggers["Database"].info("User found in database")
    loggers["Auth"].info("Token generated successfully")
    loggers["Cache"].info("Session cached with TTL 3600s")
    loggers["API"].info("Response sent: 200 OK")

    print("\n✓ Created 4 coordinated loggers in one line")
    print("✓ All share console and merged log file")


def example_real_world_webapp():
    """Example 6: Real-world web application logging."""
    print("\n" + "=" * 70)
    print("Example 6: Real-World Web Application")
    print("=" * 70)

    # Setup for a typical web application
    timestamp = LogNamingStrategy.timestamped("webapp", suffix="")

    manager = LoggerManager(
        shared_console=True, shared_file=LogNamingStrategy.daily("app", suffix="all"), use_color=True
    )

    # Different components with different strategies
    access_log = manager.register_logger("Access", file_strategy="separate", log_file=LogNamingStrategy.daily("access"))

    error_log = manager.register_logger("Error", file_strategy="separate", log_file=LogNamingStrategy.daily("error"))

    app_log = manager.register_logger("App", file_strategy="merged")
    db_log = manager.register_logger("DB", file_strategy="merged")

    # Simulate web application activity
    access_log.info("192.168.1.100 - GET /api/users - 200")
    app_log.info("Processing user list request")
    db_log.info("SELECT * FROM users LIMIT 50")
    access_log.info("192.168.1.101 - POST /api/login - 200")

    # Error scenario
    access_log.info("192.168.1.102 - GET /api/broken - 500")
    error_log.error("Exception in /api/broken: NullPointerException")
    app_log.error("Failed to process request", exc_info=False)

    print("\n✓ Access logs: separate file (daily)")
    print("✓ Error logs: separate file (daily)")
    print("✓ App & DB logs: merged file (daily)")
    print("✓ Console: unified view of all activity")


def example_training_with_manager():
    """Example 7: ML training with coordinated logging."""
    print("\n" + "=" * 70)
    print("Example 7: ML Training with Logger Manager")
    print("=" * 70)

    # Create timestamped training session
    session_name = LogNamingStrategy.timestamped("training", suffix="resnet")

    manager = LoggerManager(shared_console=True, shared_file=session_name.replace(".log", "_all.log"))

    # Different components of training
    train_logger = manager.register_logger(
        "Training", file_strategy="separate", log_file=session_name.replace(".log", "_train.log")
    )

    metrics_logger = manager.register_logger(
        "Metrics", file_strategy="separate", log_file=session_name.replace(".log", "_metrics.log")
    )

    system_logger = manager.register_logger("System", file_strategy="merged")

    # Training simulation
    train_logger.info("Starting training: ResNet-50 on ImageNet")
    system_logger.info("GPU Memory: 10.2 GB / 24 GB")

    for epoch in range(1, 4):
        train_logger.info(f"Epoch {epoch}/10 started")
        metrics_logger.info(f"Epoch {epoch}: loss=0.{50 - epoch * 10:.2f}, acc=0.{70 + epoch * 5:.2f}")
        system_logger.info(f"GPU utilization: {85 + epoch}%")
        time.sleep(0.1)

    train_logger.info("Training completed successfully")

    print("\n✓ Training logs: organized by component")
    print("✓ All logs timestamped to identify the training run")
    print("✓ Unified console output for monitoring")


def run_all_examples():
    """Run all advanced examples."""
    examples = [
        example_shared_console_separate_files,
        example_merged_logging,
        example_flexible_strategy,
        example_smart_naming,
        example_convenience_function,
        example_real_world_webapp,
        example_training_with_manager,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\nError in {example.__name__}: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("All advanced examples completed!")
    print("Check the 'logs/advanced/' directory for log files.")
    print("=" * 70)


if __name__ == "__main__":
    run_all_examples()
