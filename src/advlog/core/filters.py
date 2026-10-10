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

"""Logger-level filters."""

import logging
import sys

__all__ = [
    "MainProcessFilter",
    "is_main_process",
]


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
