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
from typing import Any, Dict, Optional

from advlog.utils.path import ensure_dir

try:
    from omegaconf import OmegaConf

    OMEGACONF_AVAILABLE = True
except ImportError:
    OMEGACONF_AVAILABLE = False

try:
    from torchinfo import summary

    TORCHINFO_AVAILABLE = True
except ImportError:
    TORCHINFO_AVAILABLE = False


class TrainingLogger:
    """Logger with utilities for machine learning training.

    This class provides convenient methods for logging training
    information such as configurations, model summaries, and
    training metrics.

    Usage:
        from core import AdvancedLogger
        from plugins import TrainingLogger

        logger = AdvancedLogger().get_logger()
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

        Example:
            trainer.log_configuration(cfg, title="Training Config")
        """
        self.logger.info(f"===== {title} =====")

        if OMEGACONF_AVAILABLE and hasattr(config, "__module__"):
            # Try to detect OmegaConf objects
            if "omegaconf" in config.__module__:
                self.logger.info(OmegaConf.to_yaml(config))
            else:
                self._log_generic_config(config)
        elif isinstance(config, dict):
            self._log_dict_config(config)
        else:
            self._log_generic_config(config)

        self.logger.info("=" * (len(title) + 12))

    def _log_dict_config(self, config: Dict[str, Any], indent: int = 0):
        """Log a dictionary configuration recursively.

        Args:
            config: Configuration dictionary
            indent: Current indentation level
        """
        for key, value in config.items():
            if isinstance(value, dict):
                self.logger.info("  " * indent + f"{key}:")
                self._log_dict_config(value, indent + 1)
            else:
                self.logger.info("  " * indent + f"{key}: {value}")

    def _log_generic_config(self, config: Any):
        """Log a generic configuration object.

        Args:
            config: Configuration object
        """
        if hasattr(config, "__dict__"):
            for key, value in config.__dict__.items():
                if not key.startswith("_"):
                    self.logger.info(f"{key}: {value}")
        else:
            self.logger.info(str(config))

    def log_model_summary(
        self, model: Any, input_size: tuple, module_name: Optional[str] = None, depth: int = 3, verbose: int = 0
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
            self.logger.warning("torchinfo not available. Install with: pip install torchinfo")
            return

        if module_name:
            self.logger.info(f"====== Model Summary: {module_name} ======")
        else:
            self.logger.info("====== Model Summary ======")

        try:
            model_stats = summary(model, input_size=input_size, depth=depth, verbose=verbose)
            model_summary = str(model_stats)
            self.logger.info(model_summary)
        except Exception as e:
            self.logger.error(f"Failed to generate model summary: {e}")

        self.logger.info("=" * 30)

    def log_train_step(
        self,
        epoch: int,
        total_epochs: int,
        batch: int,
        total_batches: int,
        loss_dict: Dict[str, float],
        time_elapsed: float,
        csv_path: Optional[str] = None,
        additional_metrics: Optional[Dict[str, Any]] = None,
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

        # Log to console/file
        self.logger.info(message)

        # Log to CSV if requested
        if csv_path:
            self._log_to_csv(csv_path, epoch, batch, loss_dict, additional_metrics)

    def _log_to_csv(
        self,
        csv_path: str,
        epoch: int,
        batch: int,
        loss_dict: Dict[str, float],
        additional_metrics: Optional[Dict[str, Any]] = None,
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
            self.logger.error(f"Failed to write to CSV file {csv_path}: {e}")

    def log_evaluation_results(
        self, metrics: Dict[str, float], epoch: Optional[int] = None, title: str = "Evaluation Results"
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
        if epoch is not None:
            self.logger.info(f"===== {title} (Epoch {epoch}) =====")
        else:
            self.logger.info(f"===== {title} =====")

        for metric_name, value in metrics.items():
            if isinstance(value, float):
                self.logger.info(f"  {metric_name}: {value:.4f}")
            else:
                self.logger.info(f"  {metric_name}: {value}")

        self.logger.info("=" * (len(title) + 12))

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
