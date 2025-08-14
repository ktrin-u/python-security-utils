import logging
import logging.handlers
import os

# Config
ENVIRONMENT = os.getenv("ENVIRONMENT", "prod")
LOG_LEVEL = logging.DEBUG if ENVIRONMENT not in ["prod", "production"] else logging.INFO
LOG_FORMAT = logging.Formatter(
    "[%(asctime)s][Security Utils][%(levelname)s][%(name)s]: %(message)s"
)
LOGS_DIR = os.path.join(os.path.dirname(__file__), "_logs")

# Get logger
logger = logging.getLogger("security_utils")
logger.setLevel(LOG_LEVEL)
logger.propagate = True


# Add handlers if not already added
if not logger.hasHandlers():
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

logger.info(f"LOGGER_LEVEL: {logging.getLevelName(logger.level)}")