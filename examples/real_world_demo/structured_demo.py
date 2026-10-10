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

"""Demonstrate structured (JSON Lines) logging for a training run.

With file_format="both" every record is written twice:
    logs/structured_demo.log    - human-readable text, same as before
    logs/structured_demo.jsonl  - one JSON object per line, for parsing/querying

Anything passed via extra={...} is invisible in the text log but stored under
the "extra" key in the .jsonl file, and so are the context fields bound once
at startup (run_id, seed). The second half of this script reads the .jsonl
file back and answers a few questions that would need regex-scraping with a
text log.

Usage:
    python -m examples.real_world_demo.structured_demo
"""

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from advlog import TrainingLogger, bind_context, get_logger, initialize, unbind_context

LOG_FILE = Path("./logs/structured_demo.log")
JSONL_FILE = LOG_FILE.with_suffix(".jsonl")

# ── Setup ──────────────────────────────────────────────────────────────────────

initialize(
    log_file_path=str(LOG_FILE),
    file_mode="w",
    log_level="INFO",
    file_format="both",  # <-- text log + .jsonl next to it
    context={"run_id": "run_001", "seed": 42},  # <-- attached to every record
)

log = get_logger(__name__)
trainer = TrainingLogger(log)


# ── Part 1: a simulated training run ───────────────────────────────────────────


def fake_loss(step: int) -> float:
    """Decaying loss that blows up to NaN once, like a bad batch would."""
    if step == 7:
        return math.nan
    return 2.0 * math.exp(-0.25 * step) + 0.1


def run_training() -> None:
    # Run parameters: logged once, stored as ONE structured record
    params = {
        "model": {"name": "resnet18", "depth": 18, "dropout": 0.1},
        "optimizer": {"name": "adamw", "lr": 1e-3, "weight_decay": 0.01},
        "data": {"dataset": "cifar10", "batch_size": 64, "image_size": (32, 32)},
        "output_dir": Path("./results/run_001"),  # not JSON-native, converted to str
        "seed": 42,
    }
    trainer.log_configuration(params, title="Run Parameters")

    # Plain logger call with ad-hoc structured fields
    log.info("Dataset loaded", extra={"event": "data_loaded", "train_samples": 50000, "val_samples": 10000})

    # Decoration for the human reader only: kept out of the .jsonl file
    log.info("-" * 40, extra={"text_only": True})
    log.info("[bold green]Training started[/bold green]")  # markup colors the console, files get plain text

    total_epochs, total_batches = 3, 4
    step = 0
    for epoch in range(1, total_epochs + 1):
        bind_context(epoch=epoch)  # every record of this epoch now carries it
        for batch in range(1, total_batches + 1):
            step += 1
            loss = fake_loss(step)
            lr = 1e-3 * (0.5 ** (epoch - 1))

            trainer.log_train_step(
                epoch=epoch,
                total_epochs=total_epochs,
                batch=batch,
                total_batches=total_batches,
                loss_dict={"loss": loss},
                time_elapsed=0.12,
                additional_metrics={"lr": lr},
            )

            if math.isnan(loss):
                log.warning(
                    "Loss is NaN, skipping optimizer step",
                    extra={"event": "nan_loss", "epoch": epoch, "batch": batch, "step": step},
                )

        trainer.log_evaluation_results({"val_loss": fake_loss(step + 1), "val_acc": 0.6 + 0.1 * epoch}, epoch=epoch)

    unbind_context("epoch")

    # Exceptions keep their traceback, plus whatever context you attach
    try:
        raise PermissionError("results/run_001/ckpt_final.pt is read-only")
    except PermissionError:
        log.exception("Checkpoint save failed", extra={"event": "checkpoint_failed", "epoch": total_epochs})

    log.info("Run finished", extra={"event": "run_end", "total_steps": step})


# ── Part 2: querying the .jsonl file afterwards ────────────────────────────────


def analyze() -> None:
    records = [json.loads(line) for line in JSONL_FILE.read_text(encoding="utf-8").splitlines()]

    def events(name: str) -> list[dict]:
        return [r for r in records if r.get("extra", {}).get("event") == name]

    print()
    print("=" * 70)
    print(f"Read {len(records)} records back from {JSONL_FILE}")
    print("=" * 70)

    print("\n[1] Run parameters (one record, nested structure intact):")
    print(json.dumps(events("config")[0]["extra"]["config"], indent=2))

    print("\n[2] Loss curve (no regex over message text needed):")
    print(f"  {'epoch':>5} {'batch':>5} {'loss':>8} {'lr':>10}")
    for r in events("train_step"):
        e = r["extra"]
        loss = e["metrics"]["loss"]
        loss_str = f"{loss:8.4f}" if loss is not None else "    null"
        print(f"  {e['epoch']:>5} {e['batch']:>5} {loss_str} {e['metrics']['lr']:>10.2e}")

    print("\n[3] Steps where loss was NaN (stored as null):")
    for r in events("train_step"):
        if r["extra"]["metrics"]["loss"] is None:
            print(f"  epoch {r['extra']['epoch']}, batch {r['extra']['batch']}  ->  message was: {r['message']}")

    print("\n[4] Best validation accuracy:")
    best = max(events("evaluation"), key=lambda r: r["extra"]["metrics"]["val_acc"])
    print(f"  epoch {best['extra']['epoch']}: {best['extra']['metrics']}")

    print("\n[5] Everything at WARNING or above:")
    for r in records:
        if r["level"] in ("WARNING", "ERROR", "CRITICAL"):
            print(f"  {r['timestamp']}  {r['level']:<7}  {r['message']}  extra={r.get('extra')}")
            if "exception" in r:
                print(f"      exception: {r['exception'].splitlines()[-1]}")

    print("\n[6] Records per logging call site (TrainingLogger reports the caller, not itself):")
    sites: dict[str, int] = {}
    for r in records:
        site = f"{r['module']}.{r['function']}"
        sites[site] = sites.get(site, 0) + 1
    for site, count in sites.items():
        print(f"  {site}: {count}")

    print("\n[7] One raw line from the file, for reference:")
    print("  " + next(line for line in JSONL_FILE.read_text(encoding="utf-8").splitlines() if "train_step" in line))

    print()
    print(f"Text log : {LOG_FILE.resolve()}")
    print(f"JSON log : {JSONL_FILE.resolve()}")


def main() -> None:
    run_training()
    analyze()


if __name__ == "__main__":
    main()
