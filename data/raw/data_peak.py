import xarray as xr
from compliance_checker.runner import ComplianceChecker, CheckSuite
import sys, json


# Path to your NetCDF file
file_path = 'deployment0020_CE02SHSM-RID27-03-CTDBPC000-telemetered-ctdbp_cdef_dcl_instrument_20251101T023003.923000-20251226T063106.137000.nc'

# This prints the report directly - no parsing needed
ComplianceChecker.run_checker(
    file_path,
    ['cf'],
    verbose=True,
    criteria='normal'
)

print("\n✅ CF Compliance check complete!")