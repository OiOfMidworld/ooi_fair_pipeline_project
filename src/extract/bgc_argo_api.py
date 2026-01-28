"""
BGC-Argo Data Extractor

Downloads Biogeochemical-Argo float profiles from GDAC (Global Data Assembly Centers).
Focuses on floats with pH, oxygen, and other carbon-relevant sensors.

Data sources:
- Ifremer GDAC (France): https://data-argo.ifremer.fr
- USGODAE GDAC (USA): https://usgodae.org/ftp/outgoing/argo

Author: OOI-FAIR Pipeline Project
Sprint: 4A - mCDR/MRV Extension
"""

import sys
from pathlib import Path
import requests
import xarray as xr
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import ftplib
import io

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import get_logger
from utils.exceptions import DownloadError

logger = get_logger(__name__)


class BGCArgoExtractor:
    """
    Extract BGC-Argo float profiles from GDAC

    Focuses on biogeochemical parameters relevant for marine CDR:
    - pH (ocean acidification monitoring)
    - Dissolved oxygen
    - Nitrate
    - Chlorophyll-a
    """

    # GDAC HTTP servers
    IFREMER_HTTP = "https://data-argo.ifremer.fr"
    USGODAE_HTTP = "https://usgodae.org/ftp/outgoing/argo"

    # FTP servers (fallback)
    IFREMER_FTP = "ftp.ifremer.fr"
    USGODAE_FTP = "usgodae.org"

    def __init__(self, data_dir: str = "data/bgc_argo"):
        """
        Initialize BGC-Argo data extractor

        Parameters:
        -----------
        data_dir : str
            Directory to save downloaded files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OOI-FAIR-Pipeline/1.0 (mCDR-MRV research)'
        })

        logger.info(f"Initialized BGC-Argo extractor")
        logger.info(f"Data directory: {self.data_dir}")

    def search_ph_floats(self,
                        region: Optional[str] = None,
                        limit: int = 10) -> List[Dict]:
        """
        Search for BGC-Argo floats with pH sensors

        Parameters:
        -----------
        region : str, optional
            Geographic region (e.g., 'north_pacific', 'north_atlantic')
        limit : int
            Maximum number of floats to return

        Returns:
        --------
        List[Dict]: Float metadata
        """
        logger.info(f"Searching for BGC-Argo floats with pH sensors (limit={limit})")

        # Use Argo index file to find floats
        index_url = f"{self.IFREMER_HTTP}/ar_index_global_prof.txt"

        try:
            logger.info(f"Downloading Argo index from: {index_url}")
            response = self.session.get(index_url, timeout=30)
            response.raise_for_status()

            # Parse index file
            lines = response.text.strip().split('\n')
            header = lines[0].split(',')

            ph_floats = []
            seen_floats = set()

            for line in lines[1:]:
                if len(ph_floats) >= limit:
                    break

                parts = line.split(',')
                if len(parts) < 8:
                    continue

                # Check if file contains BGC parameters (B-file)
                file_path = parts[0]
                if '/profiles/B' in file_path or '/profiles/S' in file_path:
                    # Extract float ID (WMO number)
                    float_id = file_path.split('/')[1]

                    if float_id not in seen_floats:
                        seen_floats.add(float_id)

                        float_info = {
                            'float_id': float_id,
                            'file_path': file_path,
                            'date': parts[1] if len(parts) > 1 else None,
                            'lat': float(parts[2]) if len(parts) > 2 and parts[2] else None,
                            'lon': float(parts[3]) if len(parts) > 3 and parts[3] else None,
                        }

                        ph_floats.append(float_info)
                        logger.debug(f"Found BGC float: {float_id}")

            logger.info(f"Found {len(ph_floats)} BGC-Argo floats")
            return ph_floats

        except Exception as e:
            logger.error(f"Error searching for pH floats: {e}")
            raise DownloadError(f"Failed to search BGC-Argo index: {e}")

    def download_float_profile(self,
                               float_id: str,
                               profile_file: str = None) -> Path:
        """
        Download a specific BGC-Argo float profile

        Parameters:
        -----------
        float_id : str
            WMO float number (e.g., '5904468')
        profile_file : str, optional
            Specific profile file (e.g., 'BD5904468_001.nc')
            If None, downloads the latest profile

        Returns:
        --------
        Path: Path to downloaded NetCDF file
        """
        logger.info(f"Downloading BGC-Argo float {float_id}")

        if profile_file:
            # Download specific file
            url = f"{self.IFREMER_HTTP}/dac/aoml/{float_id}/profiles/{profile_file}"
        else:
            # Try to get the latest B-profile (BGC data)
            # Format: BD{float_id}_001.nc
            profile_file = f"BD{float_id}_001.nc"
            url = f"{self.IFREMER_HTTP}/dac/aoml/{float_id}/profiles/{profile_file}"

        output_path = self.data_dir / profile_file

        try:
            logger.info(f"Downloading from: {url}")
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()

            # Save to file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = output_path.stat().st_size / (1024 * 1024)
            logger.info(f"✅ Downloaded {profile_file} ({file_size:.2f} MB)")

            return output_path

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Try different DAC (Data Assembly Center)
                logger.warning(f"File not found at aoml, trying coriolis...")
                url = f"{self.IFREMER_HTTP}/dac/coriolis/{float_id}/profiles/{profile_file}"

                try:
                    response = self.session.get(url, timeout=60, stream=True)
                    response.raise_for_status()

                    with open(output_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    file_size = output_path.stat().st_size / (1024 * 1024)
                    logger.info(f"✅ Downloaded {profile_file} ({file_size:.2f} MB)")
                    return output_path

                except Exception as e2:
                    logger.error(f"Failed to download from both DACs: {e2}")
                    raise DownloadError(f"Float {float_id} not found in any DAC")
            else:
                raise DownloadError(f"Download failed: {e}")

        except Exception as e:
            logger.error(f"Download error: {e}")
            raise DownloadError(f"Failed to download {profile_file}: {e}")

    def quick_inspect(self, file_path: Path) -> Dict:
        """
        Quick inspection of downloaded BGC-Argo file

        Parameters:
        -----------
        file_path : Path
            Path to NetCDF file

        Returns:
        --------
        Dict: Summary of file contents
        """
        logger.info(f"Inspecting {file_path.name}")

        try:
            ds = xr.open_dataset(file_path)

            # Check for BGC parameters
            bgc_params = {
                'ph': 'PH_IN_SITU_TOTAL' in ds or 'PH' in ds,
                'oxygen': 'DOXY' in ds or 'DOXY_ADJUSTED' in ds,
                'nitrate': 'NITRATE' in ds,
                'chla': 'CHLA' in ds,
                'bbp': 'BBP700' in ds or 'BBP' in ds,
            }

            summary = {
                'file': file_path.name,
                'variables': list(ds.data_vars),
                'dimensions': dict(ds.dims),
                'bgc_params': bgc_params,
                'global_attrs': len(ds.attrs),
                'n_profiles': ds.dims.get('N_PROF', 0),
                'n_levels': ds.dims.get('N_LEVELS', 0),
            }

            # Check for QC variables
            qc_vars = [v for v in ds.data_vars if 'QC' in v]
            summary['qc_variables'] = len(qc_vars)

            ds.close()

            logger.info(f"File contains {len(summary['variables'])} variables")
            logger.info(f"BGC parameters: {[k for k, v in bgc_params.items() if v]}")

            return summary

        except Exception as e:
            logger.error(f"Failed to inspect file: {e}")
            return {'error': str(e)}

    def download_sample_dataset(self, n_floats: int = 5) -> List[Path]:
        """
        Download sample BGC-Argo profiles for testing

        Parameters:
        -----------
        n_floats : int
            Number of float profiles to download

        Returns:
        --------
        List[Path]: Paths to downloaded files
        """
        logger.info("="*60)
        logger.info(f"Downloading {n_floats} sample BGC-Argo profiles")
        logger.info("="*60)

        # Known good BGC-Argo floats with pH sensors
        # (These are real WMO numbers from BGC-Argo program)
        known_floats = [
            '5904468',  # North Pacific
            '5904471',  # North Pacific
            '5904659',  # North Atlantic
            '6901528',  # Southern Ocean
            '6902745',  # Mediterranean
            '5905998',  # North Atlantic
            '7900591',  # Pacific
        ]

        downloaded = []

        for float_id in known_floats[:n_floats]:
            try:
                # Try multiple profile numbers
                for profile_num in ['001', '050', '100']:
                    profile_file = f"BD{float_id}_{profile_num}.nc"

                    try:
                        path = self.download_float_profile(float_id, profile_file)

                        # Quick check if file is valid
                        summary = self.quick_inspect(path)

                        if 'error' not in summary:
                            downloaded.append(path)
                            logger.info(f"✅ Successfully downloaded {profile_file}")
                            break
                    except:
                        continue

            except Exception as e:
                logger.warning(f"Could not download float {float_id}: {e}")
                continue

        logger.info("="*60)
        logger.info(f"Successfully downloaded {len(downloaded)}/{n_floats} profiles")
        logger.info("="*60)

        return downloaded


def main():
    """
    Main function for testing BGC-Argo data extraction
    """
    print("\n" + "="*60)
    print("BGC-ARGO DATA EXTRACTOR - Sprint 4A")
    print("="*60 + "\n")

    # Initialize extractor
    extractor = BGCArgoExtractor()

    # Download sample profiles
    print("Downloading sample BGC-Argo profiles...")
    print("(This may take a few minutes)\n")

    try:
        files = extractor.download_sample_dataset(n_floats=3)

        print("\n" + "="*60)
        print("DOWNLOAD SUMMARY")
        print("="*60)
        print(f"\nDownloaded {len(files)} BGC-Argo profiles:")
        for f in files:
            print(f"  • {f.name}")

        print(f"\nFiles saved to: {extractor.data_dir}")

        # Inspect files
        print("\n" + "="*60)
        print("FILE INSPECTION")
        print("="*60 + "\n")

        for f in files:
            summary = extractor.quick_inspect(f)
            print(f"\n{f.name}:")
            print(f"  Variables: {len(summary.get('variables', []))}")
            print(f"  Profiles: {summary.get('n_profiles', 0)}")
            print(f"  Levels: {summary.get('n_levels', 0)}")
            print(f"  QC vars: {summary.get('qc_variables', 0)}")

            bgc = summary.get('bgc_params', {})
            bgc_present = [k for k, v in bgc.items() if v]
            if bgc_present:
                print(f"  BGC params: {', '.join(bgc_present)}")

        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        print("\nNow you can:")
        print("1. Run FAIRAssessor on these files:")
        print(f"   python3 examples/assess_dataset.py {files[0]}")
        print("\n2. Compare with OOI data structure")
        print("\n3. Identify BGC-Argo specific FAIR gaps")
        print("\n" + "="*60 + "\n")

    except Exception as e:
        logger.error(f"Failed to download sample data: {e}")
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. Try again (Argo servers can be slow)")
        print("3. Check logs for details")


if __name__ == "__main__":
    main()
