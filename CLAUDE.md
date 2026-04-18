# Project Briefing — Southern Barn Builders LLC

This file is auto-loaded by Claude Code. It orients you to the project without needing to re-read every file.

## What this is

A static marketing website for **Southern Barn Builders LLC**, a pole-barn construction company headquartered in Southwest Florida. The company serves all of Florida and into South Georgia. Audience is landowners, ranchers, equestrian clients, and small-business owners looking for custom pole barns, horse barns, workshops, RV/boat covers, commercial storage, and barndominiums.

## Stack

- Plain HTML + CSS. No build step. No framework.
- Google Fonts (Playfair Display + Inter) loaded from CDN.
- Deployed on **Cloudflare Pages**, git-connected to GitHub. Live at `https://southbarnservices.com`.
- Quote form submits via **Formsubmit.co** → `southern.barn.services@gmail.com` (no backend code).

## File map

```
southern-barn-builders/
├── index.html           Home — hero, why-us, stats, CTAs
├── services.html        9 service cards + 4-step process
├── gallery.html         Photo grid (Unsplash placeholders)
├── service-area.html    Custom inline SVG map of FL + GA + region lists
├── about.html           Story, values, credentials
├── faq.html             10 Q&A with FAQPage JSON-LD
├── contact.html         Quote form (Formsubmit.co) + direct contact info
├── 404.html             Branded not-found page
├── css/styles.css       All styles (variables, sections, responsive)
├── images/favicon.svg   SB monogram favicon (red/gold on cream)
├── images/              (real project photos go here — currently empty)
├── sitemap.xml          7 URLs, submitted to Google Search Console later
├── robots.txt           Allow all + sitemap pointer
├── _headers             Cloudflare Pages security headers
├── _redirects           Cloudflare Pages clean-URL rules
├── README.md            Dev overview
├── DEPLOY.md            Step-by-step Cloudflare Pages deploy walkthrough
└── .gitignore
```

## Brand system

| Token           | Color     | Hex       |
|-----------------|-----------|-----------|
| Primary red     | Deep red  | `#8a1c1c` |
| Dark red        |           | `#5c0f0f` |
| Primary green   | Forest    | `#2f4a2a` |
| Dark green      |           | `#1e3119` |
| Accent gold     | Gold      | `#c9a227` |
| Cream           |           | `#f7f1e3` |
| Parchment (bg)  |           | `#fdf8ec` |

Fonts: `Playfair Display` (serif, headers) + `Inter` (sans, body). All color/font/spacing tokens are defined as CSS custom properties in `css/styles.css` under `:root`. **Modify tokens there, not inline.**

## Tone of voice

Bold Southern heritage. Confident, grounded, plainspoken, slightly rural, never cheesy. Think "family-owned builder who shows up with a firm handshake" — not "rustic Instagram aesthetic." Short punchy sentences. Occasional cowboy flavor is fine ("raised," "posts in the ground," "pasture's empty") but use sparingly.

## Known placeholders — still to replace

- Gallery images (all Unsplash) — replace with real project photos in `images/`
- Hero / About stock photos — also Unsplash
- Owner name, year founded, specific license numbers — not yet on site

Real contact info (phone `(352) 646-9090`, email `southern.barn.services@gmail.com`) and the canonical URL `https://southbarnservices.com` are now wired throughout the site.

To find remaining placeholders: `grep -rn "unsplash\|picsum" .`

## Conventions

- **Shared header/footer is duplicated across pages** (there is no template engine). If you add a nav link, update it on every `.html` file including `404.html`. A `python3` one-liner or Claude Code `sed` across files is the fastest way.
- The `class="active"` attribute on the nav anchor marks the current page — preserve this per-page.
- Void elements use the self-closing slash (`<meta ... />`, `<link ... />`) for XHTML-style consistency.
- CSS is a single file. New components should use existing tokens and the `.card` / `.grid-N` / `.section.block` patterns rather than one-off styles.

## Deploy

See `DEPLOY.md`. Summary: push to GitHub → connect repo in Netlify → done. Every `git push origin main` auto-deploys.

## Roadmap / next steps

1. Replace placeholder phone, email, and photos
2. Custom domain + DNS (Netlify auto-provisions SSL)
3. Wire Netlify Forms email notification in the Netlify dashboard
4. Run an SEO audit against the live URL; target keywords like "pole barn builder Florida", "horse barn SW Florida", "pole barn Valdosta GA"
5. Add Google Business Profile + embed reviews
6. (Optional, only if a blog or CMS is needed) Migrate to Astro or Eleventy — the shared header/footer duplication is the main reason a framework would help

## Things NOT to do without asking

- Don't add a JavaScript framework "just in case"
- Don't add analytics or tracking scripts without confirming privacy stance with the owner
- Don't reword copy in a way that loses the Southern-heritage voice — "clean and corporate" is the wrong direction for this audience
- Don't inline images as base64; keep them in `images/`
