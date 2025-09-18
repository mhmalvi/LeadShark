"""
Logging configuration and utilities.

Provides structured logging with Rich console formatting and file output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: Optional[Console] = None
) -> None:
    """Setup logging configuration.

    Args:
        level: Logging level
        log_file: Optional log file path
        console: Optional Rich console instance
    """
    # Create formatters
    console_formatter = logging.Formatter(
        '%(message)s'
    )

    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler with Rich
    if console is None:
        console = Console()

    console_handler = RichHandler(
        console=console,
        show_time=False,
        show_path=False,
        rich_tracebacks=True,
        tracebacks_show_locals=False
    )
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        root_logger.addHandler(file_handler)

    # Silence noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('google').setLevel(logging.WARNING)
    logging.getLogger('googleapiclient').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)