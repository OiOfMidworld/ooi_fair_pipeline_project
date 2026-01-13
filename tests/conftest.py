"""
Pytest configuration and shared fixtures for OOI FAIR Pipeline tests
"""

import pytest
import tempfile
import xarray as xr
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def minimal_netcdf(temp_dir):
    """
    Create a minimal NetCDF file with basic structure

    This represents a "bare minimum" dataset with no FAIR metadata
    """
    # Create simple dataset
    data = xr.Dataset(
        {
            'temperature': (['time'], np.random.rand(10)),
            'salinity': (['time'], np.random.rand(10)),
        },
        coords={
            'time': np.arange(10)
        }
    )

    # Save to file
    file_path = temp_dir / 'minimal.nc'
    data.to_netcdf(file_path)

    yield file_path


@pytest.fixture
def poor_fair_netcdf(temp_dir):
    """
    Create a NetCDF file with poor FAIR compliance

    Missing:
    - Most global metadata
    - Variable attributes
    - Standard names
    - Proper coordinates
    """
    data = xr.Dataset(
        {
            'temp': (['obs'], np.random.rand(100)),
            'sal': (['obs'], np.random.rand(100)),
        },
        coords={
            'obs': np.arange(100)
        },
        attrs={
            'title': 'Test Dataset',
            'institution': 'Test Institute'
        }
    )

    file_path = temp_dir / 'poor_fair.nc'
    data.to_netcdf(file_path)

    yield file_path


@pytest.fixture
def good_fair_netcdf(temp_dir):
    """
    Create a NetCDF file with good FAIR compliance

    Includes:
    - Rich global metadata
    - CF-compliant attributes
    - Standard names
    - Proper coordinates
    - QC flags
    """
    # Create dataset with proper structure
    data = xr.Dataset(
        {
            'sea_water_temperature': (
                ['time'],
                np.random.rand(100) + 15,
                {
                    'standard_name': 'sea_water_temperature',
                    'long_name': 'Sea Water Temperature',
                    'units': 'degree_C',
                    'valid_min': -2.0,
                    'valid_max': 40.0
                }
            ),
            'sea_water_practical_salinity': (
                ['time'],
                np.random.rand(100) + 35,
                {
                    'standard_name': 'sea_water_practical_salinity',
                    'long_name': 'Sea Water Practical Salinity',
                    'units': 'psu',
                    'valid_min': 0.0,
                    'valid_max': 42.0
                }
            ),
            'temperature_qc': (
                ['time'],
                np.ones(100, dtype=int),
                {
                    'long_name': 'Temperature Quality Control Flags',
                    'flag_values': [1, 2, 3, 4],
                    'flag_meanings': 'good unknown suspect bad'
                }
            ),
        },
        coords={
            'time': (
                ['time'],
                np.arange(100),
                {
                    'standard_name': 'time',
                    'long_name': 'Time',
                    'units': 'seconds since 2024-01-01T00:00:00Z'
                }
            ),
            'lat': 44.6,
            'lon': -124.3,
            'depth': 100.0
        },
        attrs={
            # Findable
            'id': 'test-dataset-001',
            'uuid': '12345678-1234-1234-1234-123456789abc',
            'title': 'Test Ocean Dataset',
            'summary': 'A test dataset for FAIR assessment',
            'keywords': 'oceanography, temperature, salinity',
            'creator_name': 'Test Creator',
            'institution': 'Test Ocean Institute',
            'project': 'Test Project',

            # Searchable
            'geospatial_lat_min': 44.0,
            'geospatial_lat_max': 45.0,
            'geospatial_lon_min': -125.0,
            'geospatial_lon_max': -124.0,
            'time_coverage_start': '2024-01-01T00:00:00Z',
            'time_coverage_end': '2024-01-02T00:00:00Z',

            # Standards
            'Conventions': 'CF-1.6, ACDD-1.3',
            'Metadata_Conventions': 'CF-1.6, ACDD-1.3',

            # Accessible
            'sourceUrl': 'https://example.com/data/test-dataset-001',
            'creator_email': 'creator@example.com',
            'publisher_email': 'publisher@example.com',
            'license': 'CC-BY-4.0',
            'references': 'https://example.com/metadata',

            # Reusable
            'source': 'CTD measurements',
            'processing_level': 'L2',
            'history': 'Created 2024-01-01. Processed with test pipeline.',
            'creator_institution': 'Test Ocean Institute',
            'date_created': '2024-01-01T00:00:00Z',

            # Community standards
            'featureType': 'timeSeries',
            'cdm_data_type': 'TimeSeries'
        }
    )

    file_path = temp_dir / 'good_fair.nc'
    data.to_netcdf(file_path)

    yield file_path


@pytest.fixture
def sample_metadata():
    """Sample global attributes for testing"""
    return {
        'id': 'test-001',
        'title': 'Test Dataset',
        'summary': 'A test dataset',
        'keywords': 'test, data',
        'creator_name': 'Test Creator',
        'institution': 'Test Institute',
        'Conventions': 'CF-1.6',
        'license': 'CC-BY-4.0'
    }


@pytest.fixture
def sample_variables():
    """Sample variable attributes for testing"""
    return {
        'temperature': {
            'standard_name': 'sea_water_temperature',
            'long_name': 'Sea Water Temperature',
            'units': 'degree_C'
        },
        'salinity': {
            'standard_name': 'sea_water_practical_salinity',
            'long_name': 'Sea Water Practical Salinity',
            'units': 'psu'
        },
        'pressure': {
            'long_name': 'Water Pressure',
            'units': 'dbar'
        }
    }


@pytest.fixture
def real_ooi_dataset():
    """
    Path to real OOI dataset if available

    Returns None if not available (skip tests that need it)
    """
    test_data_path = Path('data/raw/test_download.nc')

    if test_data_path.exists():
        return test_data_path
    else:
        return None
