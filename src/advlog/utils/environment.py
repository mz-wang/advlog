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
import platform
import subprocess
import sys
from collections.abc import Iterable
from importlib import metadata
from typing import Any

from .path import StrPath


def detect_environment() -> dict[str, Any]:
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
        from IPython import get_ipython  # type: ignore

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


def process_tag() -> str | None:
    """Identify this process among others started together with the same script.

    Slurm array tasks and the ranks of a distributed run (torchrun,
    ``accelerate launch``, DeepSpeed) are often started within the same
    second, so timestamped log file names alone collide.

    Returns:
        "task<N>" for a Slurm array task, "rank<N>" for a rank of a run with
        more than one process, both joined by "_", or None when neither applies
    """
    parts = []

    task = os.environ.get("SLURM_ARRAY_TASK_ID")
    if task:
        parts.append(f"task{task}")

    rank = os.environ.get("RANK")
    if rank and os.environ.get("WORLD_SIZE", "") != "1":
        parts.append(f"rank{rank}")

    return "_".join(parts) or None


_SLURM_FIELDS = {
    "job_id": "SLURM_JOB_ID",
    "job_name": "SLURM_JOB_NAME",
    "array_job_id": "SLURM_ARRAY_JOB_ID",
    "array_task_id": "SLURM_ARRAY_TASK_ID",
    "nodelist": "SLURM_JOB_NODELIST",
}


def _main_script_dir() -> str:
    """Directory of the running script, or the working directory if there is none."""
    path = getattr(sys.modules.get("__main__"), "__file__", None)
    return os.path.dirname(os.path.abspath(path)) if path else os.getcwd()


def _git_state(directory: StrPath) -> dict[str, Any] | None:
    """Read commit, branch and uncommitted changes of the repository containing a directory.

    Args:
        directory: Any directory inside the repository

    Returns:
        {"commit", "branch", "dirty"}, or None if git is missing or this is no repository
    """
    try:
        # One call gives commit, branch and changes. Untracked files are left
        # out: results and logs written into the repository would mark every run dirty.
        output = subprocess.run(
            ["git", "status", "--porcelain=v2", "--branch", "--untracked-files=no"],
            cwd=directory,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=True,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None

    state: dict[str, Any] = {"commit": None, "branch": None, "dirty": False}
    for line in output.splitlines():
        if line.startswith("# branch.oid "):
            oid = line.removeprefix("# branch.oid ")
            state["commit"] = None if oid == "(initial)" else oid
        elif line.startswith("# branch.head "):
            head = line.removeprefix("# branch.head ")
            state["branch"] = None if head == "(detached)" else head
        elif line and not line.startswith("#"):
            state["dirty"] = True
    return state


def collect_run_info(repo_dir: StrPath | None = None, packages: Iterable[str] = ()) -> dict[str, Any]:
    """Collect what is needed to tell a run apart and reproduce it.

    Args:
        repo_dir: Directory inside the git repository to describe. Defaults to
                  the directory of the running script (the working directory
                  when there is no script, e.g. in Jupyter).
        packages: Distribution names whose installed versions to record, e.g.
                  ``["numpy", "torch"]``. A package that is not installed is
                  recorded as None.

    Returns:
        Dict with ``argv``, ``cwd``, ``python``, ``executable``, ``platform``,
        ``hostname``, ``pid`` and ``git`` (``{"commit", "branch", "dirty"}``,
        None outside a repository or without git; ``dirty`` ignores untracked
        files). ``packages``, ``slurm`` (job and array ids) and ``rank`` /
        ``world_size`` are added when there is something to record.

    Example:
        >>> info = collect_run_info(packages=["numpy"])
        >>> info["git"]
        {'commit': '1a2b3c...', 'branch': 'main', 'dirty': True}
    """
    info: dict[str, Any] = {
        "argv": list(sys.argv),
        "cwd": os.getcwd(),
        "python": platform.python_version(),
        "executable": sys.executable,
        "platform": platform.platform(),
        "hostname": platform.node(),
        "pid": os.getpid(),
        "git": _git_state(repo_dir if repo_dir is not None else _main_script_dir()),
    }

    versions: dict[str, str | None] = {}
    for name in packages:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    if versions:
        info["packages"] = versions

    slurm = {key: os.environ[var] for key, var in _SLURM_FIELDS.items() if os.environ.get(var)}
    if slurm:
        info["slurm"] = slurm

    for key, var in (("rank", "RANK"), ("world_size", "WORLD_SIZE")):
        value = os.environ.get(var)
        if value is not None and value.isdigit():
            info[key] = int(value)

    return info
