"""
Custom exception classes for OOI FAIR Pipeline

These exceptions provide structured error handling and make it easier
to distinguish between different types of failures in the pipeline.
"""


class OOIPipelineError(Exception):
    """Base exception for all OOI pipeline errors"""
    pass


# Authentication & Configuration Errors
class AuthenticationError(OOIPipelineError):
    """Raised when API authentication fails"""
    pass


class ConfigurationError(OOIPipelineError):
    """Raised when configuration is missing or invalid"""
    pass


# API & Network Errors
class APIRequestError(OOIPipelineError):
    """Raised when an API request fails"""

    def __init__(self, message, status_code=None, response_text=None):
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(message)

    def __str__(self):
        base_msg = super().__str__()
        if self.status_code:
            return f"{base_msg} (Status: {self.status_code})"
        return base_msg


class DataRequestError(OOIPipelineError):
    """Raised when a data request to OOI fails"""
    pass


class DataNotReadyError(OOIPipelineError):
    """Raised when data is not ready after timeout"""

    def __init__(self, message, status_url=None, elapsed_time=None):
        self.status_url = status_url
        self.elapsed_time = elapsed_time
        super().__init__(message)


class CatalogParseError(OOIPipelineError):
    """Raised when THREDDS catalog parsing fails"""
    pass


# Download & File Errors
class DownloadError(OOIPipelineError):
    """Raised when file download fails"""

    def __init__(self, message, url=None, status_code=None):
        self.url = url
        self.status_code = status_code
        super().__init__(message)


class FileValidationError(OOIPipelineError):
    """Raised when a downloaded file fails validation"""
    pass


# Data Processing Errors
class DataFormatError(OOIPipelineError):
    """Raised when data format is unexpected or invalid"""
    pass


class MetadataError(OOIPipelineError):
    """Raised when metadata is missing or invalid"""
    pass


# FAIR Assessment Errors
class FAIRAssessmentError(OOIPipelineError):
    """Raised when FAIR assessment fails"""
    pass


class ComplianceCheckError(OOIPipelineError):
    """Raised when compliance checking fails"""
    pass


# Retry decorator for transient failures
def retry_on_failure(max_attempts=3, delay=1, exceptions=(Exception,)):
    """
    Decorator to retry a function on specific exceptions

    Parameters:
    -----------
    max_attempts : int
        Maximum number of attempts
    delay : float
        Delay in seconds between attempts
    exceptions : tuple
        Tuple of exception types to catch and retry

    Example:
    --------
    @retry_on_failure(max_attempts=3, delay=2, exceptions=(requests.RequestException,))
    def fetch_data():
        return requests.get(url)
    """
    import time
    import functools

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(delay)
                        continue
                    else:
                        raise

            # This should never be reached, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator
