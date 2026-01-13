"""
Global Metadata Enricher

Adds and improves global attributes for better FAIR compliance.
"""

import sys
from pathlib import Path
from datetime import datetime
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent.parent))

from transform.base_enricher import BaseEnricher
from transform.enrichment_strategy import OOI_METADATA_DEFAULTS
from utils import get_logger

logger = get_logger(__name__)


class MetadataEnricher(BaseEnricher):
    """
    Enhance global metadata attributes

    - Adds missing ACDD-required attributes
    - Adds OOI-specific metadata
    - Improves existing metadata quality
    """

    def enrich(self) -> xr.Dataset:
        """
        Add missing global metadata

        Returns:
        --------
        xarray.Dataset: Dataset with enriched metadata
        """
        self.logger.info("Enriching global metadata")

        ds = self.dataset.copy(deep=True)

        # Add OOI defaults
        ds = self._add_ooi_defaults(ds)

        # Enhance existing attributes
        ds = self._enhance_conventions(ds)
        ds = self._add_timestamps(ds)
        ds = self._add_qc_documentation(ds)

        # Add DOI if missing (generate placeholder)
        ds = self._add_identifier(ds)

        self.dataset = ds
        return ds

    def _add_ooi_defaults(self, ds: xr.Dataset) -> xr.Dataset:
        """Add OOI-specific default metadata"""

        for attr_name, attr_value in OOI_METADATA_DEFAULTS.items():
            if attr_name not in ds.attrs:
                ds.attrs[attr_name] = attr_value
                self.log_change('attribute_added',
                              f"Added {attr_name} = {attr_value}")

        return ds

    def _enhance_conventions(self, ds: xr.Dataset) -> xr.Dataset:
        """Ensure Conventions attribute lists CF and ACDD"""

        if 'Conventions' in ds.attrs:
            conventions = ds.attrs['Conventions']

            # Ensure CF is mentioned
            if 'CF' not in conventions:
                if conventions:
                    ds.attrs['Conventions'] = f"CF-1.6, {conventions}"
                else:
                    ds.attrs['Conventions'] = 'CF-1.6, ACDD-1.3'
                self.log_change('attribute_updated',
                              f"Updated Conventions to include CF")
        else:
            ds.attrs['Conventions'] = 'CF-1.6, ACDD-1.3'
            self.log_change('attribute_added',
                          "Added Conventions = CF-1.6, ACDD-1.3")

        return ds

    def _add_timestamps(self, ds: xr.Dataset) -> xr.Dataset:
        """Add date_created and date_modified if missing"""

        current_time = datetime.utcnow().isoformat() + 'Z'

        if 'date_created' not in ds.attrs:
            # Try to extract from existing time coverage
            if 'time_coverage_start' in ds.attrs:
                ds.attrs['date_created'] = ds.attrs['time_coverage_start']
            else:
                ds.attrs['date_created'] = current_time
            self.log_change('attribute_added', f"Added date_created")

        # Always update date_modified to reflect enrichment
        ds.attrs['date_modified'] = current_time
        ds.attrs['history'] = (
            f"{current_time}: Enriched by OOI FAIR Pipeline; " +
            ds.attrs.get('history', '')
        )
        self.log_change('attribute_updated', "Updated date_modified and history")

        return ds

    def _add_qc_documentation(self, ds: xr.Dataset) -> xr.Dataset:
        """Add QC methodology documentation"""

        if 'quality_control_methodology' not in ds.attrs:
            # Check if QC variables exist
            qc_vars = [v for v in ds.data_vars
                      if any(x in str(v).lower() for x in ['qc', 'qartod'])]

            if qc_vars:
                methodology = (
                    "Data quality controlled using OOI quality control procedures. "
                    "QARTOD flags indicate data quality: "
                    "1=Good, 2=Unknown, 3=Suspect, 4=Bad. "
                    "QC results indicate compliance with specific test criteria."
                )
                ds.attrs['quality_control_methodology'] = methodology
                self.log_change('attribute_added',
                              "Added quality_control_methodology")

        return ds

    def _add_identifier(self, ds: xr.Dataset) -> xr.Dataset:
        """Add unique identifier if missing"""

        # Check for existing identifier
        id_attrs = ['id', 'uuid', 'doi', 'identifier']
        has_id = any(attr in ds.attrs for attr in id_attrs)

        if not has_id:
            # Generate a simple ID from attributes
            if 'id' in ds.attrs:
                return ds

            # Try to build from existing metadata
            parts = []

            if 'node' in ds.attrs:
                parts.append(ds.attrs['node'])
            if 'sensor' in ds.attrs:
                parts.append(ds.attrs['sensor'])
            if 'method' in ds.attrs:
                parts.append(ds.attrs['method'])
            if 'stream' in ds.attrs:
                parts.append(ds.attrs['stream'])

            if parts:
                identifier = '-'.join(parts)
                ds.attrs['id'] = identifier
                self.log_change('attribute_added',
                              f"Added id = {identifier}")
            else:
                # Fallback: use timestamp
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                ds.attrs['id'] = f"ooi-dataset-{timestamp}"
                self.log_change('attribute_added',
                              f"Added id (timestamp-based)")

        return ds

    def validate(self) -> bool:
        """
        Validate that required metadata is present

        Returns:
        --------
        bool: True if validation passed
        """
        ds = self.dataset

        # Check for critical ACDD attributes
        required = ['title', 'summary', 'Conventions', 'institution']
        missing = [attr for attr in required if attr not in ds.attrs]

        if missing:
            self.logger.error(f"Validation failed: missing {missing}")
            return False

        self.logger.info("Metadata validation passed")
        return True
