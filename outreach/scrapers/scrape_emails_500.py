#!/usr/bin/env python3
"""
Creek Pressure Washing — 500 Lead Email Scraper
Uses a real Chromium browser (Playwright) to:
  1. Search Bing for each business to find their website
  2. Visit the website and scrape for contact emails

Safe to stop and re-run — saves progress after every business.

Usage:
    pip install playwright
    python -m playwright install chromium
    python scrape_emails_500.py
"""

import asyncio
import csv
import json
import os
import re
from datetime import date
from urllib.parse import quote_plus

from playwright.async_api import async_playwright

# ── Config ────────────────────────────────────────────────────────────────────

BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DATA_DIR      = os.path.join(BASE_DIR, "..", "data")
INPUT_CSV     = os.path.join(DATA_DIR, "top500.csv")
OUTPUT_CSV    = os.path.join(DATA_DIR, f"leads-emails-{date.today()}.csv")
PROGRESS_FILE = os.path.join(DATA_DIR, ".email500_progress.json")

SKIP_DOMAINS = {
    "yelp.com", "facebook.com", "instagram.com", "twitter.com", "x.com",
    "yellowpages.com", "tripadvisor.com", "google.com", "bing.com",
    "bbb.org", "linkedin.com", "indeed.com", "whitepages.com",
    "mapquest.com", "manta.com", "superpages.com", "dexknows.com",
    "foursquare.com", "nextdoor.com", "angieslist.com", "houzz.com",
    "cars.com", "autotrader.com", "carfax.com", "dealerrater.com",
    "allbiz.com", "chamberofcommerce.com", "loc8nearme.com",
    "findstorenearme.us", "alltrack.org", "sur.ly", "citysquares.com",
}

CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us", "/reach-us", "/staff"]

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)

JUNK_DOMAINS = {
    "example.com", "sentry.io", "wixpress.com", "squarespace.com",
    "amazonaws.com", "googleapis.com", "schema.org", "w3.org",
    "apple.com", "google.com", "facebook.com", "instagram.com",
    "twitter.com", "yelp.com", "yellowpages.com",
}

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


def is_junk_email(e):
    domain = e.split("@")[-1].lower()
    return (
        domain in JUNK_DOMAINS or
        any(e.endswith(x) for x in (".png", ".jpg", ".gif", ".svg", ".css", ".js")) or
        "@2x" in e or len(e) > 80
    )


def extract_emails(html):
    found = set()
    for e in EMAIL_RE.findall(html):
        e = e.lower().strip().rstrip(".")
        if not is_junk_email(e):
            found.add(e)
    return found


def first_good_cite(cites):
    """Return the first cite URL that isn't a directory/social site."""
    for cite in cites:
        cite = cite.strip()
        if not cite.startswith("http"):
            cite = "https://" + cite
        try:
            from urllib.parse import urlparse
            domain = urlparse(cite).netloc.lower().replace("www.", "")
            if not any(skip in domain for skip in SKIP_DOMAINS):
                return cite.split(" ")[0]  # strip any trailing text
        except Exception:
            continue
    return ""

# ── Core scraping ─────────────────────────────────────────────────────────────

async def find_website(page, name, city):
    query = f"{name} {city} KS"
    await page.goto(f"https://www.bing.com/search?q={quote_plus(query)}", timeout=15000)
    await page.wait_for_timeout(1200)
    cites = await page.eval_on_selector_all("cite", "els => els.map(e => e.innerText.trim())")
    return first_good_cite(cites)


async def scrape_emails(page, url):
    emails = set()
    base = url.rstrip("/")
    for path in [""] + CONTACT_PATHS:
        try:
            await page.goto(base + path, timeout=12000, wait_until="domcontentloaded")
            await page.wait_for_timeout(600)
            html = await page.content()
            found = extract_emails(html)
            emails |= found
            if emails:
                break
        except Exception:
            pass
    return emails


async def process_lead(browser, lead, sem):
    async with sem:
        context = await browser.new_context()
        page = await context.new_page()
        try:
            website = await find_website(page, lead["business_name"], lead["city"])
            emails = set()
            if website:
                emails = await scrape_emails(page, website)
            lead["website"] = website
            lead["emails"] = " | ".join(sorted(emails))
            return lead, bool(website), bool(emails)
        except Exception as e:
            lead["website"] = ""
            lead["emails"] = ""
            return lead, False, False
        finally:
            await context.close()

# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    with open(INPUT_CSV, encoding="utf-8") as f:
        leads = list(csv.DictReader(f))

    prog = load_progress()
    done_set = set(prog.get("done", []))
    print(f"Loaded {len(leads)} leads | Already done: {len(done_set)}\n")

    # Load existing output
    enriched = {}
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                enriched[f"{row['business_name']}|{row['city']}"] = row

    pending = [l for l in leads if f"{l['business_name']}|{l['city']}" not in done_set]
    print(f"Remaining: {len(pending)}\n")

    sem = asyncio.Semaphore(3)  # 3 concurrent browsers
    total = len(leads)
    done_count = len(done_set)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        tasks = [process_lead(browser, lead, sem) for lead in pending]

        for coro in asyncio.as_completed(tasks):
            lead, has_site, has_email = await coro
            done_count += 1
            key = f"{lead['business_name']}|{lead['city']}"
            enriched[key] = lead
            done_set.add(key)

            status = f"✓ {lead['emails']}" if has_email else ("site, no email" if has_site else "no site")
            print(f"[{done_count}/{total}] {lead['business_name']} ({lead['city']})  {status}")

            prog["done"] = list(done_set)
            save_progress(prog)

            with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                writer.writeheader()
                writer.writerows(enriched.values())

        await browser.close()

    with_emails = sum(1 for r in enriched.values() if r.get("emails"))
    with_sites  = sum(1 for r in enriched.values() if r.get("website"))
    print(f"\nDone.")
    print(f"  {len(enriched)} processed")
    print(f"  {with_sites} with websites found")
    print(f"  {with_emails} with emails")
    print(f"  Saved: {OUTPUT_CSV}")


if __name__ == "__main__":
    asyncio.run(main())
