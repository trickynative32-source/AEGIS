import urllib.parse
import webbrowser
import logging
from typing import Dict, Any, Optional
from backend.tools.registry import registry
from backend.services.location import get_current_location_summary

logger = logging.getLogger("AEGIS.BrowserTools")

@registry.register(
    name="open_website",
    description="Open any website or URL in the default web browser (e.g. YouTube, GitHub, Wikipedia, etc.).",
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to open (e.g. 'https://youtube.com', 'https://github.com')"
            }
        },
        "required": ["url"]
    },
    permission_level="normal",
    category="browser"
)
def open_website(url: str) -> Dict[str, Any]:
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    try:
        webbrowser.open(url)
        return {
            "status": "opened",
            "url": url,
            "message": f"Opened {url} in your browser.",
            "verified": True
        }
    except Exception as e:
        logger.error(f"Failed to open website {url}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "verified": False
        }

@registry.register(
    name="browser_search",
    description="Perform a Google web search in the default web browser.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"
            }
        },
        "required": ["query"]
    },
    permission_level="normal",
    category="browser"
)
def browser_search(query: str) -> Dict[str, Any]:
    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(search_url)
    return {
        "status": "searched",
        "query": query,
        "url": search_url,
        "message": f"Searching Google for '{query}'.",
        "verified": True
    }

@registry.register(
    name="youtube_search",
    description="Search for videos or music on YouTube.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Video or topic to search on YouTube"
            }
        },
        "required": ["query"]
    },
    permission_level="normal",
    category="browser"
)
def youtube_search(query: str) -> Dict[str, Any]:
    encoded = urllib.parse.quote_plus(query)
    yt_url = f"https://www.youtube.com/results?search_query={encoded}"
    webbrowser.open(yt_url)
    return {
        "status": "searched",
        "query": query,
        "url": yt_url,
        "message": f"Searching YouTube for '{query}'.",
        "verified": True
    }

@registry.register(
    name="youtube_play",
    description="Play a specific song, track, or artist on YouTube.",
    parameters={
        "type": "object",
        "properties": {
            "song": {
                "type": "string",
                "description": "Name of the song or artist to play (e.g. 'Believer by Imagine Dragons', 'Tum Hi Ho', 'Relaxing music')"
            }
        },
        "required": ["song"]
    },
    permission_level="normal",
    category="browser"
)
def youtube_play(song: str) -> Dict[str, Any]:
    # Construct clean YouTube search query
    clean_song = song.strip()
    encoded = urllib.parse.quote_plus(clean_song)
    # Direct YouTube search URL
    yt_url = f"https://www.youtube.com/results?search_query={encoded}"
    webbrowser.open(yt_url)
    return {
        "status": "playing",
        "song": clean_song,
        "url": yt_url,
        "message": f"Playing {clean_song} on YouTube.",
        "verified": True
    }

@registry.register(
    name="open_maps",
    description="Open Google Maps and search for a place, city, or landmark.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Place, address, or landmark to show on Google Maps (e.g. 'Bangalore', 'Dayananda Sagar University', 'Bangalore Airport')"
            }
        },
        "required": ["query"]
    },
    permission_level="normal",
    category="browser"
)
def open_maps(query: str) -> Dict[str, Any]:
    encoded = urllib.parse.quote_plus(query)
    maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded}"
    webbrowser.open(maps_url)
    return {
        "status": "opened",
        "place": query,
        "url": maps_url,
        "message": f"Showing {query} on Google Maps.",
        "verified": True
    }

@registry.register(
    name="maps_directions",
    description="Show navigation directions between two locations, or from current location to a destination on Google Maps.",
    parameters={
        "type": "object",
        "properties": {
            "destination": {
                "type": "string",
                "description": "The destination address or landmark (e.g. 'Bangalore Airport', 'Central Station')"
            },
            "origin": {
                "type": "string",
                "description": "Optional starting location. If omitted or 'current location', uses user's current location.",
                "default": "Current Location"
            }
        },
        "required": ["destination"]
    },
    permission_level="normal",
    category="browser"
)
def maps_directions(destination: str, origin: Optional[str] = "Current Location") -> Dict[str, Any]:
    # Check if origin is current location
    if not origin or origin.lower() in ["current location", "my location", "here", "my current location"]:
        user_loc = get_current_location_summary()
        origin_str = user_loc if user_loc else "Current Location"
    else:
        origin_str = origin

    encoded_origin = urllib.parse.quote_plus(origin_str)
    encoded_dest = urllib.parse.quote_plus(destination)
    
    directions_url = f"https://www.google.com/maps/dir/?api=1&origin={encoded_origin}&destination={encoded_dest}"
    webbrowser.open(directions_url)
    
    return {
        "status": "directions_opened",
        "origin": origin_str,
        "destination": destination,
        "url": directions_url,
        "message": f"Showing directions from {origin_str} to {destination} on Google Maps.",
        "verified": True
    }
