"""
Cowley County Property Owner Scraper
Pulls residential property owner names + addresses from Beacon (Schneider Corp)
Output: outreach/data/property-owners-cowley-county.csv

Requirements: pip install playwright && playwright install chromium
Run: python outreach/scrapers/pull_property_owners.py
"""

import csv
import time
import os
from playwright.sync_api import sync_playwright

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'property-owners-cowley-county.csv')
BEACON_URL = 'https://beacon.schneidercorp.com/Application.aspx?AppID=1237&LayerID=39451&PageTypeID=2&PageID=14685'

CITIES = ['Winfield', 'Arkansas City', 'Udall', 'Burden', 'Dexter', 'Cambridge']

def scrape_city(page, city, writer, seen):
    print(f'\n--- Searching: {city} ---')

    page.goto(BEACON_URL, wait_until='load', timeout=60000)
    time.sleep(4)

    # Fill city field
    try:
        city_input = page.locator('input[id*="City"], input[placeholder*="City"], input[name*="city"]').first
        city_input.fill(city)
    except Exception as e:
        print(f'  Could not find city field: {e}')
        page.screenshot(path=f'beacon-{city.lower().replace(" ", "-")}-debug.png')
        return

    # Select Residential if property class dropdown exists
    try:
        prop_class = page.locator('select[id*="Class"], select[id*="PropertyType"], select[name*="class"]').first
        prop_class.select_option(label='Residential')
    except Exception:
        pass  # Not all Beacon instances have this filter

    # Submit search
    try:
        search_btn = page.locator('input[value*="Search"], button:has-text("Search")').first
        search_btn.click()
        page.wait_for_load_state('networkidle', timeout=15000)
        time.sleep(2)
    except Exception as e:
        print(f'  Could not submit search: {e}')
        return

    page_num = 1
    total = 0

    while True:
        print(f'  Page {page_num}...', end=' ')

        # Extract result rows — Beacon uses a table with class "SearchResults" or similar
        rows = page.locator('table.SearchResults tr, table[id*="Results"] tr, #searchresults tr').all()

        if not rows:
            # Try generic table rows
            rows = page.locator('tr[class*="result"], tr[class*="row"], tr').all()

        found_this_page = 0
        for row in rows:
            cells = row.locator('td').all()
            if len(cells) < 2:
                continue
            texts = [c.inner_text().strip() for c in cells]

            # Beacon typically shows: Owner Name | Property Address | City | Parcel
            # Filter out header rows and empty rows
            if not texts[0] or texts[0].lower() in ('owner', 'name', 'parcel', 'address'):
                continue

            owner = texts[0] if len(texts) > 0 else ''
            address = texts[1] if len(texts) > 1 else ''
            prop_city = texts[2] if len(texts) > 2 else city
            parcel = texts[3] if len(texts) > 3 else ''

            if not owner or not address:
                continue

            key = (owner.upper(), address.upper())
            if key in seen:
                continue
            seen.add(key)

            writer.writerow({
                'owner_name': owner,
                'property_address': address,
                'city': prop_city or city,
                'state': 'KS',
                'parcel': parcel,
            })
            found_this_page += 1
            total += 1

        print(f'{found_this_page} records')

        # Try to go to next page
        next_btn = page.locator('a:has-text("Next"), input[value="Next >"], a[title*="Next"]').first
        if next_btn.count() == 0 or not next_btn.is_visible():
            break
        next_btn.click()
        page.wait_for_load_state('networkidle', timeout=10000)
        time.sleep(1.5)
        page_num += 1

        if page_num > 100:  # safety cap
            break

    print(f'  Total for {city}: {total}')


def main():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    fieldnames = ['owner_name', 'property_address', 'city', 'state', 'parcel']
    seen = set()
    grand_total = 0

    with open(OUTPUT, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # visible so you can watch
            page = browser.new_page()

            for city in CITIES:
                scrape_city(page, city, writer, seen)

            browser.close()

    # Count rows
    with open(OUTPUT, 'r', encoding='utf-8') as f:
        rows = sum(1 for _ in f) - 1  # minus header

    print(f'\nDone. {rows} property owners saved to:')
    print(f'  {os.path.abspath(OUTPUT)}')


if __name__ == '__main__':
    main()
