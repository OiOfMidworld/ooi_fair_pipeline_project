"""
Demonstration of logging infrastructure for OOI FAIR Pipeline

This script shows how to use the logging system and error handling
across different scenarios.
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from utils import setup_logging, get_logger
from utils.exceptions import (
    AuthenticationError,
    APIRequestError,
    DownloadError,
    retry_on_failure
)


def demo_basic_logging():
    """Demo 1: Basic logging at different levels"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Logging Levels")
    print("="*60 + "\n")

    logger = setup_logging(name='demo.basic', level=logging.DEBUG)

    logger.debug("This is a DEBUG message - detailed diagnostic info")
    logger.info("This is an INFO message - general information")
    logger.warning("This is a WARNING message - something unexpected")
    logger.error("This is an ERROR message - something failed")
    logger.critical("This is a CRITICAL message - serious problem")


def demo_module_logger():
    """Demo 2: Using module-specific loggers"""
    print("\n" + "="*60)
    print("DEMO 2: Module-Specific Loggers")
    print("="*60 + "\n")

    # Simulate different modules
    extractor_logger = get_logger('ooi_pipeline.extract')
    transform_logger = get_logger('ooi_pipeline.transform')
    assess_logger = get_logger('ooi_pipeline.assess')

    extractor_logger.info("Extracting data from OOI API...")
    transform_logger.info("Transforming data to FAIR format...")
    assess_logger.info("Running FAIR assessment...")


def demo_exception_handling():
    """Demo 3: Custom exception handling with logging"""
    print("\n" + "="*60)
    print("DEMO 3: Exception Handling")
    print("="*60 + "\n")

    logger = get_logger('demo.exceptions')

    # Example 1: Authentication error
    try:
        logger.info("Attempting to authenticate...")
        raise AuthenticationError("Invalid API credentials")
    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")

    # Example 2: API request error with status code
    try:
        logger.info("Making API request...")
        raise APIRequestError("Request failed", status_code=404)
    except APIRequestError as e:
        logger.error(f"API request failed: {e}")

    # Example 3: Download error with URL
    try:
        logger.info("Downloading file...")
        raise DownloadError(
            "Connection timeout",
            url="https://example.com/data.nc",
            status_code=503
        )
    except DownloadError as e:
        logger.error(f"Download failed: {e}")
        logger.debug(f"Failed URL: {e.url}")


def demo_retry_decorator():
    """Demo 4: Retry decorator for transient failures"""
    print("\n" + "="*60)
    print("DEMO 4: Retry Decorator")
    print("="*60 + "\n")

    logger = get_logger('demo.retry')

    attempt_count = {'value': 0}

    @retry_on_failure(max_attempts=3, delay=1, exceptions=(ValueError,))
    def flaky_function():
        """Simulates a function that fails twice then succeeds"""
        attempt_count['value'] += 1
        logger.info(f"Attempt {attempt_count['value']}")

        if attempt_count['value'] < 3:
            logger.warning("Simulated transient failure")
            raise ValueError("Temporary error")

        logger.info("Success!")
        return "Data retrieved"

    try:
        result = flaky_function()
        logger.info(f"Final result: {result}")
    except ValueError as e:
        logger.error(f"Failed after all retries: {e}")


def demo_structured_logging():
    """Demo 5: Structured logging for complex operations"""
    print("\n" + "="*60)
    print("DEMO 5: Structured Logging for Operations")
    print("="*60 + "\n")

    logger = get_logger('demo.structured')

    # Simulate a data extraction workflow
    logger.info("Starting data extraction workflow")

    instruments = ['CTD', 'DO', 'pH']
    for i, instrument in enumerate(instruments, 1):
        logger.info(f"Processing instrument {i}/{len(instruments)}: {instrument}")
        logger.debug(f"  - Requesting data for {instrument}")
        logger.debug(f"  - Parsing response")
        logger.debug(f"  - Validating data")
        logger.info(f"  - {instrument} complete")

    logger.info("Workflow complete - processed 3 instruments")


def demo_file_logging():
    """Demo 6: Logging to file with rotation"""
    print("\n" + "="*60)
    print("DEMO 6: File Logging with Rotation")
    print("="*60 + "\n")

    # Set up logger that writes to both console and file
    logger = setup_logging(
        name='demo.file',
        level=logging.INFO,
        log_dir='logs',
        console_output=True,
        file_output=True,
        max_bytes=5*1024*1024,  # 5MB per file
        backup_count=3  # Keep 3 backup files
    )

    logger.info("This message goes to both console and file")
    logger.info("Check the 'logs/' directory for log files")
    logger.debug("Debug messages are only in the log file if level=DEBUG")

    # Show where logs are stored
    import os
    log_dir = Path('logs')
    if log_dir.exists():
        log_files = list(log_dir.glob('*.log*'))
        if log_files:
            logger.info(f"Found {len(log_files)} log file(s):")
            for log_file in log_files:
                size = os.path.getsize(log_file)
                logger.info(f"  - {log_file.name} ({size} bytes)")


def demo_context_logging():
    """Demo 7: Logging with contextual information"""
    print("\n" + "="*60)
    print("DEMO 7: Context-Rich Logging")
    print("="*60 + "\n")

    logger = get_logger('demo.context')

    # Simulate processing a data request
    request_id = "REQ-2024-001"
    instrument = "CE02SHSM-CTD"
    date_range = "2024-01-01 to 2024-01-31"

    logger.info(f"Processing request: {request_id}")
    logger.info(f"  Instrument: {instrument}")
    logger.info(f"  Date range: {date_range}")

    try:
        # Simulate some processing
        logger.debug(f"[{request_id}] Validating parameters")
        logger.debug(f"[{request_id}] Building API query")
        logger.info(f"[{request_id}] Sending request to OOI API")

        # Simulate an error
        raise APIRequestError("Network timeout", status_code=504)

    except APIRequestError as e:
        logger.error(f"[{request_id}] Request failed: {e}")
        logger.info(f"[{request_id}] Will retry in next batch")


def main():
    """Run all logging demonstrations"""
    print("\n" + "="*70)
    print("  OOI FAIR PIPELINE - LOGGING & ERROR HANDLING DEMONSTRATION")
    print("="*70)

    demo_basic_logging()
    demo_module_logger()
    demo_exception_handling()
    demo_retry_decorator()
    demo_structured_logging()
    demo_file_logging()
    demo_context_logging()

    print("\n" + "="*70)
    print("  DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nKey Takeaways:")
    print("  1. Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)")
    print("  2. Module-specific loggers help trace issues")
    print("  3. Custom exceptions provide structured error handling")
    print("  4. Retry decorator handles transient failures gracefully")
    print("  5. Logs are written to both console (colored) and files (rotated)")
    print("  6. Context-rich logging makes debugging easier")
    print("\nFor more info, see:")
    print("  - src/utils/logging_config.py - Logging setup")
    print("  - src/utils/exceptions.py - Custom exceptions")
    print("  - src/extract/ooi_api.py - Real-world usage example")
    print()


if __name__ == "__main__":
    main()
