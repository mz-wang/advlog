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

"""Tests for the structured data TrainingLogger attaches to its records."""

import json
import logging

import pytest

from advlog import JSONFormatter, TrainingLogger


class _ListHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def trainer_and_records():
    logger = logging.getLogger("test.training")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    handler = _ListHandler()
    logger.addHandler(handler)
    yield TrainingLogger(logger), handler.records
    logger.removeHandler(handler)


def _events(records, event):
    return [r for r in records if getattr(r, "event", None) == event]


class TestTrainingLoggerStructuredData:
    def test_configuration_logged_as_one_structured_record(self, trainer_and_records):
        trainer, records = trainer_and_records
        config = {"lr": 0.001, "model": {"name": "resnet", "depth": 50}}
        trainer.log_configuration(config, title="Run Config")

        events = _events(records, "config")
        assert len(events) == 1
        assert events[0].config == config
        assert events[0].title == "Run Config"
        # Human-readable lines are still emitted
        assert any(r.getMessage() == "lr: 0.001" for r in records)

    def test_configuration_from_plain_object(self, trainer_and_records):
        trainer, records = trainer_and_records

        class Config:
            def __init__(self):
                self.lr = 0.01
                self._private = "hidden"

        trainer.log_configuration(Config())
        assert _events(records, "config")[0].config == {"lr": 0.01}

    def test_train_step_carries_metrics(self, trainer_and_records):
        trainer, records = trainer_and_records
        trainer.log_train_step(
            epoch=1,
            total_epochs=10,
            batch=50,
            total_batches=100,
            loss_dict={"loss": 0.5},
            time_elapsed=1.2,
            additional_metrics={"lr": 0.001},
        )

        record = _events(records, "train_step")[0]
        assert record.epoch == 1
        assert record.batch == 50
        assert record.metrics == {"loss": 0.5, "lr": 0.001}
        assert record.time_elapsed == 1.2
        assert "loss: 0.5000" in record.getMessage()

    def test_evaluation_carries_metrics(self, trainer_and_records):
        trainer, records = trainer_and_records
        trainer.log_evaluation_results({"accuracy": 0.95}, epoch=3)

        events = _events(records, "evaluation")
        assert len(events) == 1
        assert events[0].epoch == 3
        assert events[0].metrics == {"accuracy": 0.95}

    def test_records_report_callers_location(self, trainer_and_records):
        trainer, records = trainer_and_records
        trainer.log_configuration({"lr": 0.001, "model": {"depth": {"blocks": 4}}})
        trainer.log_train_step(
            epoch=1, total_epochs=2, batch=1, total_batches=2, loss_dict={"loss": 0.25}, time_elapsed=0.1
        )
        trainer.log_evaluation_results({"accuracy": 0.95})

        assert records
        # Every line, including nested config lines, points at this test rather than training.py
        assert {r.funcName for r in records} == {"test_records_report_callers_location"}
        assert {r.filename for r in records} == {"test_training.py"}

    def test_display_lines_marked_text_only(self, trainer_and_records):
        trainer, records = trainer_and_records
        trainer.log_configuration({"lr": 0.001, "model": {"depth": 50}})
        trainer.log_evaluation_results({"accuracy": 0.95})

        structured = [r for r in records if not getattr(r, "text_only", False)]
        assert [r.event for r in structured] == ["config", "evaluation"]
        # header + 3 config lines + footer, header + 1 metric line + footer
        assert len(records) == 8

    def test_records_serialize_to_json(self, trainer_and_records):
        trainer, records = trainer_and_records
        trainer.log_train_step(
            epoch=1, total_epochs=2, batch=1, total_batches=2, loss_dict={"loss": 0.25}, time_elapsed=0.1
        )

        data = json.loads(JSONFormatter().format(records[0]))
        assert data["extra"]["event"] == "train_step"
        assert data["extra"]["metrics"] == {"loss": 0.25}
