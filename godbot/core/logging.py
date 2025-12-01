"""
Unified Logging System for GodBot (Phase 11.1)
--------------------------------------------------
Provides:
    - get_logger(name)
    - Rotating file logs
    - Console logs
    - JSON log option (future)
    - Automatic logs directory creation
"""

from __future__ import annotations

import logging
import logging.handlers
import os
from typing import Optional


LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "bot.log")


def ensure_log_dir():
    """Create logs/ folder if missing."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)


def get_logger(name: str) -> logging.Logger:
    """
    Centralized logger for all GodBot modules.
    Uses rotating file logs + console output.
    """
    ensure_log_dir()

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        "[%(levelname)s] %(name)s: %(message)s"
    )
    console.setFormatter(console_fmt)
    logger.addHandler(console)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    return logger


# Global default logger
logger = get_logger("GodBot")

