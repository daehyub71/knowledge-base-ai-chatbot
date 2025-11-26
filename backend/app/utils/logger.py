"""Logging configuration for the Knowledge Base AI Chatbot."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from app.config import settings


def setup_logging(
    log_level: str | None = None,
    log_file: str | None = None,
    log_dir: str = "logs",
) -> logging.Logger:
    """Set up application logging with console and file handlers.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Defaults to settings.log_level.
        log_file: Log file name. Defaults to 'app.log'.
        log_dir: Directory for log files. Defaults to 'logs'.

    Returns:
        Configured root logger.
    """
    # Use settings or defaults
    level = log_level or settings.log_level
    file_name = log_file or "app.log"

    # Convert level string to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        filename=log_path / file_name,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Set levels for noisy third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    root_logger.info(f"Logging initialized: level={level}, file={log_path / file_name}")

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


class RequestLogger:
    """Context manager for logging API requests."""

    def __init__(self, logger: logging.Logger, endpoint: str, method: str = ""):
        self.logger = logger
        self.endpoint = endpoint
        self.method = method
        self.start_time = None

    def __enter__(self):
        import time
        self.start_time = time.time()
        self.logger.info(f"Request started: {self.method} {self.endpoint}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        duration = time.time() - self.start_time
        if exc_type:
            self.logger.error(
                f"Request failed: {self.method} {self.endpoint} "
                f"[{duration:.3f}s] - {exc_type.__name__}: {exc_val}"
            )
        else:
            self.logger.info(
                f"Request completed: {self.method} {self.endpoint} [{duration:.3f}s]"
            )
        return False  # Don't suppress exceptions
