"""
Logging utilities for the security_utils package.

This module provides a function to configure and retrieve loggers with appropriate handlers and log levels
based on the project environment. It supports both console and file logging with rotation, and allows
customization of the log level.

Functions
---------
setup :
    Set up logging for a given identifier and logger target, with support for console and file handlers.
"""

import inspect
import logging
import logging.handlers
import os
import warnings
from collections.abc import Iterable
from typing import Optional

from security_utils.environment import get_project_environment

_Level = int | str


class LoggerManager:
    """
    LoggerManager provides classmethods to configure and retrieve loggers with appropriate handlers and log levels.

    This class is designed for quick, top-level logger setup in other packages, especially in their __init__.py.
    It supports both console and file logging with rotation, and allows customization of the log level and log directory.
    """

    _IDENTIFIER: str
    _LOGS_PATH: str | os.PathLike
    _LOG_LEVEL: _Level

    @classmethod
    def LOG_LEVEL(cls) -> _Level:
        """
        Get the current log level for the logger.

        Returns
        -------
        _Level
            The logging level (e.g., logging.DEBUG, logging.INFO).
        """
        if hasattr(cls, "_LOG_LEVEL") and isinstance(
            cls._LOG_LEVEL, (str, int)
        ):
            return cls._LOG_LEVEL
        try:
            ENVIRONMENT = get_project_environment()
            cls._LOG_LEVEL = (
                logging.DEBUG
                if ENVIRONMENT not in ["prod", "production"]
                else logging.INFO
            )
        except:  # noqa: E722
            cls._LOG_LEVEL = logging.CRITICAL

        return cls._LOG_LEVEL

    @classmethod
    def LOG_FORMAT(cls) -> logging.Formatter:
        """
        Get the log message format for the logger.

        Returns
        -------
        logging.Formatter
            Formatter for log messages including timestamp, identifier, level, and logger name.

        Raises
        ------
        AttributeError
            If _IDENTIFIER is not set on the class.
        """
        if hasattr(cls, "_IDENTIFIER") and isinstance(
            getattr(cls, "_IDENTIFIER", None), str
        ):
            return logging.Formatter(
                f"[%(asctime)s][{cls._IDENTIFIER}][%(levelname)s][%(name)s]: %(message)s"
            )
        raise AttributeError(
            f"{cls.__name__} has no attribute _IDENTIFIER or it is not a string"
        )

    @classmethod
    def LOG_DIRECTORY(cls) -> str:
        """
        Get the directory where log files will be stored.

        Returns
        -------
        str
            Path to the log directory.

        Notes
        -----
        If LOGS_PATH is not set, attempts to infer the directory from the caller's package (__init__.py).
        If that fails, defaults to the directory of this file and issues a warning.
        """
        # Setup the Log File Directory
        if not isinstance(
            getattr(cls, "_LOGS_PATH", None), (str | os.PathLike)
        ):
            caller_frame = inspect.stack()
            for stack_element in caller_frame:
                if "__init__.py" in stack_element.filename:
                    caller_file = stack_element.filename
                    caller_dir = os.path.dirname(os.path.abspath(caller_file))
                    break

            if "caller_dir" in locals():
                LOGS_DIR = os.path.join(caller_dir, "_logs")  # pyright: ignore[reportPossiblyUnboundVariable]
            else:
                LOGS_DIR = os.path.join(os.path.dirname(__file__), "_logs")
                warnings.warn(
                    f"Failed to locate an __init__.py in the call stack. Defaulting logs directory to {LOGS_DIR}",
                    stacklevel=1,
                )
        else:
            processed_path = os.path.abspath(os.fspath(cls._LOGS_PATH))
            LOGS_DIR = os.path.join(processed_path, "_logs")
        return LOGS_DIR

    @classmethod
    def setup(
        cls,
        identifier: str,
        logger_target: str,
        log_level: Optional[_Level] = None,
        logger_files_path: Optional[str | os.PathLike] = None,
        propagate: bool = True,
        console_handler: bool = True,
        rotating_file_handler: bool = True,
        handlers: Optional[Iterable[logging.Handler]] = None,
    ) -> None:
        """
        Set up logging for a given identifier and logger target.

        Configures both console and file handlers (with daily rotation) for the logger.
        The log level is determined by the environment or can be set explicitly.
        The log file directory can be customized or inferred from the caller's package.

        Parameters
        ----------
        identifier : str
            Identifier to include in log messages (e.g., the service or module name).
        logger_target : str
            Name of the logger to configure (typically __name__ or __package__).
        log_level : int, optional
            Logging level to use (e.g., logging.DEBUG, logging.INFO). If not provided, the level is
            determined by the project environment ("prod"/"production" = INFO, otherwise DEBUG).
        logger_files_path : str or os.PathLike, optional
            Directory in which to store log files. If not provided, attempts to infer from the caller's package.
        propagate : bool, optional
            Whether log messages are passed to ancestor loggers. Default is True.
        console_handler : bool, optional
            Whether to add a console handler. Default is True.
        rotating_file_handler : bool, optional
            Whether to add a rotating file handler. Default is True.
        handlers : Iterable[logging.Handler], optional
            Additional custom handlers to add to the logger.

        Returns
        -------
        None

        Examples
        --------
        Basic usage with default log directory:
            >>> from security_utils.logging import LoggerManager
            >>> LoggerManager.setup("MyService", __name__)

        Specify a custom log directory:
            >>> from security_utils.logging import LoggerManager
            >>> LoggerManager.setup("MyService", __name__, logger_files_path="/tmp/my_logs")

        Set a custom log level:
            >>> from security_utils.logging import LoggerManager
            >>> import logging
            >>> LoggerManager.setup("MyService", __name__, log_level=logging.WARNING)

        Use with __package__ to group logs by package:
            >>> from security_utils.logging import LoggerManager
            >>> LoggerManager.setup("MyService", __package__)
        """
        cls._IDENTIFIER = identifier
        if isinstance(log_level, _Level):
            cls._LOG_LEVEL = log_level
        if isinstance(logger_files_path, (str, os.PathLike)):
            cls._LOGS_PATH = logger_files_path

        # Get logger
        logger = logging.getLogger(logger_target)
        logger.setLevel(cls.LOG_LEVEL())
        logger.propagate = propagate

        # Add handlers
        log_handlers: list[logging.Handler] = []
        if console_handler:
            log_handlers.append(cls.get_console_handler())
        if rotating_file_handler:
            log_handlers.append(cls.get_rotating_file_handler())
        if isinstance(handlers, Iterable) and any(
            filter(
                lambda handler: isinstance(handler, logging.Handler), handlers
            )
        ):
            log_handlers += handlers

        for handler in log_handlers:
            logger.addHandler(handler)

        logger.critical(f"LOGGER LEVEL: {logging.getLevelName(logger.level)}")
        logger.info(f"LOG DIRECTORY: {cls.LOG_DIRECTORY()}")

    @classmethod
    def get_console_handler(
        cls,
    ) -> logging.StreamHandler:
        """
        Create and return a console (stream) handler for logging.

        Returns
        -------
        logging.StreamHandler
            Configured stream handler for console output.
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(cls.LOG_LEVEL())
        console_handler.setFormatter(cls.LOG_FORMAT())
        return console_handler

    @classmethod
    def get_rotating_file_handler(
        cls,
    ) -> logging.handlers.TimedRotatingFileHandler:
        """
        Create and return a timed rotating file handler for logging.

        Returns
        -------
        logging.handlers.TimedRotatingFileHandler
            Configured file handler with daily rotation and backup.
        """
        os.makedirs(
            cls.LOG_DIRECTORY(), exist_ok=True
        )  # Ensure LOGS_DIR exists

        file_handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(cls.LOG_DIRECTORY(), "logs.log"),
            when="D",  # interval = DAYS
            encoding="UTF-8",
            backupCount=14,
        )
        file_handler.setLevel(cls.LOG_LEVEL())
        file_handler.setFormatter(cls.LOG_FORMAT())
        return file_handler
