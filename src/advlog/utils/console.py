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

"""Shared Console utility for advlog."""
from rich.console import Console
import sys

_shared_console = None

def get_shared_console() -> Console:
    """Get or create a shared Console instance.

    Returns:
        Console: A shared Console instance writing to stderr.
    """
    global _shared_console
    if _shared_console is None:
        _shared_console = Console(file=sys.stderr)
    return _shared_console
