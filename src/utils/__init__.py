"""
Utility modules for OOI FAIR Pipeline
"""

from .logging_config import setup_logging, get_logger
from .exceptions import (
    OOIPipelineError,
    AuthenticationError,
    ConfigurationError,
    APIRequestError,
    DataRequestError,
    DataNotReadyError,
    CatalogParseError,
    DownloadError,
    FileValidationError,
    DataFormatError,
    MetadataError,
    FAIRAssessmentError,
    ComplianceCheckError,
    retry_on_failure
)

__all__ = [
    'setup_logging',
    'get_logger',
    'OOIPipelineError',
    'AuthenticationError',
    'ConfigurationError',
    'APIRequestError',
    'DataRequestError',
    'DataNotReadyError',
    'CatalogParseError',
    'DownloadError',
    'FileValidationError',
    'DataFormatError',
    'MetadataError',
    'FAIRAssessmentError',
    'ComplianceCheckError',
    'retry_on_failure',
]
