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

"""Logger and handler filters: bound context fields and main-process gating."""

import logging
import os
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
    """Check whether this is the main process of a distributed run.

    Asks accelerate first, once it has been initialized. Otherwise uses the
    ``RANK`` environment variable set by torchrun, ``accelerate launch`` and
    DeepSpeed, or ``LOCAL_RANK`` when only that one is set (on a multi-node
    run every node then has a "main" process).

    Returns:
        False only on a process known not to be rank 0. True outside
        distributed runs and when the rank cannot be read.
    """
    # Only look, never import: importing/initializing accelerate is the application's call
    state_module = sys.modules.get("accelerate.state")
    if state_module is not None and state_module.PartialState._shared_state:
        return bool(state_module.PartialState().is_main_process)

    for variable in ("RANK", "LOCAL_RANK"):
        value = os.environ.get(variable)
        if value is not None:
            try:
                return int(value) == 0
            except ValueError:
                return True

    return True


class MainProcessFilter(logging.Filter):
    """Drop records on non-main processes of a distributed run.

    See is_main_process() for how the process is identified. With
    accelerate and no rank variable in the environment, every process logs
    until ``Accelerator()`` or ``PartialState()`` has been created.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return is_main_process()
