#!/usr/bin/env python3
"""
Creek Pressure Washing — Property Manager Email Enrichment
Scrapes emails from the property-managers CSV (websites already known).
Falls back to DuckDuckGo search for leads without a website.

Usage:
    python enrich_property_managers.py
"""

import os, re, csv, time, json, requests
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import quote_plus, urljoin, urlparse

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DATA_DIR      = os.path.join(BASE_DIR, "..", "data")
INPUT_CSV     = os.path.join(DATA_DIR, "property-managers-2026-06-23.csv")
OUTPUT_CSV    = os.path.join(DATA_DIR, f"property-managers-emails-{date.today()}.csv")
PROGRESS_FILE = os.path.join(DATA_DIR, ".pm_email_progress.json")

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
}

SKIP_DOMAINS = {
    "yelp.com", "facebook.com", "instagram.com", "twitter.com",
    "yellowpages.com", "google.com", "bbb.org", "linkedin.com",
}

CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/reach-us", "/info"]


def get_page(url, timeout=12):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code == 200:
            return r
    except Exception:
        pass
    return None


def ddg_find_website(name, city):
    query = f'"{name}" "{city}" Kansas contact email'
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
            domain = urlparse(href).netloc.lower().replace("www.", "")
            if any(s in domain for s in SKIP_DOMAINS):
                continue
            if domain and "." in domain:
                return href.split("?")[0].rstrip("/")
        except Exception:
            continue
    return ""


def is_junk_email(e):
    domain = e.split("@")[-1].lower()
    return (
        domain in JUNK_DOMAINS
        or any(e.endswith(x) for x in (".png", ".jpg", ".gif", ".svg", ".css", ".js"))
        or len(e) > 80
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
    # Try home page first, then contact pages
    pages = [""] + CONTACT_PATHS
    for path in pages:
        r = get_page(base + path)
        if r:
            found = extract_emails(r.text)
            emails |= found
        time.sleep(0.3)
        if emails:
            break
    return emails


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"done": []}


def save_progress(prog):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(prog, f)


def main():
    with open(INPUT_CSV, encoding="utf-8") as f:
        leads = list(csv.DictReader(f))

    print(f"Leads to enrich: {len(leads)}\n")

    prog = load_progress()
    done_set = set(prog.get("done", []))

    # Output fields
    out_fields = ["business_name", "type", "city", "phone", "website", "email", "rating", "reviews"]

    enriched = {}
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                enriched[f"{row['business_name']}|{row['city']}"] = row

    for i, lead in enumerate(leads):
        key = f"{lead['business_name']}|{lead['city']}"
        if key in done_set:
            print(f"[{i+1}/{len(leads)}] SKIP {lead['business_name']}")
            continue

        website = lead.get("website", "").strip()
        print(f"[{i+1}/{len(leads)}] {lead['business_name']} ({lead['city']})", end="  ", flush=True)

        # If no website, try DDG
        if not website or not website.startswith("http"):
            website = ddg_find_website(lead["business_name"], lead["city"])
            time.sleep(1.5)

        emails = set()
        if website:
            emails = scrape_site(website)

        row = {
            "business_name": lead["business_name"],
            "type": lead.get("type", ""),
            "city": lead["city"],
            "phone": lead.get("phone", ""),
            "website": website,
            "email": " | ".join(sorted(emails)) if emails else "",
            "rating": lead.get("rating", ""),
            "reviews": lead.get("reviews", ""),
        }

        if emails:
            print(f"FOUND  {row['email']}")
        elif website:
            print(f"site found, no email — {website}")
        else:
            print("no website found")

        enriched[key] = row
        done_set.add(key)
        prog["done"] = list(done_set)
        save_progress(prog)

        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(enriched.values())

        time.sleep(1.2)

    with_emails = sum(1 for r in enriched.values() if r.get("email"))
    print(f"\nDone. {len(enriched)} processed, {with_emails} with emails")
    print(f"Saved: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
