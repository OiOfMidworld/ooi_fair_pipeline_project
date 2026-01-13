"""
Centralized logging configuration for OOI FAIR Pipeline

This module provides consistent logging across all pipeline components with:
- Configurable log levels
- File and console output
- Structured log formatting
- Automatic log rotation
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """Custom formatter with color coding for console output"""

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }

    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}"
                f"{self.COLORS['RESET']}"
            )
        return super().format(record)


def setup_logging(
    name=None,
    level=logging.INFO,
    log_dir='logs',
    console_output=True,
    file_output=True,
    max_bytes=10*1024*1024,  # 10MB
    backup_count=5
):
    """
    Set up logging configuration for the application

    Parameters:
    -----------
    name : str, optional
        Logger name (None = root logger)
    level : int
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_dir : str
        Directory for log files
    console_output : bool
        Whether to output logs to console
    file_output : bool
        Whether to output logs to file
    max_bytes : int
        Maximum size of each log file before rotation
    backup_count : int
        Number of backup log files to keep

    Returns:
    --------
    logging.Logger
        Configured logger instance
    """

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    console_formatter = ColoredFormatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%H:%M:%S'
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if file_output:
        # Create logs directory
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)

        # Create log filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d')
        log_file = log_path / f'ooi_pipeline_{timestamp}.log'

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.info(f"Logging to file: {log_file}")

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name):
    """
    Get a logger with the specified name

    If the logger doesn't exist, it will be created with default settings.

    Parameters:
    -----------
    name : str
        Logger name (usually __name__ of the module)

    Returns:
    --------
    logging.Logger
        Logger instance
    """
    logger = logging.getLogger(name)

    # If logger has no handlers, set it up with defaults
    if not logger.handlers:
        return setup_logging(name=name)

    return logger


# Convenience function for common log patterns
def log_api_request(logger, url, params=None):
    """Log an API request with consistent formatting"""
    logger.info(f"API Request: {url}")
    if params:
        logger.debug(f"Parameters: {params}")


def log_api_response(logger, status_code, url):
    """Log an API response with consistent formatting"""
    if status_code == 200:
        logger.info(f"API Response: {status_code} - Success")
    else:
        logger.warning(f"API Response: {status_code} - {url}")


def log_download_progress(logger, filename, current, total):
    """Log download progress"""
    if total > 0:
        percent = (current / total) * 100
        logger.info(f"Downloading {filename}: {percent:.1f}% ({current}/{total} bytes)")
    else:
        logger.info(f"Downloading {filename}: {current} bytes")


def log_exception(logger, exception, context=None):
    """Log an exception with context"""
    if context:
        logger.error(f"{context}: {type(exception).__name__}: {str(exception)}")
    else:
        logger.error(f"{type(exception).__name__}: {str(exception)}")
    logger.debug("Exception details:", exc_info=True)
