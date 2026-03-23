"""
CLI entry point for local business listings scraping.

Usage:
    python main.py "plumbers" --cities "Austin" "Denver" -o output.json
    python main.py "restaurants" --cities "Phoenix" --country US --source maps
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_TIMEOUT_SECONDS,
    RETRY_ATTEMPTS,
    RETRY_MAX_WAIT_SECONDS,
    RETRY_MIN_WAIT_SECONDS,
    get_token,
)
from fetcher import fetch_page
from parser import parse_local_listings
from url_builder import build_google_maps_url, build_yelp_search_url

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def scrape_listings(
    query: str,
    *,
    cities: list[str] | None = None,
    country: str | None = None,
    output_path: str = DEFAULT_OUTPUT_PATH,
    page_wait: int = 2000,
    source: str = "maps",
) -> int:
    """Scrape local business listings for query across cities and write to JSON.

    Returns:
        Total number of listings extracted.
    """
    get_token()
    cities = cities or []
    if not cities:
        cities = [""]  # Single query without city

    all_listings = []
    source_key = "google_maps" if source == "maps" else "yelp"

    for city in cities:
        if source == "maps":
            url = build_google_maps_url(query, city or None)
        else:
            url = build_yelp_search_url(query, city or "US")

        @retry(
            stop=stop_after_attempt(RETRY_ATTEMPTS),
            wait=wait_exponential(
                min=RETRY_MIN_WAIT_SECONDS,
                max=RETRY_MAX_WAIT_SECONDS,
            ),
            retry=retry_if_exception_type((ConnectionError,)),
            reraise=True,
        )
        def _fetch() -> str:
            return fetch_page(
                url,
                page_wait=page_wait,
                country=country,
                use_js=True,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )

        try:
            html = _fetch()
        except Exception as e:
            logger.warning("Failed to fetch %s: %s", url, e)
            continue

        items = parse_local_listings(html, source=source_key, source_url=url)
        for item in items:
            item["city"] = city or ""
            all_listings.append(item)

        logger.info("Extracted %d listings for %s in %s", len(items), query, city or "default")

    output = {
        "query": query,
        "cities": cities,
        "country": country,
        "source": source,
        "listings": all_listings,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info("Written %d total listings to %s", len(all_listings), output_path)
    return len(all_listings)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scrape local business listings via Crawlbase Crawling API.",
    )
    parser.add_argument("query", help="Search term (e.g., plumbers, restaurants)")
    parser.add_argument(
        "--cities",
        nargs="*",
        default=[""],
        help="Cities to search (default: single query without city)",
    )
    parser.add_argument(
        "--country",
        default=None,
        help="Country code for geo-targeting (e.g., US)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_PATH,
        help=f"Output JSON path (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--page-wait",
        type=int,
        default=2000,
        help="Milliseconds to wait for dynamic content (default: 2000)",
    )
    parser.add_argument(
        "--source",
        choices=["maps", "yelp"],
        default="maps",
        help="Source: maps (Google Maps) or yelp (default: maps)",
    )
    args = parser.parse_args()

    count = scrape_listings(
        args.query,
        cities=args.cities if args.cities else [""],
        country=args.country,
        output_path=args.output,
        page_wait=args.page_wait,
        source=args.source,
    )
    return 0 if count >= 0 else 1


if __name__ == "__main__":
    sys.exit(main())
