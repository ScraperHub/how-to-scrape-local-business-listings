"""Parse local business listings from Google Maps, Yelp, and directory HTML."""

import logging
import re
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

LISTING_ITEM = dict[str, Any]


def parse_local_listings(
    html: str,
    source: str = "google_maps",
    source_url: str = "",
) -> list[LISTING_ITEM]:
    """Extract local business listings from HTML.

    Uses layered fallback selectors because Google Maps, Yelp, and directories
    frequently change DOM structure.

    Args:
        html: Raw HTML from the search results page.
        source: One of "google_maps", "yelp", "yellow_pages".
        source_url: URL of the search (for reference).

    Returns:
        List of dicts: {name, address, phone, hours, rating}
    """
    if source == "google_maps":
        return _parse_google_maps(html, source_url)
    if source == "yelp":
        return _parse_yelp(html, source_url)
    if source == "yellow_pages":
        return _parse_yellow_pages(html, source_url)
    logger.warning("Unknown source %s, defaulting to google_maps", source)
    return _parse_google_maps(html, source_url)


def _parse_google_maps(html: str, source_url: str) -> list[LISTING_ITEM]:
    """Parse Google Maps search results HTML."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[LISTING_ITEM] = []

    # Container selectors (layered fallbacks - Google changes these)
    container_selectors = [
        "[data-result-index]",
        ".section-result",
        "div[role='feed'] > div",
        "a[href*='/maps/place/']",
        ".Nv2PK",
    ]

    containers = []
    for sel in container_selectors:
        found = soup.select(sel)
        if found and len(found) > 2:
            containers = found
            break

    # Name selectors
    name_selectors = [
        "span[role='heading']",
        ".fontHeadline",
        ".fontHeadlineSmall",
        ".qBF1Pd",
        "[data-tooltip]",
    ]

    for container in containers:
        name = _extract_with_selectors(container, name_selectors)
        if not name or len(name) < 2:
            continue

        item: LISTING_ITEM = {
            "name": name,
            "address": _extract_address(container),
            "phone": _extract_phone(container),
            "hours": _extract_hours(container),
            "rating": _extract_rating(container),
            "source_url": source_url,
        }
        results.append(item)

    return results


def _parse_yelp(html: str, source_url: str) -> list[LISTING_ITEM]:
    """Parse Yelp search results HTML."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[LISTING_ITEM] = []

    containers = soup.select(
        "div[data-testid='serp-ia-card'], "
        "a[href*='/biz/'], "
        ".container__09f24__mpR5_"
    )

    for container in containers:
        name = _extract_with_selectors(
            container,
            ["h3", "a[href*='/biz/']", ".css-1egoivc", "[role='link']"],
        )
        if not name or len(name) < 2:
            continue

        item: LISTING_ITEM = {
            "name": name,
            "address": _extract_address(container),
            "phone": _extract_phone(container),
            "hours": _extract_hours(container),
            "rating": _extract_rating(container),
            "source_url": source_url,
        }
        results.append(item)

    return results


def _parse_yellow_pages(html: str, source_url: str) -> list[LISTING_ITEM]:
    """Parse Yellow Pages search results HTML."""
    soup = BeautifulSoup(html, "html.parser")
    results: list[LISTING_ITEM] = []

    containers = soup.select(
        ".result, "
        ".search-result, "
        "div[data-listing-id]"
    )

    for container in containers:
        name = _extract_with_selectors(
            container,
            [".business-name", "a.listing-name", "h2", ".n"],
        )
        if not name or len(name) < 2:
            continue

        item: LISTING_ITEM = {
            "name": name,
            "address": _extract_address(container),
            "phone": _extract_phone(container),
            "hours": _extract_hours(container),
            "rating": _extract_rating(container),
            "source_url": source_url,
        }
        results.append(item)

    return results


def _extract_with_selectors(container, selectors: list[str]) -> str:
    """Try each selector until one returns non-empty text."""
    for sel in selectors:
        el = container.select_one(sel)
        if el:
            text = el.get_text(separator=" ", strip=True)
            if text:
                return text
    return ""


def _extract_address(container) -> str:
    """Extract address from listing container."""
    # Google Maps often uses aria-label or address-like text
    addr_selectors = [
        "[data-item-id='address']",
        ".rogA2c",
        ".fontBodyMedium",
        "span[aria-label*='Address']",
        ".address",
    ]
    for sel in addr_selectors:
        el = container.select_one(sel)
        if el:
            text = el.get_text(separator=" ", strip=True)
            if text and re.search(r"\d+", text):
                return text
    return ""


def _extract_phone(container) -> str:
    """Extract phone from listing container."""
    # Look for tel: links or phone-like patterns
    tel = container.select_one("a[href^='tel:']")
    if tel:
        return tel.get("href", "").replace("tel:", "").strip()
    text = container.get_text()
    match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    return match.group(0) if match else ""


def _extract_hours(container) -> str:
    """Extract hours from listing container."""
    hours_selectors = [
        "[data-item-id='oh']",
        "[aria-label*='Hours']",
        ".Open",
        ".hours",
    ]
    for sel in hours_selectors:
        el = container.select_one(sel)
        if el:
            return el.get_text(separator=" ", strip=True)
    return ""


def _extract_rating(container) -> str:
    """Extract rating from listing container."""
    # Google uses aria-label like "4.5 stars"
    rating_el = container.select_one("[aria-label*='star'], .ZkP5Je, .rating")
    if rating_el:
        aria = rating_el.get("aria-label", "")
        match = re.search(r"[\d.]+", aria or rating_el.get_text())
        if match:
            return match.group(0)
    return ""
