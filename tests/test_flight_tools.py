import pytest
import datetime
from backend.tools.flight_tools import (
    get_airport_code,
    parse_flight_date,
    build_flight_url,
    book_flight_tickets,
    resolve_user_location
)
from backend.agent.router import FastDeterministicRouter

def test_airport_codes():
    assert get_airport_code("Bengaluru") == "BLR"
    assert get_airport_code("Bangalore") == "BLR"
    assert get_airport_code("Delhi") == "DEL"
    assert get_airport_code("Mumbai") == "BOM"
    assert get_airport_code("Goa") in ["GOI", "GOX"]
    assert get_airport_code("Dubai") == "DXB"
    assert get_airport_code("London") == "LHR"
    assert get_airport_code("New York") == "JFK"

def test_parse_flight_date():
    now = datetime.datetime.now()
    tomorrow = (now + datetime.timedelta(days=1)).date()
    
    t_date, iso, ddmmyyyy, yymmdd = parse_flight_date("tomorrow")
    assert t_date == tomorrow
    assert iso == tomorrow.strftime("%Y-%m-%d")
    assert ddmmyyyy == tomorrow.strftime("%d/%m/%Y")

def test_build_flight_url_google():
    url, portal, meta = build_flight_url("Bengaluru", "Delhi", "tomorrow", "Google Flights")
    assert portal == "Google Flights"
    assert "google.com/travel/flights" in url
    assert "Bengaluru" in url or "BLR" in url
    assert "Delhi" in url

def test_build_flight_url_makemytrip():
    url, portal, meta = build_flight_url("Bengaluru", "Delhi", "tomorrow", "MakeMyTrip")
    assert portal == "MakeMyTrip"
    assert "makemytrip.com/flight/search" in url
    assert "BLR-DEL" in url

def test_build_flight_url_skyscanner():
    url, portal, meta = build_flight_url("Bengaluru", "Delhi", "tomorrow", "Skyscanner")
    assert portal == "Skyscanner"
    assert "skyscanner" in url
    assert "blr/del" in url

def test_build_flight_url_expedia():
    url, portal, meta = build_flight_url("Bengaluru", "Delhi", "tomorrow", "Expedia")
    assert portal == "Expedia"
    assert "expedia" in url
    assert "Bengaluru" in url
    assert "Delhi" in url

def test_book_flight_tickets_tool():
    res = book_flight_tickets("Delhi", origin="Bengaluru", date="tomorrow", preferred_site="MakeMyTrip")
    assert res["status"] == "redirecting"
    assert res["action"] == "open_url"
    assert "makemytrip.com" in res["url"]
    assert res["booking_data"]["origin_code"] == "BLR"
    assert res["booking_data"]["dest_code"] == "DEL"

@pytest.mark.asyncio
async def test_router_flight_multi_turn():
    router = FastDeterministicRouter()

    # Step 1: User says "Book a flight ticket from my given location"
    res1 = await router.route_and_execute("Book a flight ticket from my given location")
    assert res1 is not None
    assert "Where would you like to fly to" in res1["response"]
    assert res1["pending_flight"]["step"] == "awaiting_destination_date"

    # Step 2: User responds "To Delhi tomorrow"
    res2 = await router.route_and_execute("To Delhi tomorrow")
    assert res2 is not None
    assert "From which booking site" in res2["response"]
    assert res2["pending_flight"]["step"] == "awaiting_site"
    assert res2["pending_flight"]["destination"] == "Delhi"

    # Step 3: User says "MakeMyTrip"
    res3 = await router.route_and_execute("MakeMyTrip")
    assert res3 is not None
    assert res3["action"] == "open_url"
    assert "makemytrip.com" in res3["url"]
    assert "-DEL" in res3["url"]

@pytest.mark.asyncio
async def test_router_flight_one_shot():
    router = FastDeterministicRouter()
    res = await router.route_and_execute("Book a flight ticket from my given location to Delhi tomorrow on MakeMyTrip")
    assert res is not None
    assert res["action"] == "open_url"
    assert "makemytrip.com" in res["url"]
    assert "-DEL" in res["url"]
