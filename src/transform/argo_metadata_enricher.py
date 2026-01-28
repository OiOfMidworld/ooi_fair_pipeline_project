"""
Argo Metadata Enricher

Adds Argo-specific discovery metadata to BGC-Argo NetCDF files.

Addresses FAIR gaps specific to BGC-Argo data:
- Adds unique identifiers (WMO-based)
- Adds program/project information
- Adds creator/publisher metadata
- Adds license and data policy
- Adds source URLs
- Adds acknowledgment text

Sprint: 4B - BGC-Argo mCDR/MRV Extension
"""

import sys
from pathlib import Path
import xarray as xr
import re
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from transform.base_enricher import BaseEnricher
from utils import get_logger

logger = get_logger(__name__)


class ArgoMetadataEnricher(BaseEnricher):
    """
    Add Argo program metadata to BGC-Argo files

    Extracts WMO number from filename and adds comprehensive
    Argo program metadata for discovery and citation.
    """

    # Argo program defaults
    ARGO_DEFAULTS = {
        'program': 'Argo',
        'project': 'Biogeochemical-Argo',
        'creator_name': 'Argo',
        'creator_type': 'institution',
        'creator_institution': 'Argo',
        'creator_url': 'https://argo.ucsd.edu/',
        'creator_email': 'info@argo.ucsd.edu',
        'publisher_name': 'Global Data Assembly Centre (GDAC)',
        'publisher_type': 'institution',
        'publisher_institution': 'Argo GDAC',
        'publisher_url': 'https://www.ocean-ops.org/board/wa/GDAC',
        'publisher_email': 'info@argo.ucsd.edu',
        'institution': 'Argo',
        'license': 'These data are freely available under the Argo data policy. '
                  'Please acknowledge use of these data with: "These data were collected '
                  'and made freely available by the International Argo Program and the '
                  'national programs that contribute to it. (https://argo.ucsd.edu)"',
        'acknowledgement': 'These data were collected and made freely available by the '
                          'International Argo Program and the national programs that '
                          'contribute to it. (https://argo.ucsd.edu, https://www.ocean-ops.org)',
        'citation': 'Argo (2000). Argo float data and metadata from Global Data Assembly Centre (Argo GDAC). '
                   'SEANOE. https://doi.org/10.17882/42182',
        'references': 'https://argo.ucsd.edu, https://www.ocean-ops.org, '
                     'https://doi.org/10.17882/42182',
    }

    def __init__(self, dataset: xr.Dataset, file_path: str = None):
        """
        Initialize Argo metadata enricher

        Parameters:
        -----------
        dataset : xr.Dataset
            Input dataset
        file_path : str, optional
            Original file path (to extract WMO number)
        """
        super().__init__(dataset)
        self.file_path = Path(file_path) if file_path else None
        self.wmo_number = None
        self.dac = None

    def enrich(self) -> xr.Dataset:
        """
        Add Argo program metadata

        Returns:
        --------
        xr.Dataset: Dataset with enriched Argo metadata
        """
        self.logger.info("Enriching Argo program metadata")

        ds = self.dataset.copy(deep=True)

        # Extract WMO number from filename if available
        if self.file_path:
            self.wmo_number = self._extract_wmo_number(self.file_path)
            self.dac = self._guess_dac(self.file_path)

        # Add unique identifiers
        ds = self._add_identifiers(ds)

        # Add program/project info
        ds = self._add_program_info(ds)

        # Add creator/publisher info
        ds = self._add_creator_publisher(ds)

        # Add license and data policy
        ds = self._add_license(ds)

        # Add source URLs
        ds = self._add_source_urls(ds)

        # Add acknowledgment
        ds = self._add_acknowledgment(ds)

        # Add keywords
        ds = self._add_keywords(ds)

        # Add summary if missing
        ds = self._add_summary(ds)

        self.dataset = ds
        return ds

    def _extract_wmo_number(self, file_path: Path) -> str:
        """
        Extract WMO number from Argo filename

        Examples:
        - BD5904468_001.nc -> 5904468
        - R5904471_001.nc -> 5904471
        - 5904659_Rtraj.nc -> 5904659
        """
        filename = file_path.name

        # Pattern: BD/R/S + 7 digits
        match = re.search(r'[BRS]?D?(\d{7})', filename)
        if match:
            return match.group(1)

        # Pattern: just 7 digits
        match = re.search(r'(\d{7})', filename)
        if match:
            return match.group(1)

        self.log_issue('no_wmo_number',
                      f"Could not extract WMO number from {filename}")
        return None

    def _guess_dac(self, file_path: Path) -> str:
        """
        Guess Data Assembly Center from file path

        Common DACs: aoml, coriolis, meds, incois, etc.
        """
        path_str = str(file_path)

        for dac in ['aoml', 'coriolis', 'meds', 'incois', 'csio',
                    'jma', 'kma', 'bodc', 'csiro']:
            if dac in path_str.lower():
                return dac.upper()

        return 'GDAC'

    def _add_identifiers(self, ds: xr.Dataset) -> xr.Dataset:
        """Add unique identifiers"""

        # Add WMO-based ID
        if self.wmo_number:
            if 'id' not in ds.attrs:
                ds.attrs['id'] = f"ARGO-BGC-{self.wmo_number}"
                self.log_change('attribute_added',
                              f"Added id: ARGO-BGC-{self.wmo_number}")

            # Add naming_authority
            if 'naming_authority' not in ds.attrs:
                ds.attrs['naming_authority'] = 'org.argo'
                self.log_change('attribute_added',
                              'Added naming_authority: org.argo')

            # Add WMO number as attribute
            if 'wmo_platform_code' not in ds.attrs:
                ds.attrs['wmo_platform_code'] = self.wmo_number
                self.log_change('attribute_added',
                              f"Added wmo_platform_code: {self.wmo_number}")
        else:
            self.log_issue('no_identifier',
                          "Could not create unique identifier (no WMO number)")

        # Add DOI for Argo data
        if 'doi' not in ds.attrs:
            ds.attrs['doi'] = '10.17882/42182'
            self.log_change('attribute_added',
                          'Added Argo data DOI: 10.17882/42182')

        return ds

    def _add_program_info(self, ds: xr.Dataset) -> xr.Dataset:
        """Add program and project information"""

        if 'program' not in ds.attrs:
            ds.attrs['program'] = self.ARGO_DEFAULTS['program']
            self.log_change('attribute_added',
                          f"Added program: {self.ARGO_DEFAULTS['program']}")

        if 'project' not in ds.attrs:
            ds.attrs['project'] = self.ARGO_DEFAULTS['project']
            self.log_change('attribute_added',
                          f"Added project: {self.ARGO_DEFAULTS['project']}")

        return ds

    def _add_creator_publisher(self, ds: xr.Dataset) -> xr.Dataset:
        """Add creator and publisher metadata"""

        # Creator info
        for key in ['creator_name', 'creator_type', 'creator_institution',
                    'creator_url', 'creator_email']:
            if key not in ds.attrs:
                ds.attrs[key] = self.ARGO_DEFAULTS[key]
                self.log_change('attribute_added',
                              f"Added {key}: {self.ARGO_DEFAULTS[key]}")

        # Publisher info
        for key in ['publisher_name', 'publisher_type', 'publisher_institution',
                    'publisher_url', 'publisher_email']:
            if key not in ds.attrs:
                ds.attrs[key] = self.ARGO_DEFAULTS[key]
                self.log_change('attribute_added',
                              f"Added {key}: {self.ARGO_DEFAULTS[key]}")

        # Institution
        if 'institution' not in ds.attrs:
            ds.attrs['institution'] = self.ARGO_DEFAULTS['institution']
            self.log_change('attribute_added',
                          f"Added institution: {self.ARGO_DEFAULTS['institution']}")

        return ds

    def _add_license(self, ds: xr.Dataset) -> xr.Dataset:
        """Add license and data policy"""

        if 'license' not in ds.attrs:
            ds.attrs['license'] = self.ARGO_DEFAULTS['license']
            self.log_change('attribute_added', 'Added Argo data license')

        return ds

    def _add_source_urls(self, ds: xr.Dataset) -> xr.Dataset:
        """Add source URLs for data access"""

        # Source URL
        if 'source' not in ds.attrs and self.wmo_number:
            source_url = f"https://data-argo.ifremer.fr/dac/aoml/{self.wmo_number}/"
            ds.attrs['source'] = source_url
            self.log_change('attribute_added', f"Added source: {source_url}")

        # ERDDAP dataset ID
        if 'datasetID' not in ds.attrs and self.wmo_number:
            ds.attrs['datasetID'] = f"ArgoFloats-{self.wmo_number}"
            self.log_change('attribute_added',
                          f"Added datasetID: ArgoFloats-{self.wmo_number}")

        return ds

    def _add_acknowledgment(self, ds: xr.Dataset) -> xr.Dataset:
        """Add acknowledgment and citation"""

        if 'acknowledgement' not in ds.attrs:
            ds.attrs['acknowledgement'] = self.ARGO_DEFAULTS['acknowledgement']
            self.log_change('attribute_added', 'Added acknowledgement text')

        if 'citation' not in ds.attrs:
            ds.attrs['citation'] = self.ARGO_DEFAULTS['citation']
            self.log_change('attribute_added', 'Added citation')

        # Update references if needed
        if 'references' in ds.attrs:
            # Append Argo references if not already present
            if 'argo.ucsd.edu' not in ds.attrs['references'].lower():
                ds.attrs['references'] += f"; {self.ARGO_DEFAULTS['references']}"
                self.log_change('attribute_updated', 'Updated references with Argo URLs')
        else:
            ds.attrs['references'] = self.ARGO_DEFAULTS['references']
            self.log_change('attribute_added', 'Added references')

        return ds

    def _add_keywords(self, ds: xr.Dataset) -> xr.Dataset:
        """Add relevant keywords for discovery"""

        if 'keywords' not in ds.attrs:
            keywords = [
                'EARTH SCIENCE > OCEANS',
                'Argo',
                'Biogeochemical-Argo',
                'BGC-Argo',
                'profiling float',
                'ocean observations',
                'in situ',
                'pH',
                'dissolved oxygen',
                'nitrate',
                'chlorophyll',
                'ocean acidification',
                'marine carbon dioxide removal',
                'mCDR',
                'ocean alkalinity',
            ]

            ds.attrs['keywords'] = ', '.join(keywords)
            self.log_change('attribute_added',
                          f"Added {len(keywords)} keywords for discovery")

        # Add keywords_vocabulary
        if 'keywords_vocabulary' not in ds.attrs:
            ds.attrs['keywords_vocabulary'] = 'GCMD Science Keywords'
            self.log_change('attribute_added',
                          'Added keywords_vocabulary: GCMD')

        return ds

    def _add_summary(self, ds: xr.Dataset) -> xr.Dataset:
        """Add summary/abstract if missing"""

        if 'summary' not in ds.attrs:
            if self.wmo_number:
                summary = (
                    f"Biogeochemical-Argo (BGC-Argo) float {self.wmo_number} profile data. "
                    f"BGC-Argo floats measure ocean biogeochemical parameters including pH, "
                    f"dissolved oxygen, nitrate, and chlorophyll-a in addition to physical "
                    f"properties. Data are collected via autonomous profiling floats that "
                    f"drift with ocean currents and profile from the surface to 2000m depth "
                    f"approximately every 10 days. BGC-Argo data are critical for understanding "
                    f"ocean carbon cycling, acidification, and provide essential baseline "
                    f"monitoring for marine carbon dioxide removal (mCDR) verification."
                )
            else:
                summary = (
                    "Biogeochemical-Argo (BGC-Argo) float profile data with measurements of "
                    "ocean pH, dissolved oxygen, nitrate, and chlorophyll-a alongside physical "
                    "properties."
                )

            ds.attrs['summary'] = summary
            self.log_change('attribute_added', 'Added descriptive summary')

        return ds

    def validate(self) -> bool:
        """
        Validate that required Argo metadata is present

        Returns:
        --------
        bool: True if validation passed
        """
        ds = self.dataset

        required_attrs = [
            'program',
            'license',
            'creator_name',
            'publisher_name',
        ]

        missing = [attr for attr in required_attrs if attr not in ds.attrs]

        if missing:
            self.logger.warning(f"Missing required Argo attributes: {missing}")
            return False

        # Check for identifier (WMO-based or other)
        has_id = any(attr in ds.attrs for attr in ['id', 'wmo_platform_code', 'doi'])

        if not has_id:
            self.logger.warning("No unique identifier found")
            return False

        self.logger.info("Argo metadata validation passed")
        return True
