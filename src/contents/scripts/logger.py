import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Standard location for application state/logs on Linux
LOG_DIR = Path("~/.local/state/recent-tracker").expanduser()
LOG_FILE = LOG_DIR / "widget.log"

MAX_LOG_SIZE = 1 * 1024 * 1024  # 1 MB


def setup_logger() -> logging.Logger:
    """Configure a structured logger writing to file and console."""

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    logger = logging.getLogger("recent_tracker")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] " "[%(filename)s:%(lineno)d]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    try:
        # File handler with automatic log rotation, so the log file size doesn't explode
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=MAX_LOG_SIZE,
            backupCount=0,
            encoding="utf-8",
        )

        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    except Exception:
        pass

    # Stream handler for CLI debugging
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger


# Global logger instance
log = setup_logger()
