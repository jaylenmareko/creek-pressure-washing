# Creek Pressure Washing — Project CLAUDE.md

## Business
- **Name:** Creek Pressure Washing LLC
- **Area:** Wichita metro, KS — Wichita, Derby, Andover, Park City, Bel Aire, Maize, Haysville, Goddard (repositioned from South-Central Kansas/Cowley County 2026-07-27; legal address/phone unchanged, still Winfield/620)
- **Phone:** (620) 291-4583
- **Email:** us@creekpressurewashing.com
- **Services:** Driveways & Concrete, Siding & Exterior, Decks & Fences, Gutters
- **Market:** Residential + Commercial

## Current Priority
Ship the website → connect quote form → start local business outreach

## Status
- [ ] Website — built, needs real photos + Formspree form connection
- [ ] Vercel deploy — pending
- [ ] Quote form backend — needs Formspree account (free)
- [x] Outreach — running: business + property-manager scrape/enrich/send pipeline, leads through 2026-07-07 (see `outreach/CONTEXT.md`)

## File Map

```
creek-pressure-washing/
├── CLAUDE.md                        ← you are here — routing + status
│
├── site/                            ← deployable website (set Vercel root dir here)
│   ├── README.md                    ← deploy instructions, what to edit, form setup
│   ├── index.html                   ← full single-page site
│   ├── css/style.css                ← all styles — design tokens at top
│   ├── js/main.js                   ← nav scroll, hamburger, form success state
│   └── assets/images/               ← drop real photos here (see site/README.md)
│
├── outreach/                        ← lead scraping + email campaigns (active)
│   ├── CONTEXT.md                   ← pipeline contract — inputs/process/outputs/human check
│   ├── scrapers/                    ← scrape + enrich scripts, two tracks (businesses, property managers)
│   └── data/                        ← dated lead CSVs, most recent date = current list
│
└── sessions/
    └── session.md                   ← session log
```

## Stack
- Static HTML/CSS/JS — no build step, no dependencies
- Deploy: Vercel (set root directory to `projects/business/creek-pressure-washing/site`)
- Form backend: Formspree (free tier, see site/README.md)

## Design System
- **Cream:** #f2ede4 — page background
- **Navy:** #1a1e2c — headings, nav, footer
- **Blue:** #2d5be3 — accent, CTAs, italic serif
- **Font display:** Space Grotesk (bold sans) + Playfair Display (italic serif)
- Matches the existing Creek Pressure Washing flier aesthetic
