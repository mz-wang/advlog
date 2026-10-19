## v0.5.0 (2026-10-19)

### Feat

- **run**: add run info, metrics and artifact records
- **api**: log exceptions in threads and, opt-in, SIGTERM

## v0.4.0 (2026-10-19)

### BREAKING CHANGE

- arrays and tensors with more than 1000 elements are no
longer written in full to JSON output; their shape, dtype and size are
written instead. Pass JSONFormatter(max_array_size=None) to keep the
full values.

### Feat

- **api**: give each process its own auto-named log file
- **core**: gate output to rank 0 via initialize(main_process_only=True)
- **core**: capture standard library loggers by package name
- **json**: summarize large arrays instead of writing them in full

### Fix

- **naming**: create the target directory in LogNamingStrategy.incremental

## v0.3.1 (2026-10-19)

### Fix

- **typing**: ship py.typed and accept path objects for file paths
- **deps**: make omegaconf an optional dependency

## v0.3.0 (2026-10-14)

### BREAKING CHANGE

- JSONFormatter now nests fields passed via extra= under an "extra" key instead of merging them into the top level, so they can no longer overwrite standard fields. Read record["extra"]["key"] instead of record["key"].

### Feat

- **core**: add log rotation, bound context fields and text-only records
- **core**: add structured JSON Lines file output

### Fix

- **core**: honor settings and records that were silently dropped

## v0.2.1 (2026-07-21)

### Fix

- **api**: make implicit auto-init console-only to avoid stray log file

## v0.2.0 (2026-03-06)

### BREAKING CHANGE

- AdvancedLogger class has been removed. Use LoggerManager and global initialize()/get_logger() functions instead. Removed AlignedFormatter, TableFormatter, CompactFormatter, and ColumnFormatter. Simplified to RichColorFormatter, PlainFormatter, IndentedFormatter, and JSONFormatter only.

### Refactor

- **core**: remove AdvancedLogger class and simplify API

## v0.1.2 (2026-02-27)

### Fix

- **core**: support LoggerManager re-initialization and dynamic handler refresh

## v0.1.1 (2026-02-27)

### Refactor

- remove redundant files, reorganize files, and fix problems found by ruff and ty.

## v0.1.0 (2026-01-06)

### Feat

- initial implementation of advlog - advanced logging library with alignment, progress tracking, and rich formatting
