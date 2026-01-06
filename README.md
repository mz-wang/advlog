# advlog-core

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-brightgreen)](CHANGELOG.md)

A powerful, feature-rich logging library for Python with beautiful terminal output, flexible configuration, and extensive plugin support.

## ✨ Features

- **🎨 Rich Console Output** - Beautiful colored terminal logging with Rich library
- **📊 Progress Tracking** - Integrated progress bars with automatic management
- **🔧 Flexible Configuration** - Easy-to-use configuration system based on dataclasses
- **📁 Smart File Management** - Log rotation, intelligent naming, and multiple file strategies
- **🎯 Multi-Module Coordination** - LoggerManager for unified logging across modules
- **🔍 Source Information** - Automatic display of log origin (file, line, function)
- **📐 Aligned Formatting** - Precise control over field width and alignment
- **🌍 Environment Adaptive** - Automatic detection and adaptation to different environments
- **🚀 ML/AI Ready** - Built-in support for machine learning training logs

## 📦 Installation

Install from PyPI:

```bash
pip install advlog-core
```

Install with all optional features:

```bash
pip install "advlog-core[all]"
```

> **Note:** The PyPI package name is `advlog-core`, but when importing in Python, use `import advlog`.

## 🚀 Quick Start

### Basic Usage

```python
from advlog import get_logger

# Create a logger for the current module
log = get_logger(__name__)

# Use the logger
log.info("Application started")
log.warning("High memory usage detected")
log.error("Database connection failed")
```

### Initialize Logging System

```python
from advlog import initialize, get_logger, get_progress

# Initialize the logging system
initialize(
    output_dir="./logs",
    session_name="myapp",
    log_level="DEBUG",
    show_location=True
)

# Get logger and progress tracker
log = get_logger(__name__)
progress = get_progress()

# Use in a workflow
with progress:
    task = progress.add_task("Processing", total=100)
    for i in range(100):
        # Do work
        progress.update(task, advance=1)
```

## 🏗️ Real-World Example

For a complete multi-module application example, see [`examples/real_world_demo/`](examples/real_world_demo/). This demonstrates:

1. **Global logging initialization** - Set up logging once at application start
2. **Cross-module logging** - Share loggers across multiple Python files
3. **Progress tracking** - Track long-running workflows
4. **Error handling** - Comprehensive error logging
5. **File management** - Organized log file structure

Run it:

```bash
python -m examples.real_world_demo.main
```

## 📋 Advanced Usage

### Multiple Loggers with Manager

```python
from advlog import LoggerManager, get_logger

# Create a logger manager for coordinated logging
manager = LoggerManager(shared_console=True)

# Register loggers for different modules
api_logger = manager.register_logger("api")
db_logger = manager.register_logger("database", log_level="DEBUG")
auth_logger = manager.register_logger("auth")

# Use them
api_logger.info("API server started")
db_logger.debug("Executing query")
auth_logger.warning("Invalid login attempt")
```

### Smart File Naming

```python
from advlog import LogNamingStrategy

# Timestamp-based naming
log_file = LogNamingStrategy.timestamped("app", suffix="production")
# Result: logs/2026-01-05/20260105_143022_app_production.log

# Daily directory structure
log_file = LogNamingStrategy.daily("myapp", suffix="errors")
# Result: logs/2026-01-05/myapp_errors.log

# Incremental naming (avoids conflicts)
log_file = LogNamingStrategy.incremental("backup", suffix="data")
# Result: logs/backup_data.log (or backup_data_1.log if exists)
```

### Progress Tracking

```python
from advlog import ProgressTracker

with ProgressTracker() as progress:
    # Add multiple tasks
    download_task = progress.add_task("Downloading files", total=100)
    process_task = progress.add_task("Processing data", total=50)

    # Update progress
    for i in range(100):
        # Download file
        progress.update(download_task, advance=1)

    for i in range(50):
        # Process data
        progress.update(process_task, advance=1)
```

### ML Training Logger

```python
from advlog import AdvancedLogger, TrainingLogger

# Create logger
logger = AdvancedLogger().get_logger()

# Create training logger
trainer = TrainingLogger(logger)

# Log training step
trainer.log_train_step(
    epoch=1,
    total_epochs=10,
    batch=100,
    total_batches=1000,
    loss_dict={"loss": 0.5, "accuracy": 0.85},
    learning_rate=0.001,
    time_elapsed=45.2
)
```

## 🛠️ Dependencies

This project is built to be lightweight. While the core functionality requires minimal setup, certain features are enabled only when optional dependencies are installed.

### Required
These are necessary for the basic operation of advlog-core:

- **Rich** (MIT License): Used for beautiful terminal formatting and logging.

### Optional
Install these based on your specific use case:

- **OmegaConf** (BSD-3-Clause): Required for advanced configuration file parsing.
- **torchinfo** (MIT License): Required for model structure visualization.
- **Accelerate** (Apache-2.0): Required for distributed training and multi-GPU logging support.

### Installation

You can install the core package with:

```bash
pip install advlog-core
```

To include all optional features, you can use the extra tag:

```bash
pip install "advlog-core[all]"
```

Or install specific optional dependencies:

```bash
pip install "advlog-core[config]"      # For OmegaConf support
pip install "advlog-core[torch]"       # For torchinfo support
pip install "advlog-core[distributed]" # For Accelerate support
```

## 📖 Documentation

- **Examples**: See the [`examples/`](examples/) directory for various use cases
- **Changelog**: See [CHANGELOG.md](CHANGELOG.md) for version history
- **API Reference**: Browse the source code in [`src/advlog/`](src/advlog/)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Rich](https://github.com/Textualize/rich) - For the amazing terminal formatting library
- [Python Logging](https://docs.python.org/3/library/logging.html) - For the logging infrastructure
