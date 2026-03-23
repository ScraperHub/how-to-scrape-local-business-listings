"""Build search URLs for Google Maps, Yelp, and Yellow Pages with geo parameters."""

from urllib.parse import quote_plus, urlencode


def build_google_maps_url(query: str, city: str | None = None) -> str:
    """Build Google Maps search URL with optional city.

    Args:
        query: Search term (e.g., "plumbers", "restaurants").
        city: Optional city for geo-targeting (e.g., "Austin").

    Returns:
        Full Google Maps search URL.
    """
    base = "https://www.google.com/maps/search/"
    q = f"{query} in {city}" if city else query
    params = {"api": "1", "query": q}
    return f"{base}?{urlencode(params)}"


def build_yelp_search_url(term: str, location: str) -> str:
    """Build Yelp search URL with term and location.

    Args:
        term: Search term (e.g., "plumbers").
        location: City or address for local results (e.g., "Austin, TX").

    Returns:
        Full Yelp search URL.
    """
    base = "https://www.yelp.com/search"
    params = {
        "find_desc": term,
        "find_loc": location,
    }
    return f"{base}?{urlencode(params)}"


def build_yellow_pages_url(term: str, location: str) -> str:
    """Build Yellow Pages search URL with term and location.

    Args:
        term: Search term (e.g., "plumbers").
        location: City or zip for local results (e.g., "Austin TX").

    Returns:
        Full Yellow Pages search URL.
    """
    base = "https://www.yellowpages.com/search"
    params = {
        "search_terms": term,
        "geo_location_terms": location,
    }
    return f"{base}?{urlencode(params)}"
