# Creek Pressure Washing — Session Log

---

## 2025-05-17

**Done:**
- Created full project folder structure
- Built complete website: `site/index.html`, `site/css/style.css`, `site/js/main.js`
- Design matches Creek flier: cream bg, navy + blue palette, Space Grotesk + Playfair Display typography, decorative circles
- Sections: Nav, Hero, Trust bar, Services (4), How It Works, Gallery (before/after), Quote Form, Testimonials, Footer
- Placeholder images throughout — ready to swap for real job photos
- Quote form shows success state (JS only) — needs Formspree to actually send submissions

**Next:**
- [ ] Replace picsum placeholder images with real job photos
- [ ] Set up Formspree and connect the quote form
- [ ] Deploy to Vercel (set root dir to `site/`)
- [ ] Add real Google reviews to testimonials section
- [x] Start outreach system (scraping + email) — done since (leads data through 2026-07-07), just never logged here

---

## 2026-07-18 — Fixed stale outreach status + added stage contract

- **Did:** This log (and `CLAUDE.md`) still said outreach was a future TODO while `outreach/` had a full, running two-track scrape/enrich/send pipeline. Updated `CLAUDE.md` status + file map, replaced the stale `outreach/README.md` placeholder with a pointer to a new `outreach/CONTEXT.md` stage contract.
- **Output:** `CLAUDE.md`, `outreach/CONTEXT.md`, `outreach/README.md`. Full detail in the monorepo's `sessions/log/2026-07-18.md`.
- **Why:** Caught during an ICM-wide audit — this is exactly the "log says one thing, folder says another" drift the audit was checking for.

---

## 2026-07-27 — Repositioned service area from Cowley County to Wichita metro

- **Did:** Full regional pivot per Jaylen's request. Rewrote homepage (`site/index.html`): hero, meta/OG tags, LocalBusiness schema `areaServed`, services header, About section, quote section, form placeholder, footer. Deleted the 6 Cowley County location pages (winfield-ks, arkansas-city-ks, udall-ks, burden-ks, dexter-ks, cambridge-ks) and generated 8 new Wichita-metro pages (wichita-ks, derby-ks, andover-ks, park-city-ks, bel-aire-ks, maize-ks, haysville-ks, goddard-ks). Rebuilt `sitemap.xml` to match. Updated outreach pipeline targeting: `scrape_businesses.py` CITIES list, `scrape_property_managers.py` SEARCH_QUERIES, `email/template-cold.md` region reference. Updated `CONTEXT.md` + `CLAUDE.md` Area field.
- **Kept as-is (user decision):** Legal address (Winfield, 67156) and phone ((620) 291-4583) — user chose to keep these and just change area-served marketing copy rather than get a new Wichita (316) number.
- **Gap flagged, not fixed:** `pull_property_owners.py` hits Cowley County's Beacon (Schneider Corp) property-records instance by AppID/LayerID — this does not port to Wichita metro by swapping city names. Needs research into Sedgwick/Butler County's actual property-records source before that script can target the new area. Left CITIES/BEACON_URL untouched with a warning docstring rather than guess.
- **Not touched:** `docs/dba-statement.*` (legal DBA filing, Cowley County — historical record, not a marketing artifact). Already-sent cold email scripts (`send_emails_batch2.py`, `send_emails_resend*.py`) still say "Cowley County" in their pitch text — left as historical record of what was actually sent; any *new* send should draw from the updated `email/template-cold.md` instead.
- **Next:** Site needs redeploy to Vercel to go live with the new pages. Outreach needs a fresh Wichita-metro business scrape (old CSVs in `outreach/data/` are Cowley County leads, now stale for targeting purposes but left in place as historical record).
