"""security_utils.logging.manager
================================

Utilities to configure module/package loggers consistently across the
project.

This module exposes :class:`LoggerManager`, a convenience manager for
creating and configuring a named :class:`logging.Logger` with
console and rotating file handlers. It centralizes log formatting,
log directory selection and default log level decisions so packages can
use a single, predictable logging configuration.

Functions
---------
setup
    Convenience wrapper (via :class:`LoggerManager.setup`) to configure a
    logger for a given identifier and target.
"""

import inspect
import logging
import logging.handlers
import os
import warnings
from collections.abc import Iterable
from typing import Optional

from .formatter import ExpandedFormatter

_Level = int | str


class LoggerManager:
    """
    Manager for configuring package loggers with sensible defaults.

    The class exposes classmethods that configure a logger's level,
    attach handlers (console and timed rotating file handler), and set a
    structured formatter. Intended for lightweight, top-level use (for
    example, in a package ``__init__``) to ensure consistent logging
    behavior across consumers of the package.

    Attributes
    ----------
    _IDENTIFIER : str
        Service or package identifier inserted into formatted log records.
    _LOGS_PATH : str | os.PathLike
        Optional base directory in which log subdirectory ``_logs`` is
        created for file handlers.
    _LOG_LEVEL : int | str
        Optional override for the logger level. When not provided, the
        manager inspects the environment to choose a default level.
    """

    _IDENTIFIER: str
    _LOGS_PATH: str | os.PathLike
    _LOG_LEVEL: _Level

    @classmethod
    def LOG_LEVEL(cls) -> _Level:
        """
        Determine the effective log level for loggers configured by the
        manager.

        The method returns an explicitly configured ``_LOG_LEVEL`` when
        present on the class. Otherwise it inspects the environment
        variable ``DEBUG_MODE`` to decide between ``logging.DEBUG`` and
        ``logging.INFO``.

        Returns
        -------
        int | str
            The logging level value suitable for ``logger.setLevel``. This
            may be an integer (e.g. ``logging.DEBUG``) or a string name of
            the level.
        """
        if hasattr(cls, "_LOG_LEVEL") and isinstance(
            cls._LOG_LEVEL, (str, int)
        ):
            return cls._LOG_LEVEL
        DEBUG_MODE = os.getenv("DEBUG_MODE", False)
        if DEBUG_MODE:
            cls._LOG_LEVEL = logging.DEBUG
        else:
            cls._LOG_LEVEL = logging.INFO

        return cls._LOG_LEVEL

    @classmethod
    def LOG_FORMAT(cls) -> logging.Formatter:
        """
        Return a configured :class:`logging.Formatter` for this manager.

        The formatter uses the manager's ``_IDENTIFIER`` to inject a
        service/package identifier into each formatted record. A
        :class:`AttributeError` is raised when ``_IDENTIFIER`` is not set
        correctly on the class.

        Returns
        -------
        logging.Formatter
            Formatter instance used by handlers managed by
            :class:`LoggerManager`.

        Raises
        ------
        AttributeError
            When ``_IDENTIFIER`` is not defined or is not a string.
        """
        if hasattr(cls, "_IDENTIFIER") and isinstance(
            getattr(cls, "_IDENTIFIER", None), str
        ):
            return ExpandedFormatter(cls._IDENTIFIER)
        raise AttributeError(
            f"{cls.__name__} has no attribute _IDENTIFIER or it is not a string"
        )

    @classmethod
    def LOG_DIRECTORY(cls) -> str:
        """
        Determine the directory used to store rotating log files.

        The method prefers an explicit ``_LOGS_PATH`` when provided. If
        absent it attempts to infer a package-local ``_logs`` directory by
        walking the call stack and locating the first ``__init__.py`` of
        the caller. If no suitable caller package can be found the method
        falls back to a top-level ``_logs`` directory adjacent to this
        module and emits a :class:`warnings.WarningMessage`.

        Returns
        -------
        str
            Absolute path to the directory where log files should be
            created. The directory itself may not exist yet.

        Notes
        -----
        The returned path will be used by the timed rotating file handler
        to write ``logs.log`` and the caller is responsible for ensuring
        appropriate filesystem permissions.
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
        Configure and attach handlers to a named logger.

        The method creates or reconfigures the logger named by
        ``logger_target`` and attaches handlers according to the provided
        flags. By default both a console handler and a timed rotating
        file handler (daily rotation) are added. The function also logs
        the chosen log level and log directory using the newly
        configured logger.

        Parameters
        ----------
        identifier : str
            Short identifier (service or package name) injected into log
            messages via the formatter.
        logger_target : str
            Logger name to configure (commonly ``__name__`` or
            ``__package__``).
        log_level : int | str, optional
            Explicit log level to use for the logger and handlers. If
            omitted the manager falls back to :meth:`LOG_LEVEL`.
        logger_files_path : str | os.PathLike, optional
            Base path where a subordinate ``_logs`` directory will be
            created to store rotating log files. When omitted the
            directory is inferred from the caller package.
        propagate : bool, optional
            Whether messages handled by this logger are passed to
            ancestor loggers. Defaults to ``True``.
        console_handler : bool, optional
            Add a console (stream) handler when ``True``. Default ``True``.
        rotating_file_handler : bool, optional
            Add a timed rotating file handler when ``True``. Default
            ``True``.
        handlers : Iterable[logging.Handler], optional
            Additional custom handlers to attach to the logger. Only
            objects that are instances of :class:`logging.Handler` will
            be considered.

        Returns
        -------
        None

        Examples
        --------
        Basic usage with default log directory::

            >>> from security_utils.logging import LoggerManager
            >>> LoggerManager.setup("MyService", __name__)

        Specify a custom log directory::

            >>> LoggerManager.setup("MyService", __name__, logger_files_path="/tmp/my_logs")

        Set a custom log level::

            >>> import logging
            >>> LoggerManager.setup("MyService", __name__, log_level=logging.WARNING)

        Use with ``__package__`` to group logs by package::

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
        Create a console (stream) handler configured with the manager's
        formatter and level.

        Returns
        -------
        logging.StreamHandler
            A stream handler ready to be attached to a :class:`logging.Logger`.
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

        The handler writes to ``<LOG_DIRECTORY()>/logs.log`` with a daily
        rotation schedule and keeps backups according to ``backupCount``.

        Returns
        -------
        logging.handlers.TimedRotatingFileHandler
            Configured file handler with daily rotation and backup files.
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
