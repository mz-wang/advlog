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

"""Run records for experiments and simulations: run info, metrics, artifacts.

Each function writes one record whose data is attached as ``extra`` fields,
with ``extra.event`` naming the kind of record ("run_start", "metrics",
"artifact"), so a JSON Lines log can be filtered by event. TrainingLogger
uses the same convention for its training-specific records.
"""

import logging
import os
from collections.abc import Iterable, Mapping
from typing import Any

from advlog.utils.environment import collect_run_info
from advlog.utils.path import StrPath

__all__ = [
    "log_run_info",
    "log_metrics",
    "log_artifact",
]


def _default_logger(logger: logging.Logger | None) -> logging.Logger:
    if logger is not None:
        return logger
    # Imported here: advlog.api imports the plugins package
    from advlog.api import get_logger

    return get_logger("advlog")


def _check_fields(fields: Mapping[str, Any], *reserved: str) -> None:
    for key in reserved:
        if key in fields:
            raise ValueError(f"Field {key!r} is set by the function itself")


def _format_value(value: Any) -> str:
    return f"{value:.6g}" if isinstance(value, float) else str(value)


def _format_size(size: int) -> str:
    amount = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if amount < 1024 or unit == "GB":
            return f"{amount:.0f} {unit}" if unit == "B" else f"{amount:.1f} {unit}"
        amount /= 1024
    return f"{size} B"


def log_run_info(
    logger: logging.Logger | None = None,
    repo_dir: StrPath | None = None,
    packages: Iterable[str] = (),
) -> dict[str, Any]:
    """Log, once at the start of a run, where and from what code it runs.

    Writes one record with ``extra.event`` = "run_start" and the output of
    collect_run_info() under ``extra.run_info``: command line, git commit,
    branch and whether there were uncommitted changes, host, pid, Python,
    Slurm job ids and rank. The text log gets a short summary.

    Args:
        logger: Logger to use. Defaults to the managed ``advlog`` logger.
        repo_dir: Directory inside the git repository to describe. Defaults to
                  the directory of the running script.
        packages: Distribution names whose versions to record, e.g. ``["numpy", "torch"]``

    Returns:
        The collected run info

    Example:
        >>> initialize(session_name="sim", file_format="both")
        >>> info = log_run_info(packages=["numpy"])
        >>> bind_context(git_sha=info["git"]["commit"])  # optionally tag every record
    """
    info = collect_run_info(repo_dir=repo_dir, packages=packages)

    git = info["git"]
    if git is None:
        git_text = "not a git repository (or git not found)"
    elif git["commit"] is None:
        git_text = "no commits yet"
    else:
        git_text = git["commit"][:12]
        if git["branch"]:
            git_text += f" on {git['branch']}"
        if git["dirty"]:
            git_text += ", uncommitted changes"

    lines = [
        f"Run started: {' '.join(info['argv'])}",
        f"git:  {git_text}",
        f"host: {info['hostname']} (pid {info['pid']}), Python {info['python']}",
    ]
    if "slurm" in info:
        lines.append("slurm: " + ", ".join(f"{key}={value}" for key, value in info["slurm"].items()))
    if "rank" in info:
        lines.append(f"rank: {info['rank']} of {info.get('world_size', '?')}")
    if "packages" in info:
        lines.append("packages: " + ", ".join(f"{name} {version}" for name, version in info["packages"].items()))

    _default_logger(logger).info("\n".join(lines), extra={"event": "run_start", "run_info": info}, stacklevel=2)
    return info


def log_metrics(
    metrics: Mapping[str, Any],
    step: int | None = None,
    logger: logging.Logger | None = None,
    **fields: Any,
) -> None:
    """Log a set of metrics, e.g. per iteration of a solver or per epoch.

    Writes one record with ``extra.event`` = "metrics", ``extra.step`` and
    ``extra.metrics``; keyword fields (``phase="val"``, ``epoch=3``, ...) are
    added next to them. The text log gets ``step 10: residual=1e-06, energy=-1.25``.

    Args:
        metrics: Metric names and values
        step: Iteration, epoch or other position in the run
        logger: Logger to use. Defaults to the managed ``advlog`` logger.
        **fields: Further fields for the record

    Example:
        >>> log_metrics({"residual": 3.2e-7, "energy": -1.25}, step=120)
        >>> # Later: df = pd.read_json("run.jsonl", lines=True)
        >>> #        metrics = pd.json_normalize(df[df["extra"].str["event"] == "metrics"]["extra"])
    """
    _check_fields(fields, "event")
    values = ", ".join(f"{name}={_format_value(value)}" for name, value in metrics.items())
    message = f"step {step}: {values}" if step is not None else values

    _default_logger(logger).info(
        message,
        extra={"event": "metrics", "step": step, "metrics": dict(metrics), **fields},
        stacklevel=2,
    )


def log_artifact(
    name: str,
    path: StrPath,
    logger: logging.Logger | None = None,
    **fields: Any,
) -> None:
    """Log a file or directory the run produced, so results can be traced to their run.

    Writes one record with ``extra.event`` = "artifact", ``extra.artifact``
    (the name), the absolute ``extra.path``, ``extra.exists`` and
    ``extra.size`` (bytes, files only). A path that does not exist is logged
    as a warning: it usually means the output was not written where expected.

    Args:
        name: Short name for the artifact, e.g. "reconstruction"
        path: Where it was written
        logger: Logger to use. Defaults to the managed ``advlog`` logger.
        **fields: Further fields for the record (e.g. ``kind="checkpoint"``)

    Example:
        >>> np.save("out/field.npy", field)
        >>> log_artifact("field", "out/field.npy")
    """
    _check_fields(fields, "event", "artifact", "path", "exists", "size")
    full_path = os.path.abspath(path)
    exists = os.path.exists(full_path)
    size = os.path.getsize(full_path) if os.path.isfile(full_path) else None

    if not exists:
        level, detail = logging.WARNING, "missing"
    elif size is None:
        level, detail = logging.INFO, "directory"
    else:
        level, detail = logging.INFO, _format_size(size)

    _default_logger(logger).log(
        level,
        f"Artifact {name}: {full_path} ({detail})",
        extra={"event": "artifact", "artifact": name, "path": full_path, "exists": exists, "size": size, **fields},
        stacklevel=2,
    )
