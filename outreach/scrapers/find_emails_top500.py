#!/usr/bin/env python3
"""
Creek Pressure Washing — Top500 Email Finder (Yelp-based)
For each lead:
  1. Fetch the Yelp business page
  2. Extract the real business website URL from Yelp
  3. Scrape that site for contact emails

Usage:
    pip install requests beautifulsoup4
    python find_emails_top500.py
"""

import os, re, csv, time, json, requests
from bs4 import BeautifulSoup
from datetime import date
from urllib.parse import urlparse, urljoin, unquote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
INPUT    = os.path.join(DATA_DIR, "top500.csv")
OUTPUT   = os.path.join(DATA_DIR, f"top500-emails-{date.today()}.csv")
PROGRESS = os.path.join(DATA_DIR, ".top500_email_progress.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)

SKIP_DOMAINS = {
    "yelp.com","facebook.com","instagram.com","twitter.com","x.com",
    "yellowpages.com","tripadvisor.com","google.com","bing.com","bbb.org",
    "linkedin.com","indeed.com","whitepages.com","mapquest.com","manta.com",
}

JUNK_EMAIL_DOMAINS = {
    "example.com","sentry.io","wixpress.com","squarespace.com","wordpress.com",
    "shopify.com","amazonaws.com","googleapis.com","schema.org","w3.org",
    "apple.com","google.com","facebook.com","instagram.com","twitter.com",
    "yelp.com","adobe.com",
}

CONTACT_PATHS = ["/contact", "/contact-us", "/about", "/about-us"]
CSV_FIELDS = ["business_name","category","city","address","phone","website","emails","yelp_url"]


def load_progress():
    if os.path.exists(PROGRESS):
        with open(PROGRESS) as f: return json.load(f)
    return {"done": {}}

def save_progress(p):
    with open(PROGRESS, "w") as f: json.dump(p, f)

def get_page(url, timeout=12):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if r.status_code == 200: return r
    except Exception: pass
    return None

def extract_website_from_yelp(yelp_url):
    """Fetch Yelp page and extract the business website URL."""
    if not yelp_url or "yelp.com" not in yelp_url:
        return ""
    r = get_page(yelp_url)
    if not r: return ""
    soup = BeautifulSoup(r.text, "html.parser")

    # Yelp wraps external links as /biz_redir?url=...
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "biz_redir" in href and "url=" in href:
            try:
                raw = href.split("url=")[1].split("&")[0]
                decoded = unquote(raw)
                domain = urlparse(decoded).netloc.lower().replace("www.","")
                if domain and "." in domain and not any(s in domain for s in SKIP_DOMAINS):
                    return decoded.split("?")[0].rstrip("/")
            except Exception: continue

    # Fallback: look for any external link with a business-y href
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("http") and "yelp.com" not in href:
            try:
                domain = urlparse(href).netloc.lower().replace("www.","")
                if domain and "." in domain and not any(s in domain for s in SKIP_DOMAINS):
                    return href.split("?")[0].rstrip("/")
            except Exception: continue
    return ""

def is_junk_email(e):
    domain = e.split("@")[-1].lower()
    return (
        domain in JUNK_EMAIL_DOMAINS or
        any(e.endswith(x) for x in (".png",".jpg",".gif",".svg",".css",".js")) or
        len(e) > 80 or "noreply" in e or "no-reply" in e
    )

def extract_emails(html):
    found = set()
    for e in EMAIL_RE.findall(html):
        e = e.lower().strip().rstrip(".")
        if not is_junk_email(e): found.add(e)
    return found

def scrape_site(url):
    if not url or not url.startswith("http"): return set()
    emails = set()
    base = url.rstrip("/")
    for path in [""] + CONTACT_PATHS:
        r = get_page(base + path)
        if r:
            emails |= extract_emails(r.text)
            if emails: break
        time.sleep(0.3)
    return emails


def main():
    with open(INPUT, encoding="utf-8") as f:
        leads = list(csv.DictReader(f))

    # Deduplicate by phone
    seen_phones = set()
    unique_leads = []
    for l in leads:
        phone = l.get("phone","").strip()
        if phone and phone in seen_phones: continue
        seen_phones.add(phone)
        unique_leads.append(l)

    print(f"Top500 leads: {len(leads)} | Unique by phone: {len(unique_leads)}")

    prog = load_progress()
    done = prog.get("done", {})

    enriched_map = {}
    if os.path.exists(OUTPUT):
        with open(OUTPUT, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                enriched_map[row["business_name"] + "|" + row["city"]] = row

    found_email_count = sum(1 for r in enriched_map.values() if r.get("emails","").strip())

    for i, lead in enumerate(unique_leads):
        key = f"{lead['business_name']}|{lead['city']}"
        if key in done:
            continue

        print(f"[{i+1}/{len(unique_leads)}] {lead['business_name']}", end="  ", flush=True)

        yelp_url = lead.get("yelp_url","") or lead.get("website","")
        website = extract_website_from_yelp(yelp_url)
        lead["website"] = website

        emails = set()
        if website:
            emails = scrape_site(website)
            lead["emails"] = " | ".join(sorted(emails))
            if emails:
                print(f"✓ {lead['emails']}")
                found_email_count += 1
            else:
                print(f"site: {website} — no email")
        else:
            lead["emails"] = ""
            print("no website on Yelp")

        enriched_map[key] = lead
        done[key] = True
        prog["done"] = done
        save_progress(prog)

        with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(enriched_map.values())

        time.sleep(1.5)

    print(f"\n✅ Done. {found_email_count} emails found.")
    print(f"   Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
