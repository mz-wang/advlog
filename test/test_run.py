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

"""Tests for run records: run info, metrics and artifacts."""

import json
import logging
import shutil
import subprocess

import pytest

from advlog import collect_run_info, initialize, log_artifact, log_metrics, log_run_info, reset

needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="git not installed")


class _ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def logger_and_records():
    logger = logging.getLogger("test.run")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    handler = _ListHandler()
    logger.addHandler(handler)
    yield logger, handler.records
    logger.removeHandler(handler)


def _git(repo, *args):
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test@example.com", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


@pytest.fixture
def repo(tmp_path):
    path = tmp_path / "repo"
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    return path


@pytest.fixture
def no_run_env(monkeypatch):
    from advlog.utils.environment import _SLURM_FIELDS

    for variable in (*_SLURM_FIELDS.values(), "RANK", "WORLD_SIZE"):
        monkeypatch.delenv(variable, raising=False)


@needs_git
class TestGitState:
    def test_clean_commit(self, repo):
        (repo / "a.py").write_text("x = 1\n")
        _git(repo, "add", "a.py")
        _git(repo, "commit", "-q", "-m", "first")
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True).stdout.strip()

        assert collect_run_info(repo_dir=repo)["git"] == {"commit": head, "branch": "main", "dirty": False}

    def test_untracked_files_do_not_make_it_dirty(self, repo):
        (repo / "a.py").write_text("x = 1\n")
        _git(repo, "add", "a.py")
        _git(repo, "commit", "-q", "-m", "first")
        (repo / "results.log").write_text("output\n")
        assert collect_run_info(repo_dir=repo)["git"]["dirty"] is False

        (repo / "a.py").write_text("x = 2\n")
        assert collect_run_info(repo_dir=repo)["git"]["dirty"] is True

    def test_repository_without_commits(self, repo):
        assert collect_run_info(repo_dir=repo)["git"] == {"commit": None, "branch": "main", "dirty": False}


class TestCollectRunInfo:
    def test_outside_a_repository(self, tmp_path):
        assert collect_run_info(repo_dir=tmp_path)["git"] is None

    def test_git_missing(self, tmp_path, monkeypatch):
        def missing(*args, **kwargs):
            raise FileNotFoundError("git")

        monkeypatch.setattr(subprocess, "run", missing)
        assert collect_run_info(repo_dir=tmp_path)["git"] is None

    def test_basic_fields(self, tmp_path, no_run_env):
        import os
        import sys

        info = collect_run_info(repo_dir=tmp_path)
        assert info["argv"] == sys.argv
        assert info["pid"] == os.getpid()
        assert info["executable"] == sys.executable
        for key in ("cwd", "python", "platform", "hostname"):
            assert isinstance(info[key], str)
        for key in ("packages", "slurm", "rank", "world_size"):
            assert key not in info
        json.dumps(info)  # all JSON-serializable

    def test_packages(self, tmp_path):
        from importlib import metadata

        info = collect_run_info(repo_dir=tmp_path, packages=["rich", "surely-not-installed-pkg"])
        assert info["packages"] == {"rich": metadata.version("rich"), "surely-not-installed-pkg": None}

    def test_slurm_and_rank(self, tmp_path, monkeypatch, no_run_env):
        monkeypatch.setenv("SLURM_JOB_ID", "9001")
        monkeypatch.setenv("SLURM_ARRAY_TASK_ID", "3")
        monkeypatch.setenv("RANK", "1")
        monkeypatch.setenv("WORLD_SIZE", "4")

        info = collect_run_info(repo_dir=tmp_path)
        assert info["slurm"] == {"job_id": "9001", "array_task_id": "3"}
        assert (info["rank"], info["world_size"]) == (1, 4)


class TestLogRunInfo:
    def test_one_structured_record(self, logger_and_records, tmp_path, no_run_env):
        logger, records = logger_and_records
        info = log_run_info(logger, repo_dir=tmp_path, packages=["rich"])

        assert len(records) == 1
        record = records[0]
        assert record.event == "run_start"
        assert record.run_info == info
        assert record.filename == "test_run.py"  # the caller, not run.py
        message = record.getMessage()
        assert message.startswith("Run started: ")
        assert "git:  not a git repository" in message
        assert f"pid {info['pid']}" in message
        assert "packages: rich " in message

    @needs_git
    def test_summary_shows_commit_and_changes(self, logger_and_records, repo):
        logger, records = logger_and_records
        (repo / "a.py").write_text("x = 1\n")
        _git(repo, "add", "a.py")
        _git(repo, "commit", "-q", "-m", "first")
        (repo / "a.py").write_text("x = 2\n")

        info = log_run_info(logger, repo_dir=repo)
        assert f"git:  {info['git']['commit'][:12]} on main, uncommitted changes" in records[0].getMessage()

    def test_json_output_through_default_logger(self, tmp_path):
        initialize(log_file_path=tmp_path / "run.jsonl", file_format="json")
        log_run_info(repo_dir=tmp_path)
        reset()

        record = json.loads((tmp_path / "run.jsonl").read_text(encoding="utf-8"))
        assert record["logger"] == "advlog"
        assert record["extra"]["event"] == "run_start"
        assert record["extra"]["run_info"]["git"] is None


class TestLogMetrics:
    def test_record_and_message(self, logger_and_records):
        logger, records = logger_and_records
        log_metrics({"residual": 3.2e-7, "energy": -1.25, "iterations": 40}, step=120, logger=logger, phase="solve")

        record = records[0]
        assert record.getMessage() == "step 120: residual=3.2e-07, energy=-1.25, iterations=40"
        assert record.event == "metrics"
        assert record.step == 120
        assert record.metrics == {"residual": 3.2e-7, "energy": -1.25, "iterations": 40}
        assert record.phase == "solve"
        assert record.filename == "test_run.py"

    def test_without_step(self, logger_and_records):
        logger, records = logger_and_records
        log_metrics({"psnr": 31.123456789}, logger=logger)
        assert records[0].getMessage() == "psnr=31.1235"
        assert records[0].step is None

    def test_event_cannot_be_overridden(self, logger_and_records):
        logger, _ = logger_and_records
        with pytest.raises(ValueError, match="event"):
            log_metrics({"x": 1}, logger=logger, event="other")

    def test_json_round_trip(self, tmp_path):
        initialize(log_file_path=tmp_path / "run.jsonl", file_format="json")
        for step in range(3):
            log_metrics({"loss": 1.0 / (step + 1)}, step=step)
        reset()

        lines = (tmp_path / "run.jsonl").read_text(encoding="utf-8").splitlines()
        extras = [json.loads(line)["extra"] for line in lines]
        assert [(e["step"], e["metrics"]["loss"]) for e in extras] == [(0, 1.0), (1, 0.5), (2, 1.0 / 3)]


class TestLogArtifact:
    def test_file(self, logger_and_records, tmp_path):
        logger, records = logger_and_records
        path = tmp_path / "field.npy"
        path.write_bytes(b"\0" * 2048)
        log_artifact("field", path, logger=logger, kind="array")

        record = records[0]
        assert record.levelno == logging.INFO
        assert record.getMessage() == f"Artifact field: {path} (2.0 KB)"
        assert (record.event, record.artifact, record.path) == ("artifact", "field", str(path))
        assert (record.exists, record.size, record.kind) == (True, 2048, "array")

    def test_directory(self, logger_and_records, tmp_path):
        logger, records = logger_and_records
        log_artifact("outputs", tmp_path, logger=logger)
        assert records[0].getMessage().endswith("(directory)")
        assert (records[0].exists, records[0].size) == (True, None)

    def test_missing_path_warns(self, logger_and_records, tmp_path):
        logger, records = logger_and_records
        log_artifact("checkpoint", tmp_path / "nope.pt", logger=logger)
        assert records[0].levelno == logging.WARNING
        assert records[0].getMessage().endswith("(missing)")
        assert records[0].exists is False

    def test_relative_path_made_absolute(self, logger_and_records, tmp_path, monkeypatch):
        logger, records = logger_and_records
        monkeypatch.chdir(tmp_path)
        (tmp_path / "out.txt").write_text("x")
        log_artifact("out", "out.txt", logger=logger)
        assert records[0].path == str(tmp_path / "out.txt")
