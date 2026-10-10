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

"""Training-specific logging utilities."""

import csv
import logging
import os
from typing import Any

from advlog.utils.path import ensure_dir

try:
    from omegaconf import OmegaConf

    OMEGACONF_AVAILABLE = True
except ImportError:
    OMEGACONF_AVAILABLE = False

try:
    from torchinfo import summary  # type: ignore

    TORCHINFO_AVAILABLE = True
except ImportError:
    TORCHINFO_AVAILABLE = False


class TrainingLogger:
    """Logger with utilities for machine learning training.

    This class provides convenient methods for logging training
    information such as configurations, model summaries, and
    training metrics.

    Records report the location of your call, not of this class, and carry
    their data as ``extra`` fields for JSON log files.

    Usage:
        from advlog import TrainingLogger, get_logger

        logger = get_logger(__name__)
        trainer = TrainingLogger(logger)

        trainer.log_configuration(config)
        trainer.log_model_summary(model, input_size=(1, 3, 224, 224))
        trainer.log_train_step(epoch=1, total_epochs=10, ...)
    """

    def __init__(self, logger: logging.Logger):
        """Initialize the training logger.

        Args:
            logger: Python logging.Logger instance
        """
        self.logger = logger
        self._history = []

    def log_configuration(self, config: Any, title: str = "Hyperparameters"):
        """Log configuration/hyperparameters.

        Args:
            config: Configuration object (OmegaConf, dict, or any object)
            title: Section title for the log

        The header line carries the whole configuration as structured data
        (``extra["config"]``), so JSON log files hold it as a single record.

        Example:
            trainer.log_configuration(cfg, title="Training Config")
        """
        # stacklevel: 2 reports the caller of this method; the helpers below
        # sit one frame deeper and need 3
        self.logger.info(
            f"===== {title} =====",
            extra={"event": "config", "title": title, "config": self._config_to_data(config)},
            stacklevel=2,
        )

        if OMEGACONF_AVAILABLE and hasattr(config, "__module__"):
            # Try to detect OmegaConf objects
            if "omegaconf" in config.__module__:
                self.logger.info(OmegaConf.to_yaml(config), stacklevel=2)
            else:
                self._log_generic_config(config, stacklevel=3)
        elif isinstance(config, dict):
            self._log_dict_config(config, stacklevel=3)
        else:
            self._log_generic_config(config, stacklevel=3)

        self.logger.info("=" * (len(title) + 12), stacklevel=2)

    def _config_to_data(self, config: Any) -> Any:
        """Convert a configuration object to plain data for structured logging.

        Args:
            config: Configuration object (OmegaConf, dict, or any object)

        Returns:
            Plain dict where possible, otherwise the string form
        """
        if OMEGACONF_AVAILABLE and "omegaconf" in getattr(config, "__module__", ""):
            try:
                return OmegaConf.to_container(config, resolve=True)
            except Exception:
                # Missing values or unresolvable interpolations
                return OmegaConf.to_container(config, resolve=False)

        if isinstance(config, dict):
            return config

        if hasattr(config, "__dict__"):
            return {key: value for key, value in config.__dict__.items() if not key.startswith("_")}

        return str(config)

    def _log_dict_config(self, config: dict[str, Any], indent: int = 0, stacklevel: int = 2):
        """Log a dictionary configuration recursively.

        Args:
            config: Configuration dictionary
            indent: Current indentation level
            stacklevel: Frames between the logging call and the user's call site
        """
        for key, value in config.items():
            if isinstance(value, dict):
                self.logger.info("  " * indent + f"{key}:", stacklevel=stacklevel)
                self._log_dict_config(value, indent + 1, stacklevel + 1)
            else:
                self.logger.info("  " * indent + f"{key}: {value}", stacklevel=stacklevel)

    def _log_generic_config(self, config: Any, stacklevel: int = 2):
        """Log a generic configuration object.

        Args:
            config: Configuration object
            stacklevel: Frames between the logging call and the user's call site
        """
        if hasattr(config, "__dict__"):
            for key, value in config.__dict__.items():
                if not key.startswith("_"):
                    self.logger.info(f"{key}: {value}", stacklevel=stacklevel)
        else:
            self.logger.info(str(config), stacklevel=stacklevel)

    def log_model_summary(
        self, model: Any, input_size: tuple, module_name: str | None = None, depth: int = 3, verbose: int = 0
    ):
        """Log model architecture summary.

        Requires torchinfo to be installed.

        Args:
            model: PyTorch model
            input_size: Input tensor size (e.g., (1, 3, 224, 224))
            module_name: Optional module name for the title
            depth: Depth of nested modules to display
            verbose: Verbosity level (0, 1, or 2)

        Example:
            trainer.log_model_summary(model, (1, 3, 224, 224), "ResNet50")
        """
        if not TORCHINFO_AVAILABLE:
            self.logger.warning("torchinfo not available. Install with: pip install torchinfo", stacklevel=2)
            return

        if module_name:
            self.logger.info(f"====== Model Summary: {module_name} ======", stacklevel=2)
        else:
            self.logger.info("====== Model Summary ======", stacklevel=2)

        try:
            model_stats = summary(model, input_size=input_size, depth=depth, verbose=verbose)
            model_summary = str(model_stats)
            self.logger.info(model_summary, extra={"event": "model_summary", "module_name": module_name}, stacklevel=2)
        except Exception as e:
            self.logger.error(f"Failed to generate model summary: {e}", stacklevel=2)

        self.logger.info("=" * 30, stacklevel=2)

    def log_train_step(
        self,
        epoch: int,
        total_epochs: int,
        batch: int,
        total_batches: int,
        loss_dict: dict[str, float],
        time_elapsed: float,
        csv_path: str | None = None,
        additional_metrics: dict[str, Any] | None = None,
    ):
        """Log training step information.

        Args:
            epoch: Current epoch number
            total_epochs: Total number of epochs
            batch: Current batch number
            total_batches: Total number of batches
            loss_dict: Dictionary of loss values (e.g., {"loss": 0.5, "acc": 0.9})
            time_elapsed: Time elapsed for this step in seconds
            csv_path: Optional path to CSV file for logging metrics
            additional_metrics: Additional metrics to log

        Example:
            trainer.log_train_step(
                epoch=1, total_epochs=10,
                batch=50, total_batches=100,
                loss_dict={"loss": 0.5, "accuracy": 0.9},
                time_elapsed=1.2,
                csv_path="logs/metrics.csv"
            )
        """
        # Format loss string
        loss_str = ", ".join([f"{k}: {v:.4f}" for k, v in loss_dict.items()])

        # Add additional metrics if provided
        if additional_metrics:
            metrics_str = ", ".join([f"{k}: {v}" for k, v in additional_metrics.items()])
            message = (
                f"[{epoch}/{total_epochs}][{batch}/{total_batches}] {loss_str}, {metrics_str}, in {time_elapsed:.2f}s"
            )
        else:
            message = f"[{epoch}/{total_epochs}][{batch}/{total_batches}] {loss_str}, in {time_elapsed:.2f}s"

        # Log to console/file. The extra fields are what JSON log files record.
        self.logger.info(
            message,
            extra={
                "event": "train_step",
                "epoch": epoch,
                "total_epochs": total_epochs,
                "batch": batch,
                "total_batches": total_batches,
                "metrics": {**loss_dict, **(additional_metrics or {})},
                "time_elapsed": time_elapsed,
            },
            stacklevel=2,
        )

        # Log to CSV if requested
        if csv_path:
            self._log_to_csv(csv_path, epoch, batch, loss_dict, additional_metrics)

    def _log_to_csv(
        self,
        csv_path: str,
        epoch: int,
        batch: int,
        loss_dict: dict[str, float],
        additional_metrics: dict[str, Any] | None = None,
    ):
        """Log metrics to CSV file.

        Args:
            csv_path: Path to CSV file
            epoch: Current epoch
            batch: Current batch
            loss_dict: Loss values
            additional_metrics: Additional metrics
        """
        # Create directory if needed
        ensure_dir(csv_path)

        # Check if file exists
        file_exists = os.path.isfile(csv_path)

        # Prepare row data
        all_metrics = {**loss_dict}
        if additional_metrics:
            all_metrics.update(additional_metrics)

        try:
            with open(csv_path, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)

                # Write header if new file
                if not file_exists:
                    header = ["epoch", "batch"] + list(all_metrics.keys())
                    writer.writerow(header)

                # Write data row
                row = [epoch, batch] + list(all_metrics.values())
                writer.writerow(row)
        except Exception as e:
            # Called from log_train_step, so the user's call is three frames up
            self.logger.error(f"Failed to write to CSV file {csv_path}: {e}", stacklevel=3)

    def log_evaluation_results(
        self, metrics: dict[str, float], epoch: int | None = None, title: str = "Evaluation Results"
    ):
        """Log evaluation metrics.

        Args:
            metrics: Dictionary of evaluation metrics
            epoch: Optional epoch number
            title: Section title

        Example:
            trainer.log_evaluation_results(
                {"accuracy": 0.95, "f1_score": 0.93},
                epoch=10
            )
        """
        extra = {"event": "evaluation", "title": title, "epoch": epoch, "metrics": metrics}

        if epoch is not None:
            self.logger.info(f"===== {title} (Epoch {epoch}) =====", extra=extra, stacklevel=2)
        else:
            self.logger.info(f"===== {title} =====", extra=extra, stacklevel=2)

        for metric_name, value in metrics.items():
            if isinstance(value, float):
                self.logger.info(f"  {metric_name}: {value:.4f}", stacklevel=2)
            else:
                self.logger.info(f"  {metric_name}: {value}", stacklevel=2)

        self.logger.info("=" * (len(title) + 12), stacklevel=2)

    def cache_history(self, epoch: int, batch: int, loss: float):
        """Cache training history for later analysis.

        Args:
            epoch: Epoch number
            batch: Batch number
            loss: Loss value
        """
        self._history.append((epoch, batch, loss))

    def get_history(self):
        """Get cached training history.

        Returns:
            List of (epoch, batch, loss) tuples
        """
        return self._history

    def clear_history(self):
        """Clear cached training history."""
        self._history.clear()
