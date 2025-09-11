"""
Logging utilities for the security_utils package.

This module provides functions to configure and retrieve loggers with appropriate handlers and log levels
based on the environment. It supports both console and file logging with rotation.
"""

import logging
import logging.handlers
import os


def get_log_level() -> int:
    """
    Get the logging level based on the ENVIRONMENT environment variable.

    Returns
    -------
    int
        The logging level (e.g., logging.DEBUG or logging.INFO).
    """
    ENVIRONMENT = os.getenv("ENVIRONMENT", "prod")
    return (
        logging.DEBUG
        if ENVIRONMENT not in ["prod", "production"]
        else logging.INFO
    )


def setup(identifier: str, logger_target: str) -> None:
    """
    Set up logging for a given identifier and logger target.

    Configures both console and file handlers (with daily rotation) for the logger.
    The log level is determined by the environment.

    Parameters
    ----------
    identifier : str
        Identifier to include in log messages (e.g., the service or module name).
    logger_target : str
        Name of the logger to configure.

    Returns
    -------
    None
    """
    LOG_LEVEL = get_log_level()
    LOG_FORMAT = logging.Formatter(
        f"[%(asctime)s][{identifier}][%(levelname)s][%(name)s]: %(message)s"
    )
    LOGS_DIR = os.path.join(os.path.dirname(__file__), "_logs")

    # Get logger
    logger = logging.getLogger(logger_target)
    logger.setLevel(LOG_LEVEL)
    logger.propagate = True

    # Add handlers if not already added
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LOG_LEVEL)
        console_handler.setFormatter(LOG_FORMAT)
        logger.addHandler(console_handler)

        # File handler
        os.makedirs(LOGS_DIR, exist_ok=True)  # Ensure LOGS_DIR exists

        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(LOGS_DIR, "logs.log"),
            when="D",  # interval = DAYS
            encoding="UTF-8",
            backupCount=14,
        )
        file_handler.setLevel(LOG_LEVEL)
        file_handler.setFormatter(LOG_FORMAT)
        logger.addHandler(file_handler)

        logging.getLogger().addHandler(file_handler)

    logger.info(f"LOGGER LEVEL: {logging.getLevelName(logger.level)}")
