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

"""Console handler for terminal output."""

import logging
import sys
from typing import Optional

from advlog.utils.console import get_shared_console
from advlog.utils.rich_compat import RICH_AVAILABLE, Console


class ConsoleHandler:
    """Factory for creating console handlers.

    This class creates appropriate console handlers based on
    available libraries and configuration.
    """

    @staticmethod
    def create(
        use_color: bool = True,
        use_rich: bool = True,
        log_level: int = logging.DEBUG,
        show_location: bool = False,
        enable_rich_tracebacks: bool = True,
        console: Optional["Console"] = None,
    ) -> logging.Handler:
        """Create a console handler.

        Args:
            use_color: Enable colored output
            use_rich: Use Rich library if available
            log_level: Minimum log level to handle
            show_location: Show source location (file:line) in Rich sidebar
            enable_rich_tracebacks: Enable rich formatted tracebacks
            console: Custom Rich Console instance (created if None)

        Returns:
            Configured logging handler
        """
        from advlog.core.formatter import PlainFormatter

        # Use Rich handler if available and requested
        if use_rich and RICH_AVAILABLE:
            from rich.logging import RichHandler

            if console is None:
                console = get_shared_console()

            # Use RichHandler with native time format [yy/mm/dd hh:mm:ss]
            handler = RichHandler(
                console=console,
                show_time=True,
                log_time_format="[%y/%m/%d %H:%M:%S]",  # yy/mm/dd hh:mm:ss with brackets
                show_path=show_location,  # Rich shows filename:line in sidebar
                rich_tracebacks=enable_rich_tracebacks,
                markup=True,
            )
        else:
            # Fall back to standard StreamHandler
            handler = logging.StreamHandler(sys.stderr)
            fmt = "%(asctime)s [%(levelname)s] %(message)s"
            if show_location:
                fmt = "%(asctime)s [%(levelname)s] %(message)s (%(filename)s:%(lineno)d)"
            formatter = PlainFormatter(fmt=fmt, datefmt="%y/%m/%d %H:%M:%S")
            handler.setFormatter(formatter)

        handler.setLevel(log_level)

        return handler


def create_console_handler(
    use_color: bool = True, use_rich: bool = True, log_level: int = logging.DEBUG, show_location: bool = False, **kwargs
) -> logging.Handler:
    """Convenience function to create a console handler.

    Args:
        use_color: Enable colored output
        use_rich: Use Rich library if available
        log_level: Minimum log level to handle
        show_location: Show source location (file:line) in RichHandler sidebar
        **kwargs: Additional arguments passed to ConsoleHandler.create()

    Returns:
        Configured logging handler

    Example:
        handler = create_console_handler(use_color=True, log_level=logging.INFO, show_location=True)
    """
    return ConsoleHandler.create(use_color=use_color, use_rich=use_rich, log_level=log_level, show_location=show_location, **kwargs)
