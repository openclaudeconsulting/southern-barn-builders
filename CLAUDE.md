# Project Briefing — G&P Steel Trusses Website

This file is auto-loaded by Claude Code. It orients you to the project without needing to re-read every file.

## What this is

A static marketing website for **G&P Steel Trusses**, a commercial and residential pole-barn-structure specialist serving Florida and South Georgia. G&P fabricates, supplies, and installs pole-barn structures — **barns, barndominiums, stables, workshops, garages, and custom pole-barn builds**. That's the entire scope — do NOT advertise roofing, fencing, porches, decks, or steps as standalone services. Audience is homeowners, ranchers, landowners, and commercial clients.

## Important — sales-rep arrangement

The site owner is NOT G&P Steel Trusses. The owner runs a sales/referral operation: leads are captured through this site and referred to G&P for fulfillment. The owner keeps the margin above G&P's cost. Therefore:

- Contact info on the site must always be the owner's: **(352) 646-9090** and **Southern.Barn.Services@gmail.com** — so leads flow through the owner.
- Do NOT put G&P's or any subcontractor's internal phone numbers anywhere.
- The brand and service lineup belong to G&P Steel Trusses. No official logo yet — header uses a text "G&P" monogram + wordmark as placeholder.

## Stack

- Plain HTML + CSS. No build step. No framework.
- Google Fonts (Montserrat + Inter) loaded from CDN.
- Deployed on **Cloudflare Pages**, git-connected to GitHub. Live at `https://southbarnservices.com` (domain kept from prior brand).
- Quote form submits via **Formsubmit.co** → `southernbarnservices@gmail.com` (Gmail ignores dots, so mail still lands in the canonical `Southern.Barn.Services@gmail.com` inbox).

## File map

```
southern-barn-builders/
├── index.html           Home — hero, why-us, stats, services, CTAs
├── services.html        9 service cards + 4-step process
├── gallery.html         Photo grid (real project photos)
├── service-area.html    FL + GA coverage with pinned overlay map
├── about.html           Story, 6 values, credentials
├── faq.html             10+ Q&A with FAQPage JSON-LD
├── contact.html         Quote form (Formsubmit.co) + direct contact info
├── 404.html             Branded not-found page
├── css/styles.css       All styles (variables, sections, responsive)
├── images/favicon.svg   Monogram favicon (navy on white)
├── images/              Real project photos (IMG_*.jpg). No brand logo file — header uses a text monogram placeholder.
├── sitemap.xml          URL list for Google Search Console
├── robots.txt           Allow all + sitemap pointer
├── _headers             Cloudflare Pages security headers
├── _redirects           Cloudflare Pages clean-URL rules
├── README.md            Dev overview
├── DEPLOY.md            Step-by-step Cloudflare Pages deploy walkthrough
└── .gitignore
```

## Brand system

| Token              | Color           | Hex       |
|--------------------|-----------------|-----------|
| Navy               | Deep navy       | `#1e3a5f` |
| Navy dark          |                 | `#102338` |
| Navy light         |                 | `#2c507f` |
| Blue (primary)     |                 | `#3d6bb4` |
| Blue dark          |                 | `#2a5390` |
| Blue light         |                 | `#6d93c9` |
| Sky                | Soft sky        | `#b8d0ec` |
| Sky soft (bg alt)  |                 | `#eaf1fa` |
| White              |                 | `#ffffff` |
| Off-white (page)   |                 | `#f8fafc` |
| Ink (text)         |                 | `#0f172a` |
| Muted (secondary)  |                 | `#475569` |
| Border             |                 | `#e2e8f0` |

Fonts: `Montserrat` (display/headers, uppercase h1) + `Inter` (body). All color/font/spacing tokens are defined as CSS custom properties in `css/styles.css` under `:root` with the `--pc-*` prefix. **Modify tokens there, not inline.**

## Tone of voice

Confident, grounded, plainspoken. Think "family-owned general contractor who shows up with a firm handshake." Short punchy sentences. Not corporate, not overly rural. Tag line: **Commercial & Residential**.

## Conventions

- **Shared header/footer is duplicated across pages** (there is no template engine). If you add a nav link, update it on every `.html` file including `404.html`.
- The `class="active"` attribute on the nav anchor marks the current page — preserve this per-page.
- The brand header is a text placeholder: `<span class="brand-mark">G&amp;P</span>` (navy gradient monogram box) + `<span class="brand-text">` wrapper containing `.brand-name` and `.brand-tag`. When a real logo is provided, swap this for an `<img class="brand-logo">` and the existing `.brand-logo` CSS rule will style it.
- Void elements use the self-closing slash (`<meta ... />`, `<link ... />`).
- CSS is a single file. New components should use existing `--pc-*` tokens and the `.card` / `.grid-N` / `.section.block` patterns rather than one-off styles.

## Deploy

See `DEPLOY.md`. Summary: push to GitHub → connected Cloudflare Pages project auto-builds and deploys.

## Things NOT to do without asking

- Don't add a JavaScript framework "just in case"
- Don't add analytics or tracking scripts without confirming privacy stance with the owner
- Don't replace contact info with any G&P internal number or email — leads must flow through the owner's contact info
- Don't inline images as base64; keep them in `images/`
