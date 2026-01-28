"""
Geospatial Metadata Extractor

Extracts geospatial and temporal bounds from data arrays and adds
appropriate global metadata attributes for discovery.

Designed for Argo data where lat/lon/time are data variables rather
than in global attributes.

Sprint: 4B - BGC-Argo mCDR/MRV Extension
"""

import sys
from pathlib import Path
import xarray as xr
import numpy as np
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from transform.base_enricher import BaseEnricher
from utils import get_logger

logger = get_logger(__name__)


class GeospatialExtractor(BaseEnricher):
    """
    Extract and add geospatial/temporal metadata

    Reads lat/lon/time from data variables and creates
    ACDD-compliant global attributes for discovery.
    """

    def enrich(self) -> xr.Dataset:
        """
        Extract geospatial and temporal bounds

        Returns:
        --------
        xr.Dataset: Dataset with geospatial metadata
        """
        self.logger.info("Extracting geospatial and temporal metadata")

        ds = self.dataset.copy(deep=True)

        # Extract latitude bounds
        ds = self._extract_latitude_bounds(ds)

        # Extract longitude bounds
        ds = self._extract_longitude_bounds(ds)

        # Extract time coverage
        ds = self._extract_time_coverage(ds)

        # Add geospatial resolution
        ds = self._add_geospatial_resolution(ds)

        self.dataset = ds
        return ds

    def _find_latitude_variable(self, ds: xr.Dataset) -> str:
        """Find latitude variable name"""

        candidates = ['LATITUDE', 'latitude', 'lat', 'Latitude']

        for var in candidates:
            if var in ds.variables:
                return var

        self.log_issue('no_latitude',
                      "Could not find latitude variable")
        return None

    def _find_longitude_variable(self, ds: xr.Dataset) -> str:
        """Find longitude variable name"""

        candidates = ['LONGITUDE', 'longitude', 'lon', 'Longitude']

        for var in candidates:
            if var in ds.variables:
                return var

        self.log_issue('no_longitude',
                      "Could not find longitude variable")
        return None

    def _find_time_variable(self, ds: xr.Dataset) -> str:
        """Find time variable name"""

        candidates = ['JULD', 'time', 'TIME', 'Time']

        for var in candidates:
            if var in ds.variables:
                return var

        # Check for reference_date_time
        if 'REFERENCE_DATE_TIME' in ds.variables:
            return 'REFERENCE_DATE_TIME'

        self.log_issue('no_time',
                      "Could not find time variable")
        return None

    def _extract_latitude_bounds(self, ds: xr.Dataset) -> xr.Dataset:
        """Extract and add latitude bounds"""

        lat_var = self._find_latitude_variable(ds)

        if not lat_var:
            return ds

        try:
            lat_data = ds[lat_var].values

            # Handle multi-dimensional arrays (flatten)
            lat_data = lat_data.flatten()

            # Remove NaN values
            lat_data = lat_data[~np.isnan(lat_data)]

            if len(lat_data) == 0:
                self.log_issue('no_valid_latitude',
                              "No valid latitude values found")
                return ds

            lat_min = float(np.min(lat_data))
            lat_max = float(np.max(lat_data))

            # Add global attributes
            if 'geospatial_lat_min' not in ds.attrs:
                ds.attrs['geospatial_lat_min'] = lat_min
                self.log_change('attribute_added',
                              f"Added geospatial_lat_min: {lat_min:.5f}")

            if 'geospatial_lat_max' not in ds.attrs:
                ds.attrs['geospatial_lat_max'] = lat_max
                self.log_change('attribute_added',
                              f"Added geospatial_lat_max: {lat_max:.5f}")

            if 'geospatial_lat_units' not in ds.attrs:
                ds.attrs['geospatial_lat_units'] = 'degrees_north'
                self.log_change('attribute_added',
                              'Added geospatial_lat_units: degrees_north')

            # Add bounds as single value if float is stationary
            if abs(lat_max - lat_min) < 0.01:  # Less than ~1 km difference
                if 'geospatial_lat' not in ds.attrs:
                    ds.attrs['geospatial_lat'] = float(np.mean(lat_data))
                    self.log_change('attribute_added',
                                  f"Added geospatial_lat: {np.mean(lat_data):.5f} "
                                  "(stationary float)")

        except Exception as e:
            self.log_issue('latitude_extraction_error',
                          f"Error extracting latitude bounds: {e}")

        return ds

    def _extract_longitude_bounds(self, ds: xr.Dataset) -> xr.Dataset:
        """Extract and add longitude bounds"""

        lon_var = self._find_longitude_variable(ds)

        if not lon_var:
            return ds

        try:
            lon_data = ds[lon_var].values

            # Handle multi-dimensional arrays
            lon_data = lon_data.flatten()

            # Remove NaN values
            lon_data = lon_data[~np.isnan(lon_data)]

            if len(lon_data) == 0:
                self.log_issue('no_valid_longitude',
                              "No valid longitude values found")
                return ds

            lon_min = float(np.min(lon_data))
            lon_max = float(np.max(lon_data))

            # Add global attributes
            if 'geospatial_lon_min' not in ds.attrs:
                ds.attrs['geospatial_lon_min'] = lon_min
                self.log_change('attribute_added',
                              f"Added geospatial_lon_min: {lon_min:.5f}")

            if 'geospatial_lon_max' not in ds.attrs:
                ds.attrs['geospatial_lon_max'] = lon_max
                self.log_change('attribute_added',
                              f"Added geospatial_lon_max: {lon_max:.5f}")

            if 'geospatial_lon_units' not in ds.attrs:
                ds.attrs['geospatial_lon_units'] = 'degrees_east'
                self.log_change('attribute_added',
                              'Added geospatial_lon_units: degrees_east')

            # Add bounds as single value if float is stationary
            if abs(lon_max - lon_min) < 0.01:
                if 'geospatial_lon' not in ds.attrs:
                    ds.attrs['geospatial_lon'] = float(np.mean(lon_data))
                    self.log_change('attribute_added',
                                  f"Added geospatial_lon: {np.mean(lon_data):.5f} "
                                  "(stationary float)")

        except Exception as e:
            self.log_issue('longitude_extraction_error',
                          f"Error extracting longitude bounds: {e}")

        return ds

    def _extract_time_coverage(self, ds: xr.Dataset) -> xr.Dataset:
        """Extract and add time coverage"""

        time_var = self._find_time_variable(ds)

        if not time_var:
            return ds

        try:
            time_data = ds[time_var]

            # Handle different time formats
            # Argo JULD is days since 1950-01-01
            if time_var == 'JULD':
                # Get valid (non-NaN) times
                valid_times = time_data.values[~np.isnan(time_data.values)]

                if len(valid_times) == 0:
                    self.log_issue('no_valid_times',
                                  "No valid time values found")
                    return ds

                # Convert Argo JULD to datetime
                # JULD is days since 1950-01-01 00:00:00 UTC
                reference_date = np.datetime64('1950-01-01')
                time_min = reference_date + np.timedelta64(int(np.min(valid_times)), 'D')
                time_max = reference_date + np.timedelta64(int(np.max(valid_times)), 'D')

            else:
                # Assume xarray can handle it
                valid_times = time_data.values[~np.isnan(time_data.values.astype(float))]
                time_min = np.min(valid_times)
                time_max = np.max(valid_times)

            # Convert to ISO 8601 strings
            time_min_str = np.datetime_as_string(time_min, unit='s') + 'Z'
            time_max_str = np.datetime_as_string(time_max, unit='s') + 'Z'

            # Add time coverage attributes
            if 'time_coverage_start' not in ds.attrs:
                ds.attrs['time_coverage_start'] = time_min_str
                self.log_change('attribute_added',
                              f"Added time_coverage_start: {time_min_str}")

            if 'time_coverage_end' not in ds.attrs:
                ds.attrs['time_coverage_end'] = time_max_str
                self.log_change('attribute_added',
                              f"Added time_coverage_end: {time_max_str}")

            # Calculate duration
            duration_days = float(np.max(valid_times) - np.min(valid_times))
            if 'time_coverage_duration' not in ds.attrs:
                ds.attrs['time_coverage_duration'] = f"P{int(duration_days)}D"
                self.log_change('attribute_added',
                              f"Added time_coverage_duration: {int(duration_days)} days")

        except Exception as e:
            self.log_issue('time_extraction_error',
                          f"Error extracting time coverage: {e}")

        return ds

    def _add_geospatial_resolution(self, ds: xr.Dataset) -> xr.Dataset:
        """Add geospatial resolution information"""

        # For Argo floats, resolution is essentially point measurements
        if 'geospatial_lat_resolution' not in ds.attrs:
            ds.attrs['geospatial_lat_resolution'] = 'point'
            self.log_change('attribute_added',
                          'Added geospatial_lat_resolution: point')

        if 'geospatial_lon_resolution' not in ds.attrs:
            ds.attrs['geospatial_lon_resolution'] = 'point'
            self.log_change('attribute_added',
                          'Added geospatial_lon_resolution: point')

        # Vertical resolution (depth levels)
        if 'PRES' in ds.variables or 'PRES_ADJUSTED' in ds.variables:
            pres_var = 'PRES_ADJUSTED' if 'PRES_ADJUSTED' in ds.variables else 'PRES'

            try:
                pres_data = ds[pres_var].values.flatten()
                pres_data = pres_data[~np.isnan(pres_data)]

                if len(pres_data) > 1:
                    # Calculate median vertical resolution
                    sorted_pres = np.sort(pres_data)
                    diffs = np.diff(sorted_pres)
                    median_res = float(np.median(diffs))

                    if 'geospatial_vertical_min' not in ds.attrs:
                        ds.attrs['geospatial_vertical_min'] = float(np.min(pres_data))
                        self.log_change('attribute_added',
                                      f"Added geospatial_vertical_min: {np.min(pres_data):.1f} dbar")

                    if 'geospatial_vertical_max' not in ds.attrs:
                        ds.attrs['geospatial_vertical_max'] = float(np.max(pres_data))
                        self.log_change('attribute_added',
                                      f"Added geospatial_vertical_max: {np.max(pres_data):.1f} dbar")

                    if 'geospatial_vertical_resolution' not in ds.attrs:
                        ds.attrs['geospatial_vertical_resolution'] = f"{median_res:.1f} dbar"
                        self.log_change('attribute_added',
                                      f"Added geospatial_vertical_resolution: {median_res:.1f} dbar")

                    if 'geospatial_vertical_units' not in ds.attrs:
                        ds.attrs['geospatial_vertical_units'] = 'dbar'
                        self.log_change('attribute_added',
                                      'Added geospatial_vertical_units: dbar')

                    if 'geospatial_vertical_positive' not in ds.attrs:
                        ds.attrs['geospatial_vertical_positive'] = 'down'
                        self.log_change('attribute_added',
                                      'Added geospatial_vertical_positive: down')

            except Exception as e:
                self.log_issue('vertical_resolution_error',
                              f"Error calculating vertical resolution: {e}")

        return ds

    def validate(self) -> bool:
        """
        Validate that geospatial metadata was added

        Returns:
        --------
        bool: True if validation passed
        """
        ds = self.dataset

        required_attrs = [
            'geospatial_lat_min',
            'geospatial_lat_max',
            'geospatial_lon_min',
            'geospatial_lon_max',
        ]

        missing = [attr for attr in required_attrs if attr not in ds.attrs]

        if missing:
            self.logger.warning(f"Missing geospatial attributes: {missing}")
            return False

        # Check for time coverage
        if 'time_coverage_start' not in ds.attrs:
            self.logger.warning("Missing time_coverage_start")
            return False

        self.logger.info("Geospatial metadata validation passed")
        return True
