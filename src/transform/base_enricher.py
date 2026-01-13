"""
Base Enricher Class

Abstract base class for all dataset enrichers.
"""

import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_logger
from utils.exceptions import DataFormatError


class BaseEnricher(ABC):
    """
    Abstract base class for dataset enrichers

    Each enricher focuses on improving specific aspects of FAIR compliance.
    """

    def __init__(self, dataset: xr.Dataset, logger=None):
        """
        Initialize enricher

        Parameters:
        -----------
        dataset : xarray.Dataset
            Dataset to enrich
        logger : logging.Logger, optional
            Logger instance
        """
        self.dataset = dataset
        self.logger = logger or get_logger(self.__class__.__name__)
        self.changes_made = []
        self.issues_found = []

    @abstractmethod
    def enrich(self) -> xr.Dataset:
        """
        Apply enrichments to the dataset

        Returns:
        --------
        xarray.Dataset: Enriched dataset
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """
        Validate that enrichments were successful

        Returns:
        --------
        bool: True if validation passed
        """
        pass

    def log_change(self, change_type: str, details: str):
        """
        Log a change made during enrichment

        Parameters:
        -----------
        change_type : str
            Type of change (e.g., 'attribute_added', 'variable_modified')
        details : str
            Description of the change
        """
        self.changes_made.append({
            'type': change_type,
            'details': details
        })
        self.logger.debug(f"[{change_type}] {details}")

    def log_issue(self, issue_type: str, details: str):
        """
        Log an issue found during enrichment

        Parameters:
        -----------
        issue_type : str
            Type of issue
        details : str
            Description of the issue
        """
        self.issues_found.append({
            'type': issue_type,
            'details': details
        })
        self.logger.warning(f"[{issue_type}] {details}")

    def get_summary(self) -> Dict:
        """
        Get summary of enrichment changes

        Returns:
        --------
        dict: Summary with changes and issues
        """
        return {
            'enricher': self.__class__.__name__,
            'changes_made': len(self.changes_made),
            'issues_found': len(self.issues_found),
            'changes': self.changes_made,
            'issues': self.issues_found
        }

    def safe_add_attribute(self, target, attr_name: str, attr_value,
                          overwrite: bool = False):
        """
        Safely add an attribute to dataset or variable

        Parameters:
        -----------
        target : xr.Dataset or xr.DataArray
            Target to add attribute to
        attr_name : str
            Attribute name
        attr_value : any
            Attribute value
        overwrite : bool
            Whether to overwrite existing attributes
        """
        if attr_name in target.attrs:
            if not overwrite:
                self.logger.debug(f"Attribute '{attr_name}' already exists, skipping")
                return
            else:
                self.log_change('attribute_updated',
                              f"Updated {attr_name} = {attr_value}")
        else:
            self.log_change('attribute_added',
                          f"Added {attr_name} = {attr_value}")

        target.attrs[attr_name] = attr_value


class EnrichmentError(Exception):
    """Raised when enrichment fails"""
    pass
