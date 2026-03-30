import sys
import os
from pathlib import Path

# Add backend to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.xml_pipeline import XMLPipelineService
import logging

logging.basicConfig(level=logging.INFO)

def main():
    pipeline = XMLPipelineService(xslt_dir="transforms", cache_dir="backend/.cache")
    
    print("=== Testing USGS XML Pipeline ===")
    try:
        # Fetch last 24 hours, min mag 5.0
        events = pipeline.get_earthquakes(source="USGS", min_mag=5.0)
        print(f"Successfully fetched {len(events)} events from USGS.")
        if events:
            print(f"Top event: {events[0].title} (Mag: {events[0].magnitude})")
            print(f"Canonical XML saved to: backend/.cache/canonical/usgs_latest.xml")
    except Exception as e:
        print(f"USGS Pipeline failed: {e}")

    print("\n=== Testing GDACS XML Pipeline ===")
    try:
        events = pipeline.get_earthquakes(source="GDACS")
        print(f"Successfully fetched {len(events)} events from GDACS.")
        if events:
            print(f"Top event: {events[0].title} (Mag: {events[0].magnitude})")
            print(f"Canonical XML saved to: backend/.cache/canonical/gdacs_latest.xml")
    except Exception as e:
        print(f"GDACS Pipeline failed: {e}")

if __name__ == "__main__":
    main()
