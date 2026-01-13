# Logging and Error Handling Guide

This guide explains how to use the logging infrastructure and error handling system in the OOI FAIR Pipeline.

## Quick Start

### Basic Setup

```python
from src.utils import setup_logging, get_logger

# Option 1: Set up a logger for your module
logger = setup_logging(name=__name__, level='INFO')

# Option 2: Get a logger (auto-configures if needed)
logger = get_logger(__name__)

# Use it
logger.info("Processing started")
logger.debug("Detailed diagnostic information")
logger.warning("Something unexpected happened")
logger.error("An error occurred")
```

### Using Custom Exceptions

```python
from src.utils.exceptions import (
    AuthenticationError,
    APIRequestError,
    DownloadError,
    retry_on_failure
)

# Raise structured exceptions
if not authenticated:
    raise AuthenticationError("Invalid credentials")

# Handle specific errors
try:
    download_file(url)
except DownloadError as e:
    logger.error(f"Download failed: {e}")
    logger.debug(f"URL: {e.url}")
```

## Logging Configuration

### Log Levels

- **DEBUG**: Detailed diagnostic information (file paths, API parameters, etc.)
- **INFO**: General informational messages (progress updates, status)
- **WARNING**: Unexpected events that don't prevent operation
- **ERROR**: Errors that caused an operation to fail
- **CRITICAL**: Severe errors that may cause system failure

### Setup Options

```python
logger = setup_logging(
    name='my_module',           # Logger name (use __name__)
    level=logging.INFO,          # Minimum log level
    log_dir='logs',              # Directory for log files
    console_output=True,         # Print to console
    file_output=True,            # Write to file
    max_bytes=10*1024*1024,      # 10MB per log file
    backup_count=5               # Keep 5 backup files
)
```

### Output Formats

**Console** (colored):
```
08:25:14 | INFO | Processing started
08:25:15 | ERROR | Download failed
```

**File** (detailed):
```
2024-01-13 08:25:14 | src.extract.ooi_api | INFO | Processing started
2024-01-13 08:25:15 | src.extract.ooi_api | ERROR | Download failed
```

### Log Files

- Location: `logs/ooi_pipeline_YYYYMMDD.log`
- Rotation: Automatic when file reaches max_bytes
- Retention: Keeps backup_count old files
- Format: UTF-8 text

## Exception Hierarchy

```
OOIPipelineError (base)
├── AuthenticationError         # API credentials invalid
├── ConfigurationError          # Missing/invalid config
├── APIRequestError             # API request failed
│   ├── status_code            # HTTP status code
│   └── response_text          # Response body
├── DataRequestError           # Data request failed
├── DataNotReadyError          # Data not ready after timeout
│   ├── status_url            # Where to check status
│   └── elapsed_time          # Time waited
├── CatalogParseError          # THREDDS catalog parsing failed
├── DownloadError              # File download failed
│   ├── url                   # Download URL
│   └── status_code           # HTTP status
├── FileValidationError        # File validation failed
├── DataFormatError            # Unexpected data format
├── MetadataError              # Missing/invalid metadata
├── FAIRAssessmentError        # FAIR assessment failed
└── ComplianceCheckError       # Compliance check failed
```

## Common Patterns

### Pattern 1: Module Logger

```python
# At top of module
from src.utils import get_logger
logger = get_logger(__name__)

def my_function():
    logger.info("Starting function")
    try:
        # Do work
        logger.debug("Intermediate step complete")
    except Exception as e:
        logger.error(f"Function failed: {e}")
        raise
```

### Pattern 2: Exception Handling

```python
from src.utils.exceptions import APIRequestError, log_exception

try:
    response = requests.get(url)
    if response.status_code != 200:
        raise APIRequestError(
            "Request failed",
            status_code=response.status_code
        )
except requests.RequestException as e:
    log_exception(logger, e, "Network error")
    raise APIRequestError(f"Network error: {e}")
```

### Pattern 3: Retry on Transient Failures

```python
from src.utils.exceptions import retry_on_failure

@retry_on_failure(max_attempts=3, delay=2, exceptions=(requests.RequestException,))
def fetch_data():
    response = requests.get(url)
    return response.json()
```

### Pattern 4: Context-Rich Logging

```python
request_id = "REQ-2024-001"
logger.info(f"[{request_id}] Processing request")
logger.debug(f"[{request_id}] Parameters: {params}")

try:
    result = process()
    logger.info(f"[{request_id}] Complete")
except Exception as e:
    logger.error(f"[{request_id}] Failed: {e}")
```

### Pattern 5: Progress Logging

```python
total = len(items)
for i, item in enumerate(items, 1):
    logger.info(f"Processing {i}/{total}: {item.name}")
    logger.debug(f"  - Step 1: validate")
    logger.debug(f"  - Step 2: transform")
    logger.info(f"  - Complete")
```

## Best Practices

### DO

✅ Use appropriate log levels
✅ Include context in log messages (request IDs, file names, etc.)
✅ Log at decision points and state changes
✅ Use structured exceptions with context
✅ Log before and after major operations
✅ Include relevant details in DEBUG logs

### DON'T

❌ Log sensitive data (passwords, tokens, PII)
❌ Use print() statements in production code
❌ Log inside tight loops (use sampling)
❌ Raise generic Exception - use specific types
❌ Swallow exceptions without logging
❌ Mix logging and print statements

## Examples

### Example 1: Data Extraction

```python
from src.utils import get_logger
from src.utils.exceptions import APIRequestError, DownloadError

logger = get_logger(__name__)

def extract_data(instrument_id):
    logger.info(f"Starting extraction for {instrument_id}")

    try:
        # Request data
        logger.debug(f"Building API request for {instrument_id}")
        result = api.request_data(instrument_id)
        logger.info("Data request accepted")

        # Wait for processing
        logger.info("Waiting for data preparation")
        urls = api.wait_for_data(result['status_url'])
        logger.info(f"Found {len(urls)} file(s)")

        # Download
        for i, url in enumerate(urls, 1):
            logger.info(f"Downloading file {i}/{len(urls)}")
            api.download_file(url, output_path)

        logger.info("Extraction complete")

    except APIRequestError as e:
        logger.error(f"API request failed: {e}")
        raise
    except DownloadError as e:
        logger.error(f"Download failed: {e}")
        logger.debug(f"Failed URL: {e.url}")
        raise
```

### Example 2: Batch Processing

```python
from src.utils import get_logger

logger = get_logger(__name__)

def process_batch(items):
    logger.info(f"Processing batch of {len(items)} items")

    results = {'success': 0, 'failed': 0}

    for i, item in enumerate(items, 1):
        try:
            logger.debug(f"[{i}/{len(items)}] Processing {item.id}")
            process_item(item)
            results['success'] += 1

        except Exception as e:
            logger.warning(f"[{i}/{len(items)}] Failed: {e}")
            results['failed'] += 1
            continue

    logger.info(f"Batch complete: {results['success']} succeeded, "
                f"{results['failed']} failed")
    return results
```

## Testing

Run the logging demonstration:

```bash
python3 examples/logging_demo.py
```

This demonstrates:
- Basic logging levels
- Module-specific loggers
- Exception handling
- Retry decorator
- Structured logging
- File logging with rotation
- Context-rich logging

## Troubleshooting

### No log output?

Check that handlers are configured:
```python
logger = get_logger(__name__)
print(f"Handlers: {logger.handlers}")  # Should show handlers
```

### Log files not created?

- Check permissions on `logs/` directory
- Verify `file_output=True` in setup
- Check disk space

### Colors not showing?

Colors only work in terminals that support ANSI codes. Log files don't have colors.

### Too much output?

Increase the log level:
```python
logger.setLevel(logging.WARNING)  # Only WARNING and above
```

## Integration with OOI Extractor

The [ooi_api.py](../src/extract/ooi_api.py) module demonstrates full integration:

- Module logger at top
- Custom exceptions throughout
- Retry decorator on network calls
- Context-rich logging for debugging
- Proper error propagation

Study this file for real-world usage patterns.

## Next Steps

1. Add logging to new modules as you build Sprint 2
2. Use custom exceptions for domain-specific errors
3. Monitor log files for issues
4. Adjust log levels as needed (DEBUG during dev, INFO in production)

---

For implementation details, see:
- [src/utils/logging_config.py](../src/utils/logging_config.py) - Logging setup
- [src/utils/exceptions.py](../src/utils/exceptions.py) - Custom exceptions
- [examples/logging_demo.py](../examples/logging_demo.py) - Examples
