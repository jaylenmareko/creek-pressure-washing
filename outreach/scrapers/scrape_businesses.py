#!/usr/bin/env python3
"""
Creek Pressure Washing — South-Central Kansas Business Scraper
Scrapes Yellow Pages for local businesses, then visits their sites for emails.
Output: outreach/data/leads-YYYY-MM-DD.csv

Usage:
    pip install requests beautifulsoup4
    python scrape_businesses.py
"""

import requests
import re
import csv
import time
import os
from datetime import date
from urllib.parse import quote_plus

from bs4 import BeautifulSoup

# ── Config ────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
        "Gecko/20100101 Firefox/124.0"
    ),
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

CITIES = [
    "Winfield KS",
    "Arkansas City KS",
    "Wellington KS",
    "Mulvane KS",
    "Derby KS",
    "Haysville KS",
    "Augusta KS",
    "El Dorado KS",
    "Caldwell KS",
    "Burden KS",
    "Udall KS",
]

# Commercial categories = highest value for pressure washing
CATEGORIES = [
    "restaurants",
    "auto dealers",
    "car dealerships",
    "property management",
    "apartment complexes",
    "shopping centers",
    "retail stores",
    "hotels motels",
    "churches",
    "gas stations",
    "auto repair shops",
    "grocery stores",
    "industrial buildings",
    "manufacturing",
    "storage facilities",
    "office buildings",
    "banks",
    "veterinary clinics",
    "medical offices",
    "funeral homes",
]

EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

JUNK_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "squarespace.com",
    "wordpress.com", "shopify.com", "amazonaws.com", "googleapis.com",
    "schema.org", "w3.org", "openssl.org", "apple.com", "google.com",
    "facebook.com", "instagram.com", "twitter.com", "yelp.com",
    "yellowpages.com", "mapquest.com", "tripadvisor.com",
}

CONTACT_PATHS = [
    "/contact", "/contact-us", "/contactus", "/reach-us",
    "/about", "/about-us", "/aboutus", "/info",
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "..", "data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, f"leads-{date.today()}.csv")

CSV_FIELDS = [
    "business_name", "category", "city", "address",
    "phone", "website", "emails", "source",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_page(url, timeout=12):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r
    except Exception:
        pass
    return None


def clean_email(e):
    return e.lower().strip().rstrip(".")


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
        e = clean_email(e)
        if not is_junk_email(e):
            found.add(e)
    return found


def scrape_site_for_emails(url):
    if not url or not url.startswith("http"):
        return set()

    emails = set()
    base = url.rstrip("/")

    # Homepage
    r = get_page(base)
    if r:
        emails |= extract_emails(r.text)

    # Contact / about pages
    for path in CONTACT_PATHS:
        if emails:  # Stop once we have something
            break
        r = get_page(base + path)
        if r:
            emails |= extract_emails(r.text)
        time.sleep(0.3)

    return emails

# ── Yellow Pages Scraper ──────────────────────────────────────────────────────

def scrape_yellowpages(category, city, max_pages=3):
    results = []

    for page in range(1, max_pages + 1):
        url = (
            "https://www.yellowpages.com/search"
            f"?search_terms={quote_plus(category)}"
            f"&geo_location_terms={quote_plus(city)}"
            f"&page={page}"
        )

        r = get_page(url)
        if not r:
            break

        soup = BeautifulSoup(r.text, "html.parser")
        listings = soup.select(".result")

        if not listings:
            break

        for listing in listings:
            name_el = listing.select_one("a.business-name")
            name = name_el.get_text(strip=True) if name_el else ""
            if not name:
                continue

            phone_el = listing.select_one(".phones")
            phone = phone_el.get_text(strip=True) if phone_el else ""

            addr_el = listing.select_one(".adr")
            address = addr_el.get_text(" ", strip=True) if addr_el else ""

            site_el = listing.select_one("a.track-visit-website")
            website = site_el.get("href", "") if site_el else ""

            results.append({
                "business_name": name,
                "category": category,
                "city": city,
                "address": address,
                "phone": phone,
                "website": website,
                "emails": "",
                "source": "yellowpages",
            })

        time.sleep(1.5)

    return results

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    leads = []
    seen = set()

    total = len(CITIES) * len(CATEGORIES)
    done = 0

    print(f"Scraping {len(CITIES)} cities x {len(CATEGORIES)} categories ({total} combos)...\n")

    for city in CITIES:
        for cat in CATEGORIES:
            done += 1
            print(f"[{done}/{total}] {city} — {cat}")
            results = scrape_yellowpages(cat, city)
            new = 0
            for r in results:
                key = (r["business_name"].lower().strip(), r["city"])
                if key not in seen:
                    seen.add(key)
                    leads.append(r)
                    new += 1
            if new:
                print(f"  +{new} new ({len(leads)} total)")
            time.sleep(0.8)

    print(f"\nFound {len(leads)} unique businesses.")
    print("Scraping websites for emails...\n")

    for i, lead in enumerate(leads):
        if lead["website"]:
            print(f"[{i+1}/{len(leads)}] {lead['business_name']}  {lead['website']}")
            emails = scrape_site_for_emails(lead["website"])
            lead["emails"] = " | ".join(sorted(emails))
            if emails:
                print(f"  -> {lead['emails']}")
            time.sleep(0.4)

    # Write CSV
    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(leads)

    with_emails = sum(1 for l in leads if l["emails"])
    print(f"\nDone.")
    print(f"  {len(leads)} businesses total")
    print(f"  {with_emails} with email addresses ({round(with_emails/len(leads)*100) if leads else 0}%)")
    print(f"  Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
