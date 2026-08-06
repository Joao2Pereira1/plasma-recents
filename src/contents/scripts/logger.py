#!/usr/bin/env python3

"""Centralized logging module for the vscode-recent application.

Configures a logger that outputs structured messages to both a persistent log file
located in the XDG state directory (~/.local/state/vscode-recent/widget.log)
and stderr for CLI debugging.
"""

import logging
from pathlib import Path

# Standard location for application state/logs in Linux (XDG State)
LOG_DIR = Path("~/.local/state/vscode-recent").expanduser()
LOG_FILE = LOG_DIR / "widget.log"


def setup_logger() -> logging.Logger:
    """Configure a structured logger writing to file and console."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    logger = logging.getLogger("vscode_recent")
    logger.setLevel(logging.DEBUG)

    # Prevent adding duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        return logger

    # Log format: [2026-08-05 18:30:00] [ERROR] [database_locator]: Message...
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        # File Handler (Stores history of errors, warnings, and system events)
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception:
        pass

    # Stream Handler (Useful for debugging in terminal when running via CLI)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


# Global logger instance ready to be imported across modules
log = setup_logger()
