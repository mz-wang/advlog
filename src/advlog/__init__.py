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

"""Advanced Logging System with Rich Features.

This package provides a modular, feature-rich logging system with:
- Colored console output (via Rich)
- File logging with optional rotation
- Progress bar integration
- Training utilities for ML/DL
- Environment auto-detection
- Flexible configuration

Quick Start:
    Simple usage with global management:
        >>> from advlog import get_logger
        >>> log = get_logger(__name__)
        >>> log.info("Hello, world!")

    With explicit initialization:
        >>> from advlog import initialize, get_logger, get_progress
        >>> initialize(output_dir="./logs", session_name="myapp", log_level="DEBUG")
        >>> log = get_logger(__name__)
        >>> progress = get_progress()

    With progress bar:
        >>> from advlog import ProgressTracker
        >>> with ProgressTracker() as progress:
        ...     task = progress.add_task("Processing", total=100)
        ...     for i in range(100):
        ...         # Do work
        ...         progress.update(task, advance=1)

    Training logger:
        >>> from advlog import AdvancedLogger, TrainingLogger
        >>> logger = AdvancedLogger().get_logger()
        >>> trainer = TrainingLogger(logger)
        >>> trainer.log_train_step(
        ...     epoch=1, total_epochs=10,
        ...     batch=1, total_batches=100,
        ...     loss_dict={"loss": 0.5},
        ...     time_elapsed=1.2
        ... )

Modules:
    core: Core logging functionality
    handlers: File and console handlers
    plugins: Progress tracking and training utilities
    utils: Environment detection and helper utilities
    setup: Global logging management (initialize, get_logger, get_progress)
"""

__version__ = "0.1.0"
__author__ = "Mengzhao Wang"

# Core imports
from .core import (
    AdvancedLogger,
    AlignedFormatter,
    ColumnFormatter,
    CompactFormatter,
    IndentedFormatter,
    JSONFormatter,
    LoggerConfig,
    LoggerManager,
    PlainFormatter,
    RichColorFormatter,
    TableFormatter,
    create_aligned_formatter,
    create_logger_group,
)
from .core.logger import setup_exception_logging

# Handler imports
from .handlers import (
    create_console_handler,
    create_file_handler,
)

# Plugin imports (with graceful degradation)
try:
    from .plugins import (
        ProgressTracker,
        TrainingLogger,
        create_progress_bar,
    )

    PLUGINS_AVAILABLE = True
except ImportError:
    PLUGINS_AVAILABLE = False

# Utility imports
# Global management API (replaces old get_logger)
from .setup import (
    get_logger,
    get_progress,
    initialize,
    reset,
)
from .utils import (
    LogNamingStrategy,
    detect_environment,
    get_timestamped_name,
    supports_color,
)

# Define public API
__all__ = [
    # Version
    "__version__",
    # Core
    "AdvancedLogger",
    "LoggerConfig",
    "LoggerManager",
    "create_logger_group",
    "IndentedFormatter",
    "RichColorFormatter",
    "AlignedFormatter",
    "TableFormatter",
    "CompactFormatter",
    "ColumnFormatter",
    "PlainFormatter",
    "JSONFormatter",
    "create_aligned_formatter",
    "setup_exception_logging",
    # Handlers
    "create_console_handler",
    "create_file_handler",
    # Plugins
    "ProgressTracker",
    "create_progress_bar",
    "TrainingLogger",
    # Utils
    "detect_environment",
    "supports_color",
    "LogNamingStrategy",
    "get_timestamped_name",
    # Global management API
    "initialize",
    "get_logger",
    "get_progress",
    "reset",
]
