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

"""Logger-level filters: bound context fields and main-process gating."""

import logging
import sys
from typing import Any

from advlog.core.formatter import RESERVED_RECORD_ATTRS

__all__ = [
    "ContextFilter",
    "MainProcessFilter",
    "is_main_process",
]


class ContextFilter(logging.Filter):
    """Attach bound context fields to every record of the loggers it is added to.

    The fields behave like ``extra=`` passed on every call: invisible in the
    default text format, available to format strings as ``%(name)s``, and
    stored under ``"extra"`` in JSON output. A field passed explicitly via
    ``extra=`` on a call wins over the bound value.

    Example:
        context = ContextFilter()
        context.bind(run_id="2026-03-06-a", git_sha="ab6e876")
        logger.addFilter(context)
    """

    def __init__(self):
        super().__init__()
        self.fields: dict[str, Any] = {}

    def bind(self, **fields: Any) -> None:
        """Add or replace context fields.

        Args:
            **fields: Field names and values to attach to every record
        """
        for key in fields:
            if key in RESERVED_RECORD_ATTRS:
                raise ValueError(f"Context field {key!r} would overwrite a built-in log record attribute")

        # Replace rather than mutate so a record being filtered sees a consistent dict
        self.fields = {**self.fields, **fields}

    def unbind(self, *keys: str) -> None:
        """Remove context fields. Unknown keys are ignored.

        Args:
            *keys: Field names to remove
        """
        self.fields = {key: value for key, value in self.fields.items() if key not in keys}

    def clear(self) -> None:
        """Remove all context fields."""
        self.fields = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Add the bound fields to the record. Never rejects a record."""
        for key, value in self.fields.items():
            if key not in record.__dict__:
                record.__dict__[key] = value
        return True


def is_main_process() -> bool:
    """Check whether this is the main process of an ``accelerate`` run.

    Returns:
        False only on a non-main process of an initialized accelerate run.
        True when accelerate is not in use or has not been initialized yet.
    """
    # Only look, never import: importing/initializing accelerate is the application's call
    state_module = sys.modules.get("accelerate.state")
    if state_module is None:
        return True

    partial_state = state_module.PartialState
    if not partial_state._shared_state:
        return True

    return bool(partial_state().is_main_process)


class MainProcessFilter(logging.Filter):
    """Drop records on non-main processes of an ``accelerate`` run.

    Takes effect once accelerate's state exists (after ``Accelerator()`` or
    ``PartialState()`` has been created); before that every process logs.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return is_main_process()
