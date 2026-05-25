"""
Logging Configuration
=====================
Sets up dual logging: DEBUG-level to file, INFO-level to console.
Log files are stored in the `logs/` directory with timestamped filenames.
"""

import logging
import os
from datetime import datetime


def setup_logging(log_dir: str = "logs", log_level: str = "DEBUG") -> logging.Logger:
    """
    Configure and return the application logger.
    
    Creates a logger with two handlers:
    - FileHandler: Logs DEBUG and above to a timestamped log file
    - StreamHandler: Logs INFO and above to console (user-facing output)
    
    Args:
        log_dir: Directory to store log files (created if missing).
        log_level: Minimum log level for file handler.
    
    Returns:
        Configured logger instance.
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)

    # Create timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"trading_bot_{timestamp}.log")

    # Create root logger for the bot package
    logger = logging.getLogger("trading_bot")
    logger.setLevel(getattr(logging, log_level.upper(), logging.DEBUG))

    # Prevent duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    # --- File Handler (detailed, DEBUG level) ---
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s.%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # --- Console Handler (errors/warnings only, user output handled by Click) ---
    console_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.CRITICAL)
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized → {log_file}")
    return logger
