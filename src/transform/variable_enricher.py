"""
Variable Metadata Enricher

Adds units, standard_name, and other CF-compliant attributes to variables.
"""

import sys
from pathlib import Path
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent.parent))

from transform.base_enricher import BaseEnricher
from transform.enrichment_strategy import (
    get_variable_standard_name,
    get_variable_units,
    CF_STANDARD_NAMES
)
from utils import get_logger

logger = get_logger(__name__)


class VariableEnricher(BaseEnricher):
    """
    Add CF-compliant metadata to variables

    - Adds units attributes
    - Adds standard_name attributes
    - Adds long_name attributes
    - Improves existing metadata
    """

    def enrich(self) -> xr.Dataset:
        """
        Add missing variable metadata

        Returns:
        --------
        xarray.Dataset: Dataset with enriched variables
        """
        self.logger.info("Enriching variable metadata")

        ds = self.dataset.copy(deep=True)

        # Process each data variable
        for var_name in ds.data_vars:
            ds = self._enrich_variable(ds, var_name)

        self.dataset = ds
        return ds

    def _enrich_variable(self, ds: xr.Dataset, var_name: str) -> xr.Dataset:
        """Enrich a single variable's metadata"""

        var = ds[var_name]

        # Skip QC variables (they have special handling)
        if self._is_qc_variable(var_name):
            return ds

        # Skip timestamp variables (they already have units from xarray encoding)
        if self._is_timestamp_variable(var_name):
            return ds

        # Add standard_name if missing
        if 'standard_name' not in var.attrs:
            standard_name = get_variable_standard_name(var_name)
            if standard_name:
                var.attrs['standard_name'] = standard_name
                self.log_change('attribute_added',
                              f"{var_name}: standard_name = {standard_name}")
            else:
                self.log_issue('no_standard_name',
                             f"Could not determine standard_name for {var_name}")

        # Add units if missing
        if 'units' not in var.attrs:
            # Try to get units from standard_name
            standard_name = var.attrs.get('standard_name')
            units = get_variable_units(standard_name, var_name)

            if units:
                var.attrs['units'] = units
                self.log_change('attribute_added',
                              f"{var_name}: units = {units}")
            else:
                # Default to dimensionless
                var.attrs['units'] = '1'
                self.log_change('attribute_added',
                              f"{var_name}: units = 1 (dimensionless)")
                self.log_issue('unknown_units',
                             f"Unknown units for {var_name}, set to dimensionless")

        # Add long_name if missing
        if 'long_name' not in var.attrs:
            long_name = self._generate_long_name(var_name)
            var.attrs['long_name'] = long_name
            self.log_change('attribute_added',
                          f"{var_name}: long_name = {long_name}")

        # Add valid_min/valid_max if data available and not present
        if var.size > 0:
            if 'valid_min' not in var.attrs:
                try:
                    valid_min = float(var.min().values)
                    var.attrs['valid_min'] = valid_min
                    self.log_change('attribute_added',
                                  f"{var_name}: valid_min = {valid_min:.3f}")
                except:
                    pass

            if 'valid_max' not in var.attrs:
                try:
                    valid_max = float(var.max().values)
                    var.attrs['valid_max'] = valid_max
                    self.log_change('attribute_added',
                                  f"{var_name}: valid_max = {valid_max:.3f}")
                except:
                    pass

        return ds

    def _is_qc_variable(self, var_name: str) -> bool:
        """Check if variable is a QC flag variable"""
        qc_indicators = ['qc', 'qartod', 'flag', 'quality']
        name_lower = var_name.lower()
        return any(indicator in name_lower for indicator in qc_indicators)

    def _is_timestamp_variable(self, var_name: str) -> bool:
        """Check if variable is a timestamp variable"""
        timestamp_indicators = ['timestamp', '_time', 'time_']
        name_lower = var_name.lower()
        return any(indicator in name_lower for indicator in timestamp_indicators)

    def _generate_long_name(self, var_name: str) -> str:
        """
        Generate a human-readable long_name from variable name

        Parameters:
        -----------
        var_name : str
            Variable name

        Returns:
        --------
        str: Generated long name
        """
        # Replace underscores with spaces
        long_name = var_name.replace('_', ' ')

        # Capitalize words
        long_name = ' '.join(word.capitalize() for word in long_name.split())

        # Handle common abbreviations
        replacements = {
            'Ctd': 'CTD',
            'Qc': 'QC',
            'Ph': 'pH',
            'Do': 'DO',
            'Dcl': 'DCL',
            'Temp': 'Temperature',
            'Sal': 'Salinity',
            'Pres': 'Pressure',
            'Cond': 'Conductivity'
        }

        for old, new in replacements.items():
            long_name = long_name.replace(old, new)

        return long_name

    def validate(self) -> bool:
        """
        Validate that variables have required attributes

        Returns:
        --------
        bool: True if validation passed
        """
        ds = self.dataset
        missing_attrs = []

        for var_name in ds.data_vars:
            var = ds[var_name]

            # Skip QC variables
            if self._is_qc_variable(var_name):
                continue

            # Check required attributes
            if 'units' not in var.attrs:
                missing_attrs.append(f"{var_name}: missing units")

            if 'long_name' not in var.attrs:
                missing_attrs.append(f"{var_name}: missing long_name")

        if missing_attrs:
            self.logger.error(f"Validation failed: {len(missing_attrs)} issues")
            for issue in missing_attrs[:5]:  # Show first 5
                self.logger.error(f"  - {issue}")
            return False

        self.logger.info("Variable validation passed")
        return True
