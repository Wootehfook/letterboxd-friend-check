"""
Logging configuration for the Letterboxd Friend Check application
"""

import os
import logging
from pathlib import Path


def setup_logging(level=logging.INFO, log_file=None, console=True):
    """
    Set up logging for the application

    Args:
        level: Logging level
        log_file: Path to log file (if None, will use default)
        console: Whether to log to console
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Format for logs
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Add console handler if requested
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if requested or default
    if log_file is None:
        # Use default log file in logs directory
        project_root = Path(__file__).parent.parent.parent
        log_dir = project_root / "logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = log_dir / "output.log"

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
