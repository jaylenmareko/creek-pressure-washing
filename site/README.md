# site/ — Creek Pressure Washing Website

Static HTML/CSS/JS. No build step. Open `index.html` in a browser to preview.

## Deploy to Vercel
1. Push this repo to GitHub
2. Import project in Vercel
3. Set **Root Directory** → `projects/business/creek-pressure-washing/site`
4. Framework: Other (static)
5. Deploy

## Connect the Quote Form
Currently the form shows a success state on submit (JS only — no data is sent).

To receive real submissions:
1. Go to formspree.io → create free account → new form
2. Copy your form endpoint (e.g. `https://formspree.io/f/abcd1234`)
3. In `index.html`, find the `<form id="quote-form">` tag
4. Add: `action="https://formspree.io/f/YOUR_ID" method="POST"`
5. Formspree emails submissions to you — free up to 50/month

## Replacing Placeholder Images
All `<img>` tags with picsum.photos URLs have a `<!-- Replace: ... -->` comment above them.
- Drop real photos into `assets/images/`
- Update the `src` attribute on each image
- Use your own before/after job photos — NOT stock images

## File Map
| File | What it is |
|---|---|
| `index.html` | Full single-page site — all sections |
| `css/style.css` | All styles. Design tokens (colors, fonts) are at the top in `:root {}` |
| `js/main.js` | Nav scroll shadow, hamburger menu, form success state |
| `assets/images/` | Drop real photos here |

## Editing Colors
Open `css/style.css` → find `:root {` at the top → change `--navy`, `--blue`, `--cream` values.

## Sections (in order)
1. Nav — sticky, collapses to hamburger on mobile
2. Hero — big Creek typography matching the flier, right-side photo panel
3. Trust bar — Licensed, Insured, Guaranteed, Location
4. Services — 4 cards (Driveways, Siding, Decks, Gutters)
5. How It Works — 3 steps
6. Gallery — before/after grid (replace with real job photos)
7. Quote Form — name, phone, email, property type, city, services, message
8. Testimonials — 3 reviews (replace with real ones)
9. Footer
