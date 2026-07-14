#!/usr/bin/env python3
"""
Creek Pressure Washing — Property Manager Scraper (Cowley County, KS)
Uses Apify Google Maps Scraper to pull property managers from Winfield,
Arkansas City, Wellington, and Cowley County area.

Output: outreach/data/property-managers-YYYY-MM-DD.csv

Run:
  python scrape_property_managers.py
"""

import json
import csv
import os
import time
import requests
from datetime import date

# ── Config ────────────────────────────────────────────────────────────────────

APIFY_TOKEN = os.environ["APIFY_API_TOKEN"]
ACTOR_ID = "nwua9Gu5YrADL7ZDj"  # compass/google-maps-scraper
APIFY_BASE = "https://api.apify.com/v2"

SEARCH_QUERIES = [
    "property management Winfield KS",
    "property management Arkansas City KS",
    "property management Wellington KS",
    "property manager Cowley County KS",
    "apartment management Winfield KS",
    "rental property management Winfield KS",
    "real estate property management Cowley County KS",
    "HOA management Cowley County KS",
]

OUTPUT_DIR = "outreach/data"
OUTPUT_FILE = f"{OUTPUT_DIR}/property-managers-{date.today()}.csv"

CSV_FIELDS = [
    "business_name", "search_query", "address", "city", "phone",
    "website", "rating", "review_count", "google_maps_url", "category",
]

# ── Apify ─────────────────────────────────────────────────────────────────────

def run_actor(queries):
    """Start the Apify Google Maps Scraper actor and return run ID."""
    url = f"{APIFY_BASE}/acts/{ACTOR_ID}/runs?token={APIFY_TOKEN}"
    payload = {
        "searchStringsArray": queries,
        "maxCrawledPlacesPerSearch": 20,
        "language": "en",
        "countryCode": "us",
        "includeWebResults": False,
    }
    r = requests.post(url, json=payload, timeout=30)
    r.raise_for_status()
    data = r.json()
    run_id = data["data"]["id"]
    print(f"Actor started — run ID: {run_id}")
    return run_id


def wait_for_run(run_id, poll_secs=10, timeout_secs=300):
    """Poll until run finishes or times out."""
    url = f"{APIFY_BASE}/actor-runs/{run_id}?token={APIFY_TOKEN}"
    elapsed = 0
    while elapsed < timeout_secs:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        status = r.json()["data"]["status"]
        print(f"  Status: {status} ({elapsed}s elapsed)")
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            return status
        time.sleep(poll_secs)
        elapsed += poll_secs
    return "TIMEOUT"


def fetch_results(run_id):
    """Download dataset items from the completed run."""
    url = f"{APIFY_BASE}/actor-runs/{run_id}/dataset/items?token={APIFY_TOKEN}&format=json&limit=500"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return r.json()


# ── Processing ────────────────────────────────────────────────────────────────

def normalize(item):
    """Extract and normalize fields from Apify Google Maps result."""
    address = item.get("address", "") or ""
    # Try to pull city from address string
    city = ""
    for candidate in ["Winfield", "Arkansas City", "Wellington", "Burden", "Udall", "Caldwell"]:
        if candidate.lower() in address.lower():
            city = candidate
            break

    categories = item.get("categories", [])
    category = categories[0] if categories else ""

    return {
        "business_name": item.get("title", "").strip(),
        "search_query": item.get("searchString", ""),
        "address": address,
        "city": city,
        "phone": item.get("phone", "") or "",
        "website": item.get("website", "") or "",
        "rating": item.get("totalScore", "") or "",
        "review_count": item.get("reviewsCount", "") or "",
        "google_maps_url": item.get("url", "") or "",
        "category": category,
    }


def dedupe(leads):
    seen = set()
    out = []
    for lead in leads:
        key = lead["business_name"].lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(lead)
    return out


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    import os
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Submitting {len(SEARCH_QUERIES)} search queries to Apify...\n")
    run_id = run_actor(SEARCH_QUERIES)

    print("\nWaiting for results...")
    status = wait_for_run(run_id)
    print(f"\nFinal status: {status}")

    if status != "SUCCEEDED":
        print("Run did not succeed. Check Apify dashboard.")
        return

    print("Fetching results...")
    raw = fetch_results(run_id)
    print(f"  {len(raw)} raw items returned")

    leads = [normalize(item) for item in raw]
    leads = dedupe(leads)
    print(f"  {len(leads)} unique businesses after dedup")

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(leads)

    with_phone = sum(1 for l in leads if l["phone"])
    with_website = sum(1 for l in leads if l["website"])

    print(f"\nDone.")
    print(f"  {len(leads)} property managers")
    print(f"  {with_phone} with phone ({round(with_phone/len(leads)*100) if leads else 0}%)")
    print(f"  {with_website} with website ({round(with_website/len(leads)*100) if leads else 0}%)")
    print(f"  Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
