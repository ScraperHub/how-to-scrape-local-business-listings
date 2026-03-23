"""Tests for main module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from main import scrape_listings
from url_builder import build_google_maps_url, build_yelp_search_url

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "maps_listing.html"


def load_fixture() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_build_google_maps_url_with_city() -> None:
    url = build_google_maps_url("plumbers", "Austin")
    assert "plumbers" in url and "Austin" in url
    assert "google.com/maps/search" in url
    assert "api=1" in url


def test_build_google_maps_url_without_city() -> None:
    url = build_google_maps_url("restaurants")
    assert "restaurants" in url
    assert "google.com/maps/search" in url


def test_build_yelp_search_url() -> None:
    url = build_yelp_search_url("plumbers", "Austin, TX")
    assert "plumbers" in url
    assert "Austin" in url
    assert "yelp.com/search" in url


def test_scrape_listings_mocked() -> None:
    html = load_fixture()
    with patch("main.fetch_page", return_value=html):
        with patch("main.get_token", return_value="mock"):
            count = scrape_listings(
                "plumbers",
                cities=["Austin"],
                output_path="/tmp/test_listings_output.json",
            )
    assert count >= 2, f"Expected >=2, got {count}"
    data = json.loads(Path("/tmp/test_listings_output.json").read_text())
    assert data["query"] == "plumbers"
    assert data["cities"] == ["Austin"]
    assert len(data["listings"]) >= 2
    Path("/tmp/test_listings_output.json").unlink(missing_ok=True)
