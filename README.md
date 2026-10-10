# advlog

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.2-brightgreen)](CHANGELOG.md)

A Python logging library with colored terminal output, file management, progress tracking, and ML training utilities, built on top of [Rich](https://github.com/Textualize/rich).

> **Personal project notice:** This package was written for personal development use. Update frequency and feature scope may be limited. Contributions and suggestions are welcome.

## Features

- **Rich Console Output** — Colored terminal logging via the Rich library
- **Flexible Configuration** — `LoggerConfig` dataclass for per-logger overrides; simple `initialize()` / `get_logger()` API for common cases
- **File Logging** — Separate or merged file strategies with configurable rotation
- **Progress Tracking** — Integrated progress bars via `ProgressTracker`
- **Multi-Module Coordination** — `LoggerManager` for consistent logging across modules
- **ML/Training Utilities** — `TrainingLogger` plugin for experiment logging
- **Smart File Naming** — Timestamped, daily, and incremental log file naming

## Installation

```bash
pip install advlog-core
```

With all optional features:

```bash
pip install "advlog-core[all]"
```

> The PyPI package name is `advlog-core`; import as `import advlog`.

## Quick Start

### One-liner

```python
from advlog import get_logger

log = get_logger(__name__)
log.info("Application started")
log.warning("High memory usage detected")
log.error("Database connection failed")
```

### Initialize once, use everywhere

```python
from advlog import initialize, get_logger, get_progress

initialize(
    output_dir="./logs",
    session_name="myapp",
    log_level="DEBUG",
    show_location=True,
)

log = get_logger(__name__)
log.info("Initialized")

progress = get_progress()
with progress:
    task = progress.add_task("Processing", total=100)
    for i in range(100):
        progress.update(task, advance=1)
```

### Per-logger configuration with `LoggerConfig`

```python
from advlog import LoggerManager, LoggerConfig

manager = LoggerManager(shared_console=True, shared_file="logs/app.log")

# Default registration
api_logger = manager.register_logger("api")

# Override with LoggerConfig
db_logger = manager.register_logger(config=LoggerConfig(
    name="database",
    log_level="DEBUG",
    log_file="logs/db.log",
    show_location=True,
))

api_logger.info("API server started")
db_logger.debug("Executing query: SELECT ...")
```

### Register a group of loggers at once

```python
from advlog import create_logger_group

loggers = create_logger_group(
    ["api", "database", "auth"],
    shared_console=True,
    file_strategy="merged",
)

loggers["api"].info("Request received")
loggers["database"].debug("Query executed")
loggers["auth"].warning("Invalid login attempt")
```

## Formatters

Four formatters are available:

| Class | Description |
|---|---|
| `RichColorFormatter` | Wraps messages in Rich color markup by log level |
| `PlainFormatter` | Plain text, no color codes |
| `IndentedFormatter` | Indents continuation lines of multi-line messages |
| `JSONFormatter` | Outputs each record as a JSON object, with `extra=` fields under `"extra"` |

```python
from advlog import JSONFormatter
import logging

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.getLogger("myapp").addHandler(handler)
```

## File Logging

```python
from advlog import create_file_handler

handler = create_file_handler(
    log_file="logs/app.log",
    mode="a",
    show_location=True,
)
```

### Structured (JSON Lines) output

Set `file_format` to get a machine-readable log next to (or instead of) the text log:

| `file_format` | Files written |
|---|---|
| `"text"` (default) | `app.log` |
| `"json"` | `app.jsonl` |
| `"both"` | `app.log` and `app.jsonl` |

```python
from advlog import initialize, get_logger

initialize(output_dir="./logs", session_name="train", file_format="both")

log = get_logger(__name__)
log.info("Run started", extra={"lr": 1e-3, "batch_size": 32})
```

The `.jsonl` file holds one JSON object per line. Anything passed via `extra=` is stored under the `"extra"` key:

```json
{"timestamp": "2026-03-06T14:30:22.123456+08:00", "level": "INFO", "logger": "__main__", "message": "Run started", "module": "train", "function": "<module>", "line": 6, "extra": {"lr": 0.001, "batch_size": 32}}
```

Values JSON cannot represent (paths, sets, NumPy arrays, tensors, arbitrary objects) are converted rather than dropped, and `NaN`/`Infinity` are written as `null` so every line stays valid JSON. `file_format` is also accepted by `LoggerManager`, `LoggerConfig`, and `create_logger_group`; `create_file_handlers()` builds the handlers directly.

```python
import pandas as pd

df = pd.read_json("logs/train.jsonl", lines=True)
errors = df[df["level"] == "ERROR"]
```

### Smart log file naming

```python
from advlog import LogNamingStrategy

# Timestamp-based:  logs/2026-03-06/20260306_143022_app_prod.log
log_file = LogNamingStrategy.timestamped("app", suffix="prod")

# Daily directory:  logs/2026-03-06/myapp_errors.log
log_file = LogNamingStrategy.daily("myapp", suffix="errors")

# Incremental (no conflicts):  logs/backup_data.log  →  backup_data_1.log ...
log_file = LogNamingStrategy.incremental("backup", suffix="data")
```

## Progress Tracking

```python
from advlog import ProgressTracker

with ProgressTracker() as progress:
    download = progress.add_task("Downloading", total=100)
    process  = progress.add_task("Processing",  total=50)

    for _ in range(100):
        progress.update(download, advance=1)

    for _ in range(50):
        progress.update(process, advance=1)
```

## ML Training Utilities

```python
from advlog import TrainingLogger
import logging

logger = logging.getLogger(__name__)
trainer = TrainingLogger(logger)

trainer.log_train_step(
    epoch=1,
    total_epochs=10,
    batch=100,
    total_batches=1000,
    loss_dict={"loss": 0.4231, "accuracy": 0.872},
    time_elapsed=45.2,
    additional_metrics={"lr": 1e-3},
)
```

`log_configuration`, `log_train_step`, and `log_evaluation_results` attach their data as `extra` fields, so with `file_format="json"` or `"both"` each one becomes a queryable record (`extra.event` is `"config"`, `"train_step"`, or `"evaluation"`).

## Exception Logging

```python
from advlog import setup_exception_logging

# Install a sys.excepthook that logs all uncaught exceptions
setup_exception_logging()
```

## Real-World Example

See [`examples/real_world_demo/`](examples/real_world_demo/) for a complete multi-module application demonstrating global initialization, cross-module loggers, progress tracking, error handling, and organized file output.

```bash
python -m examples.real_world_demo.main
python -m examples.real_world_demo.structured_demo   # JSON Lines output and querying it
```

## Dependencies

**Required**

- [Rich](https://github.com/Textualize/rich) — Terminal formatting and colored output

**Optional**

| Extra tag | Package | Feature |
|---|---|---|
| `config` | `omegaconf` | Advanced config file parsing |
| `torch` | `torchinfo` | Model structure visualization |
| `distributed` | `accelerate` | Distributed/multi-GPU training support |

```bash
pip install "advlog-core[config]"
pip install "advlog-core[torch]"
pip install "advlog-core[distributed]"
```

## Contributing

Contributions are welcome — please feel free to open an issue or submit a pull request.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

## Acknowledgments

- [Rich](https://github.com/Textualize/rich) for the terminal formatting library
- [Python logging](https://docs.python.org/3/library/logging.html) for the logging infrastructure