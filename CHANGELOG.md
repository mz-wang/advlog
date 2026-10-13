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
