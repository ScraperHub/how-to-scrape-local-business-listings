"""Tests for parser module."""

from pathlib import Path

import pytest

from parser import parse_local_listings

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "maps_listing.html"


def load_fixture() -> str:
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_parse_extracts_names() -> None:
    html = load_fixture()
    items = parse_local_listings(html, source="google_maps")
    assert len(items) >= 2, f"Expected >=2 items, got {len(items)}"
    names = [i["name"] for i in items]
    assert any("Plumbing" in n or "Plumber" in n for n in names), names


def test_parse_extracts_address() -> None:
    html = load_fixture()
    items = parse_local_listings(html, source="google_maps")
    with_addr = [i for i in items if i.get("address")]
    assert len(with_addr) >= 1, f"No items with address: {items}"
    assert "78701" in with_addr[0]["address"] or "Main" in with_addr[0]["address"]


def test_parse_extracts_phone() -> None:
    html = load_fixture()
    items = parse_local_listings(html, source="google_maps")
    with_phone = [i for i in items if i.get("phone")]
    assert len(with_phone) >= 1, f"No items with phone: {items}"
    assert "555" in with_phone[0]["phone"]


def test_parse_extracts_rating() -> None:
    html = load_fixture()
    items = parse_local_listings(html, source="google_maps")
    with_rating = [i for i in items if i.get("rating")]
    assert len(with_rating) >= 1, f"No items with rating: {items}"
    assert with_rating[0]["rating"] in ["4.5", "4.8", "4.2"]


def test_parse_empty_when_no_listings() -> None:
    html = "<html><body><div>No listings</div></body></html>"
    assert parse_local_listings(html, source="google_maps") == []


def test_parse_schema_has_required_fields() -> None:
    html = load_fixture()
    items = parse_local_listings(html, source="google_maps")
    for item in items:
        assert "name" in item
        assert "address" in item
        assert "phone" in item
        assert "hours" in item
        assert "rating" in item
