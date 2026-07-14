#!/usr/bin/env python3
"""
Creek Pressure Washing — Email Enrichment
For each lead, searches DuckDuckGo for the business website,
then scrapes that site for contact emails.

No API key needed. Free + unlimited.
Saves after every business — safe to Ctrl+C and re-run.

Usage:
    python enrich_emails.py
"""

import os
import re
import csv
import time
import json
import requests
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import quote_plus, urljoin

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DATA_DIR      = os.path.join(BASE_DIR, "..", "data")
INPUT_CSV     = os.path.join(DATA_DIR, "leads-2026-05-19.csv")
OUTPUT_CSV    = os.path.join(DATA_DIR, f"leads-enriched-{date.today()}.csv")
PROGRESS_FILE = os.path.join(DATA_DIR, ".enrich_progress.json")

# Only process these high-value commercial categories
PRIORITY_CATS = {
    "restaurants", "auto_dealers", "propertymgmt", "hotelstravel",
    "autorepair", "religiousorgs", "shoppingcenters", "banks",
    "medcenters", "contractors", "carwash", "realestatesvcs",
    "funeralservices", "grocery", "servicestations",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)

JUNK_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "squarespace.com",
    "wordpress.com", "shopify.com", "amazonaws.com", "googleapis.com",
    "schema.org", "w3.org", "apple.com", "google.com", "facebook.com",
    "instagram.com", "twitter.com", "yelp.com", "yellowpages.com",
    "tripadvisor.com", "bbb.org", "mapquest.com", "whitepages.com",
    "dexknows.com", "manta.com", "superpages.com",
}

SKIP_DOMAINS = {
    "yelp.com", "facebook.com", "instagram.com", "twitter.com",
    "yellowpages.com", "tripadvisor.com", "google.com", "bing.com",
    "bbb.org", "linkedin.com", "indeed.com", "whitepages.com",
    "mapquest.com", "manta.com", "superpages.com", "dexknows.com",
    "foursquare.com", "nextdoor.com", "angieslist.com", "houzz.com",
}

CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/reach-us", "/info"]

CSV_FIELDS = ["business_name", "category", "city", "address", "phone", "website", "emails", "yelp_url"]

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"done": []}


def save_progress(prog):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(prog, f)


def get_page(url, timeout=10):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r
    except Exception:
        pass
    return None


def ddg_find_website(business_name, city):
    """Search DuckDuckGo HTML for the business website."""
    query = f'"{business_name}" "{city}" -site:yelp.com -site:facebook.com'
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

    r = get_page(url)
    if not r:
        return ""

    soup = BeautifulSoup(r.text, "html.parser")

    for result in soup.select(".result__url, .result__a"):
        href = result.get("href", "") or result.get_text(strip=True)
        if not href.startswith("http"):
            href = "https://" + href

        try:
            from urllib.parse import urlparse
            domain = urlparse(href).netloc.lower().replace("www.", "")
            if any(skip in domain for skip in SKIP_DOMAINS):
                continue
            if domain and "." in domain:
                return href.split("?")[0].rstrip("/")
        except Exception:
            continue

    return ""


def is_junk_email(e):
    domain = e.split("@")[-1].lower()
    return (
        domain in JUNK_DOMAINS or
        any(e.endswith(x) for x in (".png", ".jpg", ".gif", ".svg", ".css", ".js")) or
        len(e) > 80
    )


def extract_emails(html):
    found = set()
    for e in EMAIL_RE.findall(html):
        e = e.lower().strip().rstrip(".")
        if not is_junk_email(e):
            found.add(e)
    return found


def scrape_site(url):
    if not url or not url.startswith("http"):
        return set()
    emails = set()
    base = url.rstrip("/")
    for path in [""] + CONTACT_PATHS:
        r = get_page(base + path)
        if r:
            emails |= extract_emails(r.text)
            if emails:
                break
        time.sleep(0.2)
    return emails

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Load leads
    with open(INPUT_CSV, encoding="utf-8") as f:
        all_leads = list(csv.DictReader(f))

    # Filter to priority commercial categories only
    leads = [l for l in all_leads if l["category"] in PRIORITY_CATS]
    print(f"Total leads: {len(all_leads)} | Priority commercial: {len(leads)}")

    # Load progress
    prog = load_progress()
    done_set = set(prog.get("done", []))
    print(f"Already enriched: {len(done_set)}\n")

    # Load existing enriched output
    enriched = {}
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                key = f"{row['business_name']}|{row['city']}"
                enriched[key] = row

    for i, lead in enumerate(leads):
        key = f"{lead['business_name']}|{lead['city']}"
        if key in done_set:
            continue

        print(f"[{i+1}/{len(leads)}] {lead['business_name']} ({lead['city']})", end="  ", flush=True)

        # Search DuckDuckGo for their website
        website = ddg_find_website(lead["business_name"], lead["city"])
        lead["website"] = website

        emails = set()
        if website:
            emails = scrape_site(website)
            lead["emails"] = " | ".join(sorted(emails))
            if emails:
                print(f"✓ {lead['emails']}")
            else:
                print(f"site found, no email — {website}")
        else:
            print("no website found")

        enriched[key] = lead
        done_set.add(key)
        prog["done"] = list(done_set)
        save_progress(prog)

        # Write output after every business
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(enriched.values())

        time.sleep(1.2)  # Polite delay for DDG

    with_emails = sum(1 for r in enriched.values() if r.get("emails"))
    with_sites  = sum(1 for r in enriched.values() if r.get("website"))
    print(f"\nDone.")
    print(f"  {len(enriched)} processed")
    print(f"  {with_sites} with websites")
    print(f"  {with_emails} with emails")
    print(f"  Saved: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
