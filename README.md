# Local Business Listings Scraper

Scrapes local business listings (Google Maps, Yelp) via the [Crawlbase Crawling API](https://crawlbase.com/docs/crawling-api/), parses name, address, phone, hours, and rating, and writes JSON. Supports multi-city geo-targeting and the [Enterprise Crawler](https://crawlbase.com/docs/crawler) for bulk scale.

Matches the blog post *How to Scrape Local Business Listings*.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
export CRAWLBASE_TOKEN=your_normal_token
export CRAWLBASE_JS_TOKEN=your_js_token   # Required for Google Maps and Yelp
```

Tokens are required; set `CRAWLBASE_TOKEN` and `CRAWLBASE_JS_TOKEN` in your environment (see `config.py`).

## Run

```bash
# Scrape plumbers in Austin (Google Maps)
python main.py "plumbers" --cities "Austin" -o output.json

# Multiple cities
python main.py "restaurants" --cities "Austin" "Denver" "Phoenix" -o listings.json

# With country geo-targeting
python main.py "electricians" --cities "London" --country UK

# Yelp instead of Google Maps
python main.py "plumbers" --cities "Austin" --source yelp
```

## Layout

- **config.py** — Env-based tokens (required), API base, timeouts, retries.
- **fetcher.py** — Crawlbase Crawling API client; `fetch_page()`, `fetch_page_enterprise_crawler()`.
- **url_builder.py** — `build_google_maps_url()`, `build_yelp_search_url()`, `build_yellow_pages_url()`.
- **parser.py** — `parse_local_listings()` with layered fallback selectors.
- **main.py** — CLI; builds URLs, fetches via Crawlbase, parses, writes JSON.

Output is JSON: `{query, cities, country, source, listings: [{name, address, phone, hours, rating, city}]}`.

## Tests

```bash
python3 run_tests.py
```

Or with pytest:

```bash
python3 -m pytest tests/ -v
```
