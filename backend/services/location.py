import logging
import requests
from typing import Optional, Dict, Any
from backend.config import settings

logger = logging.getLogger("AEGIS.Location")

_cached_location: Optional[Dict[str, Any]] = None

def get_current_location_data() -> Optional[Dict[str, Any]]:
    global _cached_location
    if not settings.LOCATION_ENABLED:
        logger.info("Location access is disabled in settings.")
        return None

    if _cached_location:
        return _cached_location

    # Try IP-based geolocation
    try:
        resp = requests.get("https://ipapi.co/json/", timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            _cached_location = {
                "city": data.get("city"),
                "region": data.get("region"),
                "country": data.get("country_name"),
                "lat": data.get("latitude"),
                "lon": data.get("longitude"),
                "summary": f"{data.get('city')}, {data.get('region')}, {data.get('country_name')}"
            }
            return _cached_location
    except Exception as e:
        logger.warning(f"Could not retrieve location via IP: {e}")

    return None

def get_current_location_summary() -> str:
    data = get_current_location_data()
    if data and data.get("summary"):
        return data["summary"]
    return "Current Location"
