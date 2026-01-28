"""
BGC-Argo Standard Name Mapper

Maps BGC-Argo variable names to CF standard names.

Handles Argo-specific naming conventions including:
- Core physical variables (PRES, TEMP, PSAL)
- BGC variables (pH, DOXY, NITRATE, CHLA, BBP)
- Adjusted variables (*_ADJUSTED)
- QC variables (*_QC)
- Error variables (*_ADJUSTED_ERROR)

Sprint: 4B - BGC-Argo mCDR/MRV Extension
"""

import sys
from pathlib import Path
import xarray as xr

sys.path.insert(0, str(Path(__file__).parent.parent))

from transform.base_enricher import BaseEnricher
from utils import get_logger

logger = get_logger(__name__)


class BGCStandardNameMapper(BaseEnricher):
    """
    Map Argo variable names to CF standard names

    Adds standard_name, long_name, and enhances units
    for BGC-Argo variables.
    """

    # Argo to CF standard name mapping
    STANDARD_NAME_MAP = {
        # Core physical variables
        'PRES': 'sea_water_pressure',
        'PRES_ADJUSTED': 'sea_water_pressure',
        'TEMP': 'sea_water_temperature',
        'TEMP_ADJUSTED': 'sea_water_temperature',
        'PSAL': 'sea_water_practical_salinity',
        'PSAL_ADJUSTED': 'sea_water_practical_salinity',

        # BGC variables - pH
        'PH_IN_SITU_TOTAL': 'sea_water_ph_reported_on_total_scale',
        'PH_IN_SITU_TOTAL_ADJUSTED': 'sea_water_ph_reported_on_total_scale',

        # BGC variables - Oxygen
        'DOXY': 'moles_of_oxygen_per_unit_mass_in_sea_water',
        'DOXY_ADJUSTED': 'moles_of_oxygen_per_unit_mass_in_sea_water',

        # BGC variables - Nitrate
        'NITRATE': 'moles_of_nitrate_per_unit_mass_in_sea_water',
        'NITRATE_ADJUSTED': 'moles_of_nitrate_per_unit_mass_in_sea_water',

        # BGC variables - Chlorophyll
        'CHLA': 'mass_concentration_of_chlorophyll_a_in_sea_water',
        'CHLA_ADJUSTED': 'mass_concentration_of_chlorophyll_a_in_sea_water',

        # BGC variables - Backscatter
        'BBP': 'volume_backwards_scattering_coefficient_of_radiative_flux_in_sea_water',
        'BBP532': 'volume_backwards_scattering_coefficient_of_radiative_flux_in_sea_water',
        'BBP700': 'volume_backwards_scattering_coefficient_of_radiative_flux_in_sea_water',
        'BBP_ADJUSTED': 'volume_backwards_scattering_coefficient_of_radiative_flux_in_sea_water',

        # Coordinates
        'LATITUDE': 'latitude',
        'LONGITUDE': 'longitude',
        'JULD': 'time',
    }

    # Long name mapping
    LONG_NAME_MAP = {
        'PRES': 'Sea Pressure',
        'PRES_ADJUSTED': 'Sea Pressure (Adjusted)',
        'TEMP': 'Sea Temperature',
        'TEMP_ADJUSTED': 'Sea Temperature (Adjusted)',
        'PSAL': 'Practical Salinity',
        'PSAL_ADJUSTED': 'Practical Salinity (Adjusted)',
        'PH_IN_SITU_TOTAL': 'pH (in situ total scale)',
        'PH_IN_SITU_TOTAL_ADJUSTED': 'pH (in situ total scale, Adjusted)',
        'DOXY': 'Dissolved Oxygen',
        'DOXY_ADJUSTED': 'Dissolved Oxygen (Adjusted)',
        'NITRATE': 'Nitrate',
        'NITRATE_ADJUSTED': 'Nitrate (Adjusted)',
        'CHLA': 'Chlorophyll-A',
        'CHLA_ADJUSTED': 'Chlorophyll-A (Adjusted)',
        'BBP': 'Particle Backscattering Coefficient',
        'BBP532': 'Particle Backscattering Coefficient at 532 nm',
        'BBP700': 'Particle Backscattering Coefficient at 700 nm',
        'LATITUDE': 'Latitude',
        'LONGITUDE': 'Longitude',
        'JULD': 'Julian Date',
    }

    # Units verification/addition
    UNITS_MAP = {
        'PRES': 'decibar',
        'PRES_ADJUSTED': 'decibar',
        'TEMP': 'degree_Celsius',
        'TEMP_ADJUSTED': 'degree_Celsius',
        'PSAL': 'psu',
        'PSAL_ADJUSTED': 'psu',
        'PH_IN_SITU_TOTAL': '1',  # dimensionless
        'PH_IN_SITU_TOTAL_ADJUSTED': '1',
        'DOXY': 'micromole/kg',
        'DOXY_ADJUSTED': 'micromole/kg',
        'NITRATE': 'micromole/kg',
        'NITRATE_ADJUSTED': 'micromole/kg',
        'CHLA': 'mg/m3',
        'CHLA_ADJUSTED': 'mg/m3',
        'BBP': 'm-1',
        'BBP532': 'm-1',
        'BBP700': 'm-1',
        'LATITUDE': 'degrees_north',
        'LONGITUDE': 'degrees_east',
        'JULD': 'days since 1950-01-01 00:00:00 UTC',
    }

    def enrich(self) -> xr.Dataset:
        """
        Add CF standard names to BGC-Argo variables

        Returns:
        --------
        xr.Dataset: Dataset with CF standard names
        """
        self.logger.info("Mapping BGC-Argo variables to CF standard names")

        ds = self.dataset.copy(deep=True)

        # Process each variable
        for var_name in list(ds.variables.keys()):
            if var_name in ds.dims:
                # Skip dimension variables
                continue

            ds = self._enrich_variable(ds, var_name)

        self.dataset = ds
        return ds

    def _enrich_variable(self, ds: xr.Dataset, var_name: str) -> xr.Dataset:
        """Enrich a single variable with CF metadata"""

        var = ds[var_name]

        # Add standard_name if we have a mapping
        if var_name in self.STANDARD_NAME_MAP:
            if 'standard_name' not in var.attrs:
                standard_name = self.STANDARD_NAME_MAP[var_name]
                var.attrs['standard_name'] = standard_name
                self.log_change('attribute_added',
                              f"{var_name}: standard_name = {standard_name}")
        elif not self._is_qc_variable(var_name):
            # Try to infer from base name (without _ADJUSTED suffix)
            base_name = var_name.replace('_ADJUSTED', '').replace('_QC', '')
            if base_name in self.STANDARD_NAME_MAP:
                standard_name = self.STANDARD_NAME_MAP[base_name]
                var.attrs['standard_name'] = standard_name
                self.log_change('attribute_added',
                              f"{var_name}: standard_name = {standard_name} (inferred)")

        # Add long_name if we have a mapping
        if var_name in self.LONG_NAME_MAP:
            if 'long_name' not in var.attrs:
                long_name = self.LONG_NAME_MAP[var_name]
                var.attrs['long_name'] = long_name
                self.log_change('attribute_added',
                              f"{var_name}: long_name = {long_name}")
        elif not self._is_qc_variable(var_name):
            # Generate from variable name
            long_name = self._generate_long_name(var_name)
            if 'long_name' not in var.attrs:
                var.attrs['long_name'] = long_name
                self.log_change('attribute_added',
                              f"{var_name}: long_name = {long_name}")

        # Add/verify units (skip JULD - xarray handles time encoding)
        if var_name in self.UNITS_MAP and var_name != 'JULD':
            if 'units' not in var.attrs:
                units = self.UNITS_MAP[var_name]
                var.attrs['units'] = units
                self.log_change('attribute_added',
                              f"{var_name}: units = {units}")

        # Add axis attribute for coordinates
        if var_name == 'LATITUDE':
            if 'axis' not in var.attrs:
                var.attrs['axis'] = 'Y'
                self.log_change('attribute_added', f"{var_name}: axis = Y")

        if var_name == 'LONGITUDE':
            if 'axis' not in var.attrs:
                var.attrs['axis'] = 'X'
                self.log_change('attribute_added', f"{var_name}: axis = X")

        if var_name == 'JULD':
            if 'axis' not in var.attrs:
                var.attrs['axis'] = 'T'
                self.log_change('attribute_added', f"{var_name}: axis = T")

        # Add comment for adjusted variables
        if '_ADJUSTED' in var_name and 'comment' not in var.attrs:
            var.attrs['comment'] = ('Adjusted value after application of real-time '
                                   'and delayed-mode quality control procedures')
            self.log_change('attribute_added',
                          f"{var_name}: added adjustment comment")

        return ds

    def _is_qc_variable(self, var_name: str) -> bool:
        """Check if variable is a QC flag"""
        return ('_QC' in var_name or
                'QARTOD' in var_name or
                'ADJUSTED_ERROR' in var_name)

    def _generate_long_name(self, var_name: str) -> str:
        """Generate long name from variable name"""

        # Handle _ADJUSTED suffix
        if var_name.endswith('_ADJUSTED'):
            base = var_name.replace('_ADJUSTED', '')
            long_name = self._format_name(base)
            return f"{long_name} (Adjusted)"

        # Handle _QC suffix
        if var_name.endswith('_QC'):
            base = var_name.replace('_QC', '')
            long_name = self._format_name(base)
            return f"{long_name} Quality Flag"

        # Handle _ERROR suffix
        if var_name.endswith('_ADJUSTED_ERROR'):
            base = var_name.replace('_ADJUSTED_ERROR', '')
            long_name = self._format_name(base)
            return f"{long_name} Adjusted Error"

        return self._format_name(var_name)

    def _format_name(self, name: str) -> str:
        """Format variable name into human-readable form"""

        # Replace underscores with spaces
        formatted = name.replace('_', ' ')

        # Capitalize words
        formatted = ' '.join(word.capitalize() for word in formatted.split())

        # Handle special abbreviations
        replacements = {
            'Ph': 'pH',
            'Doxy': 'Dissolved Oxygen',
            'Chla': 'Chlorophyll-A',
            'Bbp': 'Particle Backscattering',
            'Pres': 'Pressure',
            'Temp': 'Temperature',
            'Psal': 'Practical Salinity',
            'Juld': 'Julian Date',
        }

        for old, new in replacements.items():
            formatted = formatted.replace(old, new)

        return formatted

    def validate(self) -> bool:
        """
        Validate that key BGC variables have standard names

        Returns:
        --------
        bool: True if validation passed
        """
        ds = self.dataset

        # Check key BGC variables
        key_vars = ['PRES', 'TEMP', 'PSAL']
        bgc_vars = ['PH_IN_SITU_TOTAL', 'DOXY', 'NITRATE', 'CHLA']

        vars_to_check = []

        # Check which variables exist
        for var in key_vars + bgc_vars:
            if var in ds.variables:
                vars_to_check.append(var)
            elif f"{var}_ADJUSTED" in ds.variables:
                vars_to_check.append(f"{var}_ADJUSTED")

        # Verify they have standard_name
        missing_standard_name = []
        for var in vars_to_check:
            if 'standard_name' not in ds[var].attrs:
                missing_standard_name.append(var)

        if missing_standard_name:
            self.logger.warning(
                f"Variables missing standard_name: {missing_standard_name}"
            )
            return False

        self.logger.info(
            f"BGC standard name validation passed ({len(vars_to_check)} variables checked)"
        )
        return True
