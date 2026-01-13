import os
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging, log_api_request, log_api_response, log_exception
from utils.exceptions import (
    AuthenticationError,
    APIRequestError,
    DataNotReadyError,
    CatalogParseError,
    DownloadError,
    retry_on_failure
)

# Load environment variables
load_dotenv()

# Set up module logger
logger = setup_logging(name=__name__, level='INFO')


class OOIDataExtractor:
    """Extract data from OOI M2M API"""
    
    def __init__(self):
        self.username = os.getenv('OOI_API_USERNAME')
        self.token = os.getenv('OOI_API_TOKEN')
        self.base_url = 'https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv'

        if not self.username or not self.token:
            error_msg = "OOI API credentials not found. Check your .env file"
            logger.error(error_msg)
            raise AuthenticationError(error_msg)

        logger.info("OOIDataExtractor initialized successfully")
        logger.debug(f"Using API endpoint: {self.base_url}")
    
    def request_data(self, array, site, node, method, stream, 
                     start_date, end_date):
        """
        Request data from OOI M2M API
        
        Parameters:
        -----------
        array : str (e.g., 'CE02SHSM')
        site : str (e.g., 'RID27')
        node : str (e.g., '03-CTDBPC000')
        method : str (e.g., 'telemetered')
        stream : str (e.g., 'ctdbp_cdef_dcl_instrument')
        start_date : str (e.g., '2024-01-01T00:00:00.000Z')
        end_date : str (e.g., '2024-12-31T23:59:59.999Z')
        
        Returns:
        --------
        dict with request information
        """
        
        # Build request URL
        url = f"{self.base_url}/{array}/{site}/{node}/{method}/{stream}"

        # Add time parameters
        params = {
            'beginDT': start_date,
            'endDT': end_date,
            'format': 'application/netcdf',
            'include_provenance': 'true',
            'include_annotations': 'true'
        }

        logger.info(f"Requesting data from OOI API")
        logger.debug(f"URL: {url}")
        logger.debug(f"Time range: {start_date} to {end_date}")

        try:
            # Make request with authentication
            response = requests.get(
                url,
                params=params,
                auth=(self.username, self.token),
                timeout=120
            )

            log_api_response(logger, response.status_code, url)

            if response.status_code != 200:
                raise APIRequestError(
                    f"API request failed: {response.text}",
                    status_code=response.status_code,
                    response_text=response.text
                )

            result = response.json()
            logger.info("Data request accepted successfully")

            if 'allURLs' in result and len(result['allURLs']) > 0:
                logger.info(f"Status URL: {result['allURLs'][0]}")
            else:
                logger.warning("No status URL returned in response")

            return result

        except requests.exceptions.Timeout:
            error_msg = f"Request timed out after 120 seconds"
            logger.error(error_msg)
            raise APIRequestError(error_msg)
        except requests.exceptions.RequestException as e:
            log_exception(logger, e, "Network error during API request")
            raise APIRequestError(f"Network error: {str(e)}")
    
    @retry_on_failure(max_attempts=3, delay=2, exceptions=(requests.exceptions.RequestException,))
    def check_status(self, status_url):
        """
        Check if data is ready for download

        Parameters:
        -----------
        status_url : str - THREDDS catalog URL

        Returns:
        --------
        dict with status information or None if not ready
        """
        try:
            # OOI returns a THREDDS catalog URL, not a JSON endpoint
            # We need to check if the catalog page exists (200 = ready)
            response = requests.get(status_url, timeout=30)

            if response.status_code == 200:
                # Catalog exists, data is ready
                logger.debug("Data processing complete - catalog ready")
                return {'status': 'complete', 'catalog_url': status_url}
            elif response.status_code == 404:
                # Still processing
                logger.debug("Data still processing...")
                return {'status': 'processing'}
            else:
                error_msg = f"Unexpected status code: {response.status_code}"
                logger.warning(error_msg)
                raise APIRequestError(error_msg, status_code=response.status_code)

        except requests.exceptions.RequestException as e:
            log_exception(logger, e, "Error checking status")
            raise
    
    def wait_for_data(self, status_url, max_wait=600, check_interval=10):
        """
        Wait for data request to complete

        Parameters:
        -----------
        status_url : str - THREDDS catalog URL
        max_wait : int - maximum seconds to wait
        check_interval : int - seconds between checks

        Returns:
        --------
        list of download URLs when ready
        """
        logger.info(f"Waiting for data preparation (max {max_wait}s)...")

        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            try:
                status = self.check_status(status_url)

                # Check if complete
                if status.get('status') == 'complete':
                    logger.info("Data ready for download!")
                    # Get download URLs from THREDDS catalog
                    return self.parse_thredds_catalog(status['catalog_url'])

                # Wait before checking again
                elapsed = int(time.time() - start_time)
                logger.info(f"[{elapsed}s] Status: processing... checking again in {check_interval}s")
                time.sleep(check_interval)

            except APIRequestError as e:
                logger.warning(f"Error checking status: {e}. Retrying...")
                time.sleep(check_interval)
                continue

        elapsed = int(time.time() - start_time)
        error_msg = f"Data not ready after {elapsed} seconds"
        logger.error(error_msg)
        raise DataNotReadyError(error_msg, status_url=status_url, elapsed_time=elapsed)
    
    def parse_thredds_catalog(self, catalog_url):
        """
        Parse THREDDS catalog to get NetCDF download URLs

        Parameters:
        -----------
        catalog_url : str - THREDDS catalog HTML URL

        Returns:
        --------
        list of NetCDF file URLs
        """
        # Convert HTML catalog URL to XML catalog URL
        xml_catalog_url = catalog_url.replace('catalog.html', 'catalog.xml')

        logger.info(f"Parsing THREDDS catalog")
        logger.debug(f"Catalog URL: {xml_catalog_url}")

        try:
            response = requests.get(xml_catalog_url, timeout=30)
            if response.status_code != 200:
                raise CatalogParseError(
                    f"Failed to get catalog: HTTP {response.status_code}"
                )

            # Parse XML to find NetCDF files
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)

            # Find all dataset elements with .nc files
            # THREDDS namespace
            ns = {'thredds': 'http://www.unidata.ucar.edu/namespaces/thredds/InvCatalog/v1.0'}

            download_urls = []
            base_url = catalog_url.split('/catalog/')[0]

            # Find all datasets
            for dataset in root.findall('.//thredds:dataset[@urlPath]', ns):
                url_path = dataset.get('urlPath')
                if url_path and url_path.endswith('.nc'):
                    # Build full download URL
                    download_url = f"{base_url}/fileServer/{url_path}"
                    download_urls.append(download_url)
                    logger.debug(f"Found dataset: {url_path}")

            # If no datasets found in XML, try alternative parsing
            if not download_urls:
                logger.debug("No datasets found with urlPath, trying alternative parsing")
                # Sometimes files are in nested datasets
                for dataset in root.findall('.//thredds:dataset', ns):
                    name = dataset.get('name', '')
                    if name.endswith('.nc'):
                        # Try to construct URL from catalog structure
                        catalog_path = catalog_url.split('/catalog/')[1].replace('/catalog.html', '')
                        download_url = f"{base_url}/fileServer/{catalog_path}/{name}"
                        download_urls.append(download_url)
                        logger.debug(f"Found nested dataset: {name}")

            if not download_urls:
                logger.warning("No NetCDF files found in catalog")
            else:
                logger.info(f"Found {len(download_urls)} NetCDF file(s)")

            return download_urls

        except ET.ParseError as e:
            log_exception(logger, e, "Failed to parse THREDDS catalog XML")
            raise CatalogParseError(f"XML parse error: {str(e)}")
        except requests.exceptions.RequestException as e:
            log_exception(logger, e, "Network error fetching catalog")
            raise CatalogParseError(f"Network error: {str(e)}")
    
    def download_file(self, url, output_path):
        """
        Download a file from URL

        Parameters:
        -----------
        url : str - download URL
        output_path : str - where to save file
        """
        logger.info(f"Downloading file")
        logger.debug(f"URL: {url}")
        logger.debug(f"Output: {output_path}")

        try:
            response = requests.get(
                url,
                auth=(self.username, self.token),
                stream=True,
                timeout=300
            )

            if response.status_code != 200:
                raise DownloadError(
                    f"Download failed: HTTP {response.status_code}",
                    url=url,
                    status_code=response.status_code
                )

            # Create directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            # Save file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Log progress every 10MB
                        if downloaded % (10 * 1024 * 1024) == 0 or downloaded == total_size:
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100
                                logger.debug(f"Download progress: {percent:.1f}% ({downloaded}/{total_size} bytes)")

            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            logger.info(f"Download complete: {output_path} ({file_size_mb:.2f} MB)")
            return output_path

        except requests.exceptions.Timeout:
            error_msg = "Download timed out after 300 seconds"
            logger.error(error_msg)
            raise DownloadError(error_msg, url=url)
        except requests.exceptions.RequestException as e:
            log_exception(logger, e, "Network error during download")
            raise DownloadError(f"Network error: {str(e)}", url=url)
        except IOError as e:
            log_exception(logger, e, "File system error during download")
            raise DownloadError(f"Failed to write file: {str(e)}", url=url)


def test_extractor():
    """Test the extractor with CE02SHSM CTD data"""

    logger.info("="*60)
    logger.info("Testing OOI Data Extractor")
    logger.info("="*60)

    try:
        extractor = OOIDataExtractor()

        # Request 1 month of data
        result = extractor.request_data(
            array='CE02SHSM',
            site='RID27',
            node='03-CTDBPC000',
            method='telemetered',
            stream='ctdbp_cdef_dcl_instrument',
            start_date='2024-11-01T00:00:00.000Z',
            end_date='2024-11-30T23:59:59.999Z'
        )

        # Get status URL
        status_url = result.get('allURLs', [None])[0]

        if not status_url:
            logger.error("No status URL returned")
            logger.debug(f"Response: {result}")
            return

        # Wait for data
        try:
            download_urls = extractor.wait_for_data(status_url, max_wait=600)
        except DataNotReadyError as e:
            logger.warning(f"Data not ready: {e}")
            logger.info("Data may still be processing. Check the status URL manually:")
            logger.info(f"  {e.status_url}")
            return

        logger.info(f"Found {len(download_urls)} file(s) to download")

        # Download first file as test
        if download_urls:
            output_path = 'data/raw/test_download.nc'
            extractor.download_file(download_urls[0], output_path)

            # Verify it worked
            file_size = os.path.getsize(output_path) / 1024 / 1024
            logger.info("="*60)
            logger.info("Test Complete!")
            logger.info(f"File: {output_path}")
            logger.info(f"Size: {file_size:.2f} MB")
            logger.info("="*60)
        else:
            logger.warning("No download URLs available")

    except AuthenticationError as e:
        logger.error(f"Authentication failed: {e}")
        logger.info("Please check your .env file contains:")
        logger.info("  OOI_API_USERNAME=your_username")
        logger.info("  OOI_API_TOKEN=your_token")
    except APIRequestError as e:
        logger.error(f"API request failed: {e}")
        if e.status_code:
            logger.error(f"HTTP Status: {e.status_code}")
    except CatalogParseError as e:
        logger.error(f"Failed to parse THREDDS catalog: {e}")
    except DownloadError as e:
        logger.error(f"Download failed: {e}")
        if e.url:
            logger.debug(f"URL: {e.url}")
    except Exception as e:
        log_exception(logger, e, "Unexpected error during test")
        raise


if __name__ == "__main__":
    test_extractor()
