#!/usr/bin/env python3
"""Simple test runner when pytest is not available. Run: python3 run_tests.py"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from main import scrape_listings
from parser import parse_local_listings
from url_builder import build_google_maps_url, build_yelp_search_url

FIXTURE_PATH = Path(__file__).parent / "tests" / "fixtures" / "maps_listing.html"


def load_fixture() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_parse_extracts_names() -> None:
    html = load_fixture()
    items = parse_local_listings(html, source="google_maps")
    assert len(items) >= 2, f"Expected >=2 items, got {len(items)}"
    names = [i["name"] for i in items]
    assert any("Plumbing" in n or "Plumber" in n for n in names), names


def test_parse_empty_when_no_listings() -> None:
    html = "<html><body><div>No listings</div></body></html>"
    assert parse_local_listings(html, source="google_maps") == []


def test_build_google_maps_url() -> None:
    url = build_google_maps_url("plumbers", "Austin")
    assert "plumbers" in url and "Austin" in url
    assert "google.com/maps/search" in url


def test_build_yelp_search_url() -> None:
    url = build_yelp_search_url("plumbers", "Austin, TX")
    assert "plumbers" in url and "Austin" in url


def test_scrape_listings_mocked() -> None:
    html = load_fixture()
    out_path = "/tmp/test_listings_run.json"
    with patch("main.fetch_page", return_value=html):
        with patch("main.get_token", return_value="mock"):
            count = scrape_listings("plumbers", cities=["Austin"], output_path=out_path)
    assert count >= 2
    data = json.loads(Path(out_path).read_text())
    assert data["query"] == "plumbers" and len(data["listings"]) >= 2
    Path(out_path).unlink(missing_ok=True)


TESTS = [
    ("parse_extracts_names", test_parse_extracts_names),
    ("parse_empty_no_listings", test_parse_empty_when_no_listings),
    ("build_google_maps_url", test_build_google_maps_url),
    ("build_yelp_search_url", test_build_yelp_search_url),
    ("scrape_listings_mocked", test_scrape_listings_mocked),
]


def main() -> int:
    failed = 0
    for name, fn in TESTS:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as e:
            print(f"FAIL {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {name}: {e}")
            failed += 1
    print(f"\n{failed} failed, {len(TESTS) - failed} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
