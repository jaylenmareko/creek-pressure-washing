#!/usr/bin/env python3
"""
Creek Pressure Washing — South-Central Kansas Business Scraper
Uses Yelp Fusion API (free, 500 req/day) to find local businesses,
then visits each business website to scrape contact emails.

Setup (one-time):
  1. Go to https://www.yelp.com/developers → Create App → copy API key
  2. Set env var:  set YELP_API_KEY=your_key_here
  3. pip install requests beautifulsoup4
  4. python scrape_businesses.py

Output: outreach/data/leads-YYYY-MM-DD.csv
"""

import os
import re
import csv
import time
from datetime import date
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────

YELP_API_KEY = os.environ.get("YELP_API_KEY", "")
YELP_SEARCH_URL = "https://api.yelp.com/v3/businesses/search"

CITIES = [
    "Winfield, KS",
    "Arkansas City, KS",
    "Wellington, KS",
    "Mulvane, KS",
    "Derby, KS",
    "Haysville, KS",
    "Augusta, KS",
    "El Dorado, KS",
    "Caldwell, KS",
    "Burden, KS",
    "Udall, KS",
]

# Commercial categories — highest value for pressure washing
CATEGORIES = [
    "restaurants",
    "auto_dealers",
    "propertymgmt",
    "hotelstravel",
    "servicestations",
    "autorepair",
    "religiousorgs",
    "grocery",
    "shoppingcenters",
    "industrialdesign",
    "storage",
    "banks",
    "veterinarians",
    "medcenters",
    "funeralservices",
    "carwash",
    "laundryservices",
    "contractors",
    "landscaping",
    "realestatesvcs",
]

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
        "Gecko/20100101 Firefox/124.0"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

JUNK_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "squarespace.com",
    "wordpress.com", "shopify.com", "amazonaws.com", "googleapis.com",
    "schema.org", "w3.org", "apple.com", "google.com",
    "facebook.com", "instagram.com", "twitter.com", "yelp.com",
    "yellowpages.com", "mapquest.com", "tripadvisor.com",
}

CONTACT_PATHS = [
    "/contact", "/contact-us", "/contactus",
    "/about", "/about-us", "/reach-us", "/info",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"leads-{date.today()}.csv")

CSV_FIELDS = [
    "business_name", "category", "city", "address",
    "phone", "website", "emails", "yelp_url",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_page(url, timeout=12):
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r
    except Exception:
        pass
    return None


def is_junk_email(e):
    domain = e.split("@")[-1].lower()
    if domain in JUNK_DOMAINS:
        return True
    if any(e.endswith(ext) for ext in (".png", ".jpg", ".gif", ".svg", ".css", ".js")):
        return True
    if len(e) > 80:
        return True
    return False


def extract_emails(html):
    found = set()
    for e in EMAIL_RE.findall(html):
        e = e.lower().strip().rstrip(".")
        if not is_junk_email(e):
            found.add(e)
    return found


def scrape_site_for_emails(url):
    if not url or not url.startswith("http"):
        return set()

    emails = set()
    base = url.rstrip("/")

    r = get_page(base)
    if r:
        emails |= extract_emails(r.text)

    for path in CONTACT_PATHS:
        if emails:
            break
        r = get_page(base + path)
        if r:
            emails |= extract_emails(r.text)
        time.sleep(0.25)

    return emails

# ── Yelp API ──────────────────────────────────────────────────────────────────

def yelp_search(category, city, offset=0):
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {
        "categories": category,
        "location": city,
        "limit": 50,
        "offset": offset,
    }
    try:
        r = requests.get(YELP_SEARCH_URL, headers=headers, params=params, timeout=15)
        if r.status_code == 200:
            return r.json()
        else:
            print(f"    Yelp error {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"    Request failed: {e}")
    return None


def fetch_businesses(category, city):
    businesses = []
    offset = 0

    while True:
        data = yelp_search(category, city, offset=offset)
        if not data:
            break

        batch = data.get("businesses", [])
        if not batch:
            break

        for b in batch:
            loc = b.get("location", {})
            addr_parts = [
                loc.get("address1", ""),
                loc.get("city", ""),
                loc.get("state", ""),
                loc.get("zip_code", ""),
            ]
            address = ", ".join(p for p in addr_parts if p)

            businesses.append({
                "business_name": b.get("name", ""),
                "category": category,
                "city": city,
                "address": address,
                "phone": b.get("phone", ""),
                "website": b.get("url", ""),   # Yelp URL; real site added later if available
                "emails": "",
                "yelp_url": b.get("url", ""),
            })

        total = data.get("total", 0)
        offset += len(batch)
        if offset >= total or offset >= 1000:
            break

        time.sleep(0.5)

    return businesses

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not YELP_API_KEY:
        print(
            "\nNo YELP_API_KEY found.\n\n"
            "Setup:\n"
            "  1. https://www.yelp.com/developers → Create App → copy API key\n"
            "  2. In this terminal: set YELP_API_KEY=your_key_here\n"
            "  3. Run this script again.\n"
        )
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    leads = []
    seen = set()

    total = len(CITIES) * len(CATEGORIES)
    done = 0

    print(f"Scraping {len(CITIES)} cities x {len(CATEGORIES)} categories...\n")

    for city in CITIES:
        for cat in CATEGORIES:
            done += 1
            print(f"[{done}/{total}] {city} — {cat}", end="", flush=True)
            businesses = fetch_businesses(cat, city)
            new_count = 0
            for b in businesses:
                key = (b["business_name"].lower().strip(), b["city"])
                if key not in seen:
                    seen.add(key)
                    leads.append(b)
                    new_count += 1
            print(f"  +{new_count}")
            time.sleep(0.3)

    print(f"\n{len(leads)} unique businesses found.")
    print("Visiting websites for emails...\n")

    for i, lead in enumerate(leads):
        website = lead.get("website", "")
        # Skip yelp URLs — visit actual business site
        if website and "yelp.com" not in website:
            print(f"[{i+1}/{len(leads)}] {lead['business_name']}")
            emails = scrape_site_for_emails(website)
            lead["emails"] = " | ".join(sorted(emails))
            if emails:
                print(f"  -> {lead['emails']}")
        time.sleep(0.3)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(leads)

    with_emails = sum(1 for l in leads if l["emails"])
    print(f"\nDone.")
    print(f"  {len(leads)} businesses")
    print(f"  {with_emails} with emails ({round(with_emails / len(leads) * 100) if leads else 0}%)")
    print(f"  Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
