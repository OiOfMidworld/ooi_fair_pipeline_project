import requests
from dotenv import load_dotenv
import os
import json

load_dotenv()

username = os.getenv('OOI_API_USERNAME')
token = os.getenv('OOI_API_TOKEN')
base_url = 'https://ooinet.oceanobservatories.org/api/m2m/12576/sensor/inv'

def discover_path():
    """Discover the correct API path for CE02SHSM CTD"""
    
    # Level 1: Arrays
    print("=" * 60)
    print("Level 1: Checking CE02SHSM...")
    url = f"{base_url}/CE02SHSM"
    r = requests.get(url, auth=(username, token))
    if r.status_code == 200:
        sites = r.json()
        print(f"✅ Found {len(sites)} sites:")
        for site in sites:
            print(f"  - {site}")
    else:
        print(f"❌ Failed: {r.status_code}")
        return
    
    # Level 2: Pick RID27
    print("\n" + "=" * 60)
    print("Level 2: Checking CE02SHSM/RID27...")
    url = f"{base_url}/CE02SHSM/RID27"
    r = requests.get(url, auth=(username, token))
    if r.status_code == 200:
        nodes = r.json()
        print(f"✅ Found {len(nodes)} nodes:")
        for node in nodes:
            print(f"  - {node}")
    else:
        print(f"❌ Failed: {r.status_code}")
        return
    
    # Level 3: Pick CTD
    print("\n" + "=" * 60)
    print("Level 3: Checking CE02SHSM/RID27/03-CTDBPC000...")
    url = f"{base_url}/CE02SHSM/RID27/03-CTDBPC000"
    r = requests.get(url, auth=(username, token))
    if r.status_code == 200:
        instruments = r.json()
        print(f"✅ Found {len(instruments)} instruments:")
        for inst in instruments:
            print(f"  - {inst}")
    else:
        print(f"❌ Failed: {r.status_code}")
        return
    
    # Level 4: Check telemetered
    print("\n" + "=" * 60)
    print("Level 4: Checking CE02SHSM/RID27/03-CTDBPC000/telemetered...")
    url = f"{base_url}/CE02SHSM/RID27/03-CTDBPC000/telemetered"
    r = requests.get(url, auth=(username, token))
    if r.status_code == 200:
        streams = r.json()
        print(f"✅ Found {len(streams)} streams:")
        for stream in streams:
            print(f"  - {stream}")
    else:
        print(f"❌ Failed: {r.status_code}")
        return
    
    print("\n" + "=" * 60)
    print("🎯 Use the stream name from above in your data request!")

if __name__ == "__main__":
    discover_path()