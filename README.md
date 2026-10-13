# advlog

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache--2.0-green)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.3.0-brightgreen)](CHANGELOG.md)

A Python logging library with colored terminal output, file management, progress tracking, and ML training utilities, built on top of [Rich](https://github.com/Textualize/rich).

> **Personal project notice:** This package was written for personal development use. Update frequency and feature scope may be limited. Contributions and suggestions are welcome.

## Features

- **Rich Console Output** — Colored terminal logging via the Rich library
- **Flexible Configuration** — `LoggerConfig` dataclass for per-logger overrides; simple `initialize()` / `get_logger()` API for common cases
- **File Logging** — Separate or merged file strategies with size-based rotation
- **Structured Output** — Optional JSON Lines file with your own fields (`extra=`, bound context) for parsing and querying
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

Things worth knowing:

- Loggers obtained before `initialize()` are console-only; they pick up the log file as soon as `initialize()` runs.
- Calling `initialize()` again applies the new settings in full to every existing logger. In particular, `enable_file_logging=False` detaches and closes the current log file.
- `use_color=False` turns color off for everything drawn on the shared console, progress bars included.
- `get_logger(name, log_level="ERROR")` sets the level even if that logger already exists.

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

`LoggerConfig` fields and where they apply:

| Field | Applies to |
|---|---|
| `name`, `log_level`, `propagate`, `console_output`, `show_location` | The logger itself |
| `log_file`, `file_mode`, `file_format`, `max_file_size`, `backup_count`, `log_format`, `date_format`, `encoding` | The logger's own file (`log_file`). `file_format`, `max_file_size` and `backup_count` fall back to the manager's values when left as `None` |
| `use_color`, `enable_rich_tracebacks` | The logger's own console handler, i.e. only with `LoggerManager(shared_console=False)` |
| `use_accelerate` | Drops this logger's records on non-main processes of a Hugging Face `accelerate` run, once `Accelerator()` has been created |

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

Files hold plain text: paired Rich tags such as `[bold red]alert[/bold red]` color the console but are removed from file output. Brackets that are not a closed style pair (`arr[i]`, `[1/3]`, `[epoch 1]`) are left as written. Pass `strip_markup=False` to `create_file_handler()` to keep the tags.

### Rotation

For long runs, cap the file size. When the file reaches `max_file_size` bytes it is renamed to `app.log.1` (older ones shift to `.2`, `.3`, ...) and a fresh file is started; `backup_count` old files are kept.

```python
from advlog import initialize

initialize(
    output_dir="./logs",
    session_name="train",
    max_file_size=50 * 1024 * 1024,  # 50 MB
    backup_count=3,
)
```

`max_file_size` / `backup_count` are also accepted by `LoggerManager`, `LoggerConfig`, `create_file_handler()` and `create_file_handlers()`, and apply to the `.jsonl` file too. A rotating file is always appended to, so `file_mode="w"` has no effect on it.

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

Lines meant only for human eyes (separators, banners) can be kept out of the `.jsonl` file:

```python
log.info("=" * 60, extra={"text_only": True})  # console and text log only
```

### Context fields on every record

Bind fields once and they are attached to every record from every logger, as if passed via `extra=` each time. This is what lets you tell runs apart after merging their logs.

```python
from advlog import initialize, bind_context, unbind_context, clear_context

initialize(session_name="train", file_format="both", context={"run_id": "exp-42", "git_sha": "ab6e876"})

bind_context(epoch=3)     # add or update fields later
unbind_context("epoch")   # remove some
clear_context()           # remove all
```

```json
{"timestamp": "...", "level": "INFO", "logger": "train", "message": "step done", "module": "train", "function": "fit", "line": 88, "extra": {"run_id": "exp-42", "git_sha": "ab6e876", "epoch": 3}}
```

An explicit `extra=` on a call wins over a bound field of the same name. Bound fields are also available to custom text formats, e.g. `LoggerConfig(log_format="%(asctime)s %(run_id)s %(message)s")`. Names of built-in record attributes (`message`, `name`, `levelname`, ...) are rejected.

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
from advlog import TrainingLogger, get_logger

logger = get_logger(__name__)
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

`log_configuration`, `log_train_step`, and `log_evaluation_results` attach their data as `extra` fields, so with `file_format="json"` or `"both"` each one becomes a queryable record (`extra.event` is `"config"`, `"train_step"`, or `"evaluation"`). Their separator and per-key lines are marked `text_only`, so the `.jsonl` file gets one record per call rather than one per printed line.

Records logged through `TrainingLogger` report the file and line of *your* call (visible with `show_location=True` and in the JSON `module` / `function` / `line` fields), not a location inside the helper.

## Exception Logging

```python
from advlog import setup_exception_logging

# Install a sys.excepthook that logs all uncaught exceptions
setup_exception_logging()
```

The traceback goes wherever your other logs go: the console and the log file(s) configured by `initialize()`, including the `.jsonl` file (as an `ERROR` record with an `exception` field). Pass your own logger to route it elsewhere. `KeyboardInterrupt` is left to Python's default handling.

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
| `distributed` | `accelerate` | Main-process-only logging in multi-GPU runs (`LoggerConfig(use_accelerate=True)`) |

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