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

"""Demonstrate run records for a simulation: run info, metrics, artifacts.

An iterative solver logs where it ran (log_run_info), its residual per
iteration (log_metrics) and the file it wrote (log_artifact). The second half
reads the .jsonl file back: which commit produced the result, the convergence
curve, and where the output is.

Usage:
    python -m examples.real_world_demo.run_records_demo
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from advlog import initialize, log_artifact, log_metrics, log_run_info, setup_exception_logging

LOG_FILE = Path("./logs/run_records_demo.log")
JSONL_FILE = LOG_FILE.with_suffix(".jsonl")
OUTPUT = Path("./results/run_records_demo/solution.txt")


def solve() -> list[float]:
    """Jacobi iteration for a small diagonally dominant system."""
    a = [[4.0, 1.0, 0.0], [1.0, 4.0, 1.0], [0.0, 1.0, 4.0]]
    b = [1.0, 2.0, 3.0]
    x = [0.0, 0.0, 0.0]

    for iteration in range(1, 51):
        x = [(b[i] - sum(a[i][j] * x[j] for j in range(3) if j != i)) / a[i][i] for i in range(3)]
        residual = max(abs(sum(a[i][j] * x[j] for j in range(3)) - b[i]) for i in range(3))
        log_metrics({"residual": residual, "x0": x[0]}, step=iteration, phase="jacobi")
        if residual < 1e-10:
            break
    return x


def main() -> None:
    initialize(log_file_path=LOG_FILE, file_mode="w", file_format="both")
    setup_exception_logging()  # in a Slurm job: setup_exception_logging(sigterm=True)

    # ── Part 1: the run ────────────────────────────────────────────────────────
    log_run_info(packages=["rich"])  # e.g. ["numpy", "scipy"] in a real project

    x = solve()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(" ".join(f"{v:.12f}" for v in x) + "\n")
    log_artifact("solution", OUTPUT, kind="text")

    # ── Part 2: querying the .jsonl file ───────────────────────────────────────
    records = [json.loads(line) for line in JSONL_FILE.read_text(encoding="utf-8").splitlines()]

    def events(name: str) -> list[dict]:
        return [r["extra"] for r in records if r.get("extra", {}).get("event") == name]

    run = events("run_start")[0]["run_info"]
    print("\n[1] Produced by:")
    print(f"  command: {' '.join(run['argv'])}")
    print(f"  git:     {run['git']}")
    print(f"  host:    {run['hostname']}, Python {run['python']}")

    print("\n[2] Convergence:")
    for metrics in events("metrics")[::4]:
        print(f"  step {metrics['step']:>3}  residual {metrics['metrics']['residual']:.2e}")

    artifact = events("artifact")[0]
    print("\n[3] Output:")
    print(f"  {artifact['artifact']}: {artifact['path']} ({artifact['size']} bytes)")

    print(f"\nText log : {LOG_FILE.resolve()}")
    print(f"JSON log : {JSONL_FILE.resolve()}")


if __name__ == "__main__":
    main()
