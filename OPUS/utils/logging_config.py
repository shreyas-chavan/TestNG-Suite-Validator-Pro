#!/usr/bin/env python3
"""
Structured logging configuration for the application.
Provides file + console logging with configurable levels.
"""

import logging
import sys
from pathlib import Path
from ..config import LOG_FILE, LOG_FORMAT, LOG_DATE_FORMAT, LOG_LEVEL


def setup_logging(debug: bool = False) -> logging.Logger:
    """
    Configure structured logging for the application.

    Args:
        debug: If True, sets console level to DEBUG.

    Returns:
        The root application logger.
    """
    level = logging.DEBUG if debug else LOG_LEVEL
    root_logger = logging.getLogger("testng_validator")
    root_logger.setLevel(logging.DEBUG)  # Capture everything; handlers filter

    # Remove existing handlers to avoid duplicates on re-init
    root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)
    root_logger.addHandler(console)

    # File handler (rotates implicitly by overwrite on each session)
    try:
        file_handler = logging.FileHandler(str(LOG_FILE), mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception:
        root_logger.warning("Could not create log file at %s", LOG_FILE)

    return root_logger
