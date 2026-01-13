"""
Coordinate Variable Enricher

Adds missing coordinate variables (lat, lon, depth) to improve CF compliance.
"""

import sys
from pathlib import Path
import xarray as xr
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from transform.base_enricher import BaseEnricher
from utils import get_logger

logger = get_logger(__name__)


class CoordinateEnricher(BaseEnricher):
    """
    Add missing coordinate variables

    Extracts coordinates from global attributes and creates proper
    coordinate variables for CF compliance.
    """

    def enrich(self) -> xr.Dataset:
        """
        Add missing coordinate variables

        Returns:
        --------
        xarray.Dataset: Dataset with coordinate variables added
        """
        self.logger.info("Adding coordinate variables")

        ds = self.dataset.copy(deep=True)

        # Add lat/lon coordinates if missing
        ds = self._add_spatial_coordinates(ds)

        # Add depth coordinate if missing
        ds = self._add_depth_coordinate(ds)

        # Ensure time coordinate is properly formatted
        ds = self._fix_time_coordinate(ds)

        self.dataset = ds
        return ds

    def _add_spatial_coordinates(self, ds: xr.Dataset) -> xr.Dataset:
        """Add lat/lon coordinates from global attributes"""

        # Check if lat/lon already exist
        has_lat = any('lat' in str(var).lower() for var in ds.coords)
        has_lon = any('lon' in str(var).lower() for var in ds.coords)

        if has_lat and has_lon:
            self.logger.debug("Spatial coordinates already present")
            return ds

        # Try to extract from global attributes
        lat_attrs = ['lat', 'latitude', 'geospatial_lat_min', 'nominal_latitude']
        lon_attrs = ['lon', 'longitude', 'geospatial_lon_min', 'nominal_longitude']

        lat_value = None
        lon_value = None

        # Find latitude
        for attr in lat_attrs:
            if attr in ds.attrs:
                try:
                    lat_value = float(ds.attrs[attr])
                    break
                except (ValueError, TypeError):
                    continue

        # Find longitude
        for attr in lon_attrs:
            if attr in ds.attrs:
                try:
                    lon_value = float(ds.attrs[attr])
                    break
                except (ValueError, TypeError):
                    continue

        # Add coordinates if found
        if lat_value is not None and not has_lat:
            ds = ds.assign_coords(lat=lat_value)
            ds['lat'].attrs['standard_name'] = 'latitude'
            ds['lat'].attrs['long_name'] = 'Latitude'
            ds['lat'].attrs['units'] = 'degrees_north'
            ds['lat'].attrs['axis'] = 'Y'
            self.log_change('coordinate_added', f"Added lat = {lat_value}")

        if lon_value is not None and not has_lon:
            ds = ds.assign_coords(lon=lon_value)
            ds['lon'].attrs['standard_name'] = 'longitude'
            ds['lon'].attrs['long_name'] = 'Longitude'
            ds['lon'].attrs['units'] = 'degrees_east'
            ds['lon'].attrs['axis'] = 'X'
            self.log_change('coordinate_added', f"Added lon = {lon_value}")

        if lat_value is None or lon_value is None:
            self.log_issue('missing_coordinates',
                          'Could not find lat/lon in global attributes')

        return ds

    def _add_depth_coordinate(self, ds: xr.Dataset) -> xr.Dataset:
        """Add depth coordinate from global attributes"""

        # Check if depth already exists
        has_depth = any('depth' in str(var).lower() for var in ds.coords)

        if has_depth:
            self.logger.debug("Depth coordinate already present")
            return ds

        # Try to extract from global attributes
        depth_attrs = ['depth', 'nominal_depth', 'geospatial_vertical_min',
                      'sensor_depth']

        depth_value = None

        for attr in depth_attrs:
            if attr in ds.attrs:
                try:
                    depth_value = float(ds.attrs[attr])
                    break
                except (ValueError, TypeError):
                    continue

        # Add depth coordinate if found
        if depth_value is not None:
            ds = ds.assign_coords(depth=depth_value)
            ds['depth'].attrs['standard_name'] = 'depth'
            ds['depth'].attrs['long_name'] = 'Depth'
            ds['depth'].attrs['units'] = 'm'
            ds['depth'].attrs['positive'] = 'down'
            ds['depth'].attrs['axis'] = 'Z'
            self.log_change('coordinate_added', f"Added depth = {depth_value}")
        else:
            self.log_issue('missing_depth',
                          'Could not find depth in global attributes')

        return ds

    def _fix_time_coordinate(self, ds: xr.Dataset) -> xr.Dataset:
        """Ensure time coordinate has proper attributes"""

        # Find time coordinate
        time_vars = [v for v in ds.coords if 'time' in str(v).lower()]

        if not time_vars:
            self.log_issue('missing_time', 'No time coordinate found')
            return ds

        time_var = time_vars[0]

        # Add standard attributes if missing
        if 'standard_name' not in ds[time_var].attrs:
            ds[time_var].attrs['standard_name'] = 'time'
            self.log_change('attribute_added', f"Added standard_name to {time_var}")

        if 'long_name' not in ds[time_var].attrs:
            ds[time_var].attrs['long_name'] = 'Time'
            self.log_change('attribute_added', f"Added long_name to {time_var}")

        if 'axis' not in ds[time_var].attrs:
            ds[time_var].attrs['axis'] = 'T'
            self.log_change('attribute_added', f"Added axis to {time_var}")

        return ds

    def validate(self) -> bool:
        """
        Validate that coordinate variables were added

        Returns:
        --------
        bool: True if validation passed
        """
        ds = self.dataset

        # Check for required coordinates
        has_time = any('time' in str(v).lower() for v in ds.coords)
        has_lat = any('lat' in str(v).lower() for v in ds.coords)
        has_lon = any('lon' in str(v).lower() for v in ds.coords)

        if not has_time:
            self.logger.error("Validation failed: no time coordinate")
            return False

        if not (has_lat and has_lon):
            self.logger.warning("Validation warning: missing spatial coordinates")
            # Not a critical failure, but not ideal
            return True

        self.logger.info("Coordinate validation passed")
        return True
