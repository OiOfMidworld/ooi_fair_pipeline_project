import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()


class OOIDataExtractor:
    """Extract data from OOI M2M API"""
    
    def __init__(self):
        self.username = os.getenv('OOI_API_USERNAME')
        self.token = os.getenv('OOI_API_TOKEN')
        self.base_url = 'https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv'
        
        if not self.username or not self.token:
            raise ValueError("OOI API credentials not found. Check your .env file")
    
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
        
        print(f"Requesting data from: {url}")
        print(f"Time range: {start_date} to {end_date}")
        
        # Make request with authentication
        response = requests.get(
            url,
            params=params,
            auth=(self.username, self.token),
            timeout=120
        )
        
        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")
        
        result = response.json()
        print(f"✅ Request accepted!")
        
        if 'allURLs' in result and len(result['allURLs']) > 0:
            print(f"Status URL: {result['allURLs'][0]}")
        
        return result
    
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
        # OOI returns a THREDDS catalog URL, not a JSON endpoint
        # We need to check if the catalog page exists (200 = ready)
        response = requests.get(status_url)
        
        if response.status_code == 200:
            # Catalog exists, data is ready
            return {'status': 'complete', 'catalog_url': status_url}
        elif response.status_code == 404:
            # Still processing
            return {'status': 'processing'}
        else:
            raise Exception(f"Unexpected status: {response.status_code}")
    
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
        print(f"Waiting for data preparation (max {max_wait}s)...")
        
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait:
            status = self.check_status(status_url)
            
            # Check if complete
            if status.get('status') == 'complete':
                print("✅ Data ready for download!")
                # Get download URLs from THREDDS catalog
                return self.parse_thredds_catalog(status['catalog_url'])
            
            # Wait before checking again
            elapsed = int(time.time() - start_time)
            print(f"  [{elapsed}s] Status: processing... checking again in {check_interval}s")
            time.sleep(check_interval)
        
        raise TimeoutError(f"Data not ready after {max_wait} seconds")
    
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
        
        print(f"Parsing catalog: {xml_catalog_url}")
        
        response = requests.get(xml_catalog_url)
        if response.status_code != 200:
            raise Exception(f"Failed to get catalog: {response.status_code}")
        
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
        
        # If no datasets found in XML, try alternative parsing
        if not download_urls:
            # Sometimes files are in nested datasets
            for dataset in root.findall('.//thredds:dataset', ns):
                name = dataset.get('name', '')
                if name.endswith('.nc'):
                    # Try to construct URL from catalog structure
                    catalog_path = catalog_url.split('/catalog/')[1].replace('/catalog.html', '')
                    download_url = f"{base_url}/fileServer/{catalog_path}/{name}"
                    download_urls.append(download_url)
        
        print(f"Found {len(download_urls)} NetCDF files")
        
        return download_urls
    
    def download_file(self, url, output_path):
        """
        Download a file from URL
        
        Parameters:
        -----------
        url : str - download URL
        output_path : str - where to save file
        """
        print(f"Downloading: {url}")
        
        response = requests.get(url, auth=(self.username, self.token), stream=True)
        
        if response.status_code != 200:
            raise Exception(f"Download failed: {response.status_code}")
        
        # Create directory if needed
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ Saved to: {output_path}")
        return output_path


def test_extractor():
    """Test the extractor with CE02SHSM CTD data"""
    
    print("="*60)
    print("Testing OOI Data Extractor")
    print("="*60)
    
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
        print("❌ No status URL returned")
        print("Response:", result)
        return
    
    # Wait for data
    try:
        download_urls = extractor.wait_for_data(status_url, max_wait=600)
    except TimeoutError as e:
        print(f"⚠️ {e}")
        print("Data may still be processing. Check the status URL manually:")
        print(status_url)
        return
    
    print(f"\n📥 Found {len(download_urls)} files to download")
    
    # Download first file as test
    if download_urls:
        output_path = 'data/raw/test_download.nc'
        extractor.download_file(download_urls[0], output_path)
        
        # Verify it worked
        file_size = os.path.getsize(output_path) / 1024 / 1024
        print(f"\n✅ Download complete!")
        print(f"File: {output_path}")
        print(f"Size: {file_size:.2f} MB")
    else:
        print("❌ No download URLs available")


if __name__ == "__main__":
    test_extractor()
