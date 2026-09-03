import urllib.parse
import webbrowser
import logging
import datetime
import dateparser
from typing import Dict, Any, Optional, Tuple
from backend.tools.registry import registry
from backend.services.location import get_current_location_summary
from backend.database import SessionLocal
from backend.models import Memory, UserProfile

logger = logging.getLogger("AEGIS.FlightTools")

# Comprehensive mapping of common city names / nicknames to 3-letter IATA airport codes
IATA_AIRPORT_CODES: Dict[str, str] = {
    # Major Indian Hubs
    "bengaluru": "BLR",
    "bangalore": "BLR",
    "blr": "BLR",
    "delhi": "DEL",
    "new delhi": "DEL",
    "del": "DEL",
    "mumbai": "BOM",
    "bombay": "BOM",
    "bom": "BOM",
    "chennai": "MAA",
    "madras": "MAA",
    "maa": "MAA",
    "kolkata": "CCU",
    "calcutta": "CCU",
    "ccu": "CCU",
    "hyderabad": "HYD",
    "hyd": "HYD",
    "pune": "PNQ",
    "pnq": "PNQ",
    "goa": "GOI",
    "goi": "GOI",
    "dabolim": "GOI",
    "mopa": "GOX",
    "ahmedabad": "AMD",
    "amd": "AMD",
    "kochi": "COK",
    "cochin": "COK",
    "cok": "COK",
    "jaipur": "JAI",
    "jai": "JAI",
    "lucknow": "LKO",
    "lko": "LKO",
    "guwahati": "GAU",
    "gau": "GAU",
    "chandigarh": "IXC",
    "ixc": "IXC",
    "bhubaneswar": "BBI",
    "bbi": "BBI",
    "patna": "PAT",
    "pat": "PAT",
    "varanasi": "VNS",
    "vns": "VNS",
    "amritsar": "ATQ",
    "atq": "ATQ",
    "trivandrum": "TRV",
    "thiruvananthapuram": "TRV",
    "trv": "TRV",
    "indore": "IDR",
    "idr": "IDR",
    "bhopal": "BHO",
    "bho": "BHO",
    "nagpur": "NAG",
    "nag": "NAG",
    "srinagar": "SXR",
    "sxr": "SXR",
    "ranchi": "IXR",
    "ixr": "IXR",
    "coimbatore": "CJB",
    "cjb": "CJB",
    "visakhapatnam": "VTZ",
    "vizag": "VTZ",
    "vtz": "VTZ",
    "surat": "STV",
    "stv": "STV",
    "mangalore": "IXE",
    "ixe": "IXE",

    # Major International Hubs
    "dubai": "DXB",
    "dxb": "DXB",
    "singapore": "SIN",
    "sin": "SIN",
    "london": "LHR",
    "heathrow": "LHR",
    "lhr": "LHR",
    "new york": "JFK",
    "jfk": "JFK",
    "nyc": "JFK",
    "san francisco": "SFO",
    "sfo": "SFO",
    "paris": "CDG",
    "cdg": "CDG",
    "tokyo": "HND",
    "hnd": "HND",
    "sydney": "SYD",
    "syd": "SYD",
    "bangkok": "BKK",
    "bkk": "BKK",
    "kuala lumpur": "KUL",
    "kul": "KUL",
    "doha": "DOH",
    "doh": "DOH",
    "toronto": "YYZ",
    "yyz": "YYZ",
    "chicago": "ORD",
    "ord": "ORD",
    "los angeles": "LAX",
    "lax": "LAX",
    "frankfurt": "FRA",
    "fra": "FRA",
    "amsterdam": "AMS",
    "ams": "AMS",
}

def get_airport_code(location_name: str) -> Optional[str]:
    """Retrieve 3-letter IATA code if recognized, otherwise None."""
    clean = location_name.strip().lower()
    if clean in IATA_AIRPORT_CODES:
        return IATA_AIRPORT_CODES[clean]
    for key, code in IATA_AIRPORT_CODES.items():
        if key in clean or clean in key:
            return code
    return None

def resolve_user_location() -> str:
    """
    Resolves the user's origin city in order of priority:
    1. Memory table (key='user_location')
    2. UserProfile table (location column)
    3. IP-based location summary
    4. Default fallback ('Bengaluru')
    """
    db = SessionLocal()
    try:
        mem = db.query(Memory).filter(Memory.key == "user_location").first()
        if mem and mem.value and mem.value.strip():
            city = mem.value.split(",")[0].strip()
            if city:
                return city

        profile = db.query(UserProfile).first()
        if profile and profile.location and profile.location.strip():
            city = profile.location.split(",")[0].strip()
            if city:
                return city
    except Exception as e:
        logger.debug(f"Error reading location from database: {e}")
    finally:
        db.close()

    loc_summary = get_current_location_summary()
    if loc_summary and loc_summary != "Current Location":
        city = loc_summary.split(",")[0].strip()
        if city:
            return city

    return "Bengaluru"

def parse_flight_date(date_str: Optional[str]) -> Tuple[datetime.date, str, str, str]:
    """
    Parses natural language date strings into:
    - datetime.date object
    - ISO format: YYYY-MM-DD
    - Indian/UK format: DD/MM/YYYY
    - Skyscanner format: YYMMDD
    """
    now = datetime.datetime.now()
    clean = (date_str or "").strip().lower()

    if not clean or clean in ["tomorrow", "tmrw"]:
        target_date = (now + datetime.timedelta(days=1)).date()
    elif clean in ["today", "tonight"]:
        target_date = now.date()
    elif clean in ["day after tomorrow", "overmorrow"]:
        target_date = (now + datetime.timedelta(days=2)).date()
    elif clean in ["next week"]:
        target_date = (now + datetime.timedelta(days=7)).date()
    else:
        parsed = dateparser.parse(
            clean,
            settings={
                'RELATIVE_BASE': now,
                'PREFER_DATES_FROM': 'future',
                'DATE_ORDER': 'DMY'
            }
        )
        if parsed:
            if parsed.date() < now.date():
                parsed = parsed.replace(year=now.year + 1)
            target_date = parsed.date()
        else:
            target_date = (now + datetime.timedelta(days=1)).date()

    iso_date = target_date.strftime("%Y-%m-%d")
    ddmmyyyy = target_date.strftime("%d/%m/%Y")
    yymmdd = target_date.strftime("%y%m%d")

    return target_date, iso_date, ddmmyyyy, yymmdd

def build_flight_url(
    origin: str,
    destination: str,
    date_str: Optional[str] = None,
    site: str = "google_flights"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Builds a pre-filled flight booking URL for the requested portal.
    Returns: (prefilled_url, portal_display_name, booking_metadata)
    """
    target_date, iso_date, ddmmyyyy, yymmdd = parse_flight_date(date_str)
    origin_code = get_airport_code(origin) or origin[:3].upper()
    dest_code = get_airport_code(destination) or destination[:3].upper()

    site_normalized = site.lower().replace(" ", "").replace("_", "").replace("-", "")

    metadata = {
        "origin": origin,
        "origin_code": origin_code,
        "destination": destination,
        "dest_code": dest_code,
        "date": target_date.strftime("%b %d, %Y"),
        "iso_date": iso_date,
        "ddmmyyyy": ddmmyyyy
    }

    # 1. MakeMyTrip
    if "makemytrip" in site_normalized or "mmt" in site_normalized:
        portal_name = "MakeMyTrip"
        url = (
            f"https://www.makemytrip.com/flight/search?"
            f"itinerary={origin_code}-{dest_code}-{ddmmyyyy}"
            f"&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
        )

    # 2. Skyscanner
    elif "skyscanner" in site_normalized:
        portal_name = "Skyscanner"
        url = (
            f"https://www.skyscanner.co.in/transport/flights/"
            f"{origin_code.lower()}/{dest_code.lower()}/{yymmdd}/"
        )

    # 3. Expedia
    elif "expedia" in site_normalized:
        portal_name = "Expedia"
        encoded_origin = urllib.parse.quote_plus(origin)
        encoded_dest = urllib.parse.quote_plus(destination)
        url = (
            f"https://www.expedia.co.in/Flights-Search?flight-type=on&mode=search&trip=oneway"
            f"&leg1=from:{encoded_origin},to:{encoded_dest},departure:{ddmmyyyy}TANYT"
            f"&passengers=adults:1"
        )

    # 4. Cleartrip
    elif "cleartrip" in site_normalized:
        portal_name = "Cleartrip"
        url = (
            f"https://www.cleartrip.com/flights/results?"
            f"from={origin_code}&to={dest_code}&depart_date={ddmmyyyy}"
            f"&adults=1&childs=0&infants=0&class=Economy"
        )

    # 5. Kayak
    elif "kayak" in site_normalized:
        portal_name = "Kayak"
        url = f"https://www.kayak.co.in/flights/{origin_code}-{dest_code}/{iso_date}"

    # 6. Google Flights (Default & highly reliable)
    else:
        portal_name = "Google Flights"
        query_str = f"flights from {origin} to {destination} on {iso_date}"
        encoded_query = urllib.parse.quote_plus(query_str)
        url = f"https://www.google.com/travel/flights?q={encoded_query}"

    metadata["site"] = portal_name
    metadata["url"] = url

    return url, portal_name, metadata

@registry.register(
    name="book_flight_tickets",
    description="Book a flight ticket with origin, destination, travel date, and preferred booking portal automatically prefilled.",
    parameters={
        "type": "object",
        "properties": {
            "origin": {
                "type": "string",
                "description": "Departure city or airport (e.g. 'Bengaluru', 'BLR', 'Delhi', 'Current Location')"
            },
            "destination": {
                "type": "string",
                "description": "Arrival city or airport (e.g. 'Delhi', 'Mumbai', 'London', 'Dubai')"
            },
            "date": {
                "type": "string",
                "description": "Departure date (e.g. 'tomorrow', 'Friday', 'next Monday', '2026-09-15')"
            },
            "preferred_site": {
                "type": "string",
                "description": "Preferred booking portal: 'Google Flights', 'MakeMyTrip', 'Skyscanner', 'Expedia', 'Cleartrip', or 'Kayak'",
                "default": "Google Flights"
            }
        },
        "required": ["destination"]
    },
    permission_level="normal",
    category="browser"
)
def book_flight_tickets(
    destination: str,
    origin: Optional[str] = None,
    date: Optional[str] = "tomorrow",
    preferred_site: Optional[str] = "Google Flights"
) -> Dict[str, Any]:
    """Executes flight redirection and opens the pre-filled portal."""
    if not origin or origin.lower() in ["current location", "my location", "my given location", "here", "given location"]:
        clean_origin = resolve_user_location()
    else:
        clean_origin = origin.strip()

    clean_dest = destination.strip()
    clean_site = preferred_site or "Google Flights"

    url, portal_name, metadata = build_flight_url(
        origin=clean_origin,
        destination=clean_dest,
        date_str=date,
        site=clean_site
    )

    try:
        webbrowser.open(url)
        opened = True
    except Exception as e:
        logger.warning(f"Could not open browser for flights: {e}")
        opened = False

    message = (
        f"Redirecting you to {portal_name} for flights from {clean_origin} "
        f"({metadata['origin_code']}) to {clean_dest} ({metadata['dest_code']}) "
        f"on {metadata['date']}."
    )

    return {
        "status": "redirecting",
        "action": "open_url",
        "url": url,
        "portal": portal_name,
        "booking_data": metadata,
        "message": message,
        "verified": True,
        "opened_in_browser": opened
    }
