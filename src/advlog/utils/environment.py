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

"""Environment detection utilities."""

import os
import sys
from typing import Any, Dict


def detect_environment() -> Dict[str, Any]:
    """Detect the current runtime environment.

    Returns:
        Dict containing environment information:
        - platform: Operating system (windows, linux, darwin)
        - is_jupyter: Whether running in Jupyter/IPython
        - is_ci: Whether running in CI/CD environment
        - supports_color: Whether terminal supports color
        - terminal_width: Terminal width in columns
        - is_interactive: Whether in interactive mode
    """
    env_info = {
        "platform": sys.platform,
        "is_jupyter": _is_jupyter(),
        "is_ci": _is_ci(),
        "supports_color": supports_color(),
        "terminal_width": _get_terminal_width(),
        "is_interactive": sys.stdin.isatty() if hasattr(sys.stdin, "isatty") else False,
    }
    return env_info


def _is_jupyter() -> bool:
    """Check if running in Jupyter/IPython environment."""
    try:
        # Check for IPython
        from IPython import get_ipython

        ipython = get_ipython()
        if ipython is None:
            return False
        # Check if it's a Jupyter kernel
        if "IPKernelApp" in ipython.config:
            return True
    except (ImportError, AttributeError):
        pass
    return False


def _is_ci() -> bool:
    """Check if running in CI/CD environment."""
    ci_env_vars = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "JENKINS_HOME",
        "TRAVIS",
        "CIRCLECI",
    ]
    return any(os.getenv(var) for var in ci_env_vars)


def supports_color() -> bool:
    """Check if the terminal supports color output.

    Returns:
        True if color is supported, False otherwise.
    """
    # Check if NO_COLOR environment variable is set
    if os.getenv("NO_COLOR"):
        return False

    # Check if FORCE_COLOR environment variable is set
    if os.getenv("FORCE_COLOR"):
        return True

    # CI environments typically don't support color well
    if _is_ci():
        return False

    # Windows color support
    if sys.platform == "win32":
        # Windows 10+ supports ANSI color codes
        try:
            import platform

            version = platform.version()
            # Windows 10 is version 10.0
            if version.startswith("10."):
                return True
        except Exception:
            pass
        # Check if running in Windows Terminal or ConEmu
        if os.getenv("WT_SESSION") or os.getenv("ConEmuANSI"):
            return True
        return False

    # Unix-like systems
    if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
        return True

    return False


def _get_terminal_width() -> int:
    """Get terminal width in columns.

    Returns:
        Terminal width, defaults to 80 if unable to determine.
    """
    try:
        import shutil

        size = shutil.get_terminal_size()
        return size.columns
    except Exception:
        return 80
