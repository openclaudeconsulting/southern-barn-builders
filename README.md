# Southern Barn Builders LLC — Website

Static multi-page marketing site for Southern Barn Builders LLC, a pole barn builder headquartered in Southwest Florida serving all of Florida and into South Georgia.

## Stack

- Plain HTML + CSS (no build step, no framework)
- Google Fonts: Playfair Display + Inter
- Custom SVG service-area map (inline in `service-area.html`)
- Form handling via [Formsubmit.co](https://formsubmit.co/) → `southern.barn.services@gmail.com`

## Structure

```
southern-barn-builders/
├── index.html            Home
├── services.html         Services grid + process
├── gallery.html          Photo gallery
├── service-area.html     FL + GA coverage map
├── about.html            Company story + values
├── contact.html          Quote request form (Formsubmit.co)
├── css/
│   └── styles.css        Shared stylesheet
├── images/               (real project photos go here)
├── _headers              Cloudflare Pages security headers
├── _redirects            Cloudflare Pages clean-URL rules
├── .gitignore
├── DEPLOY.md             Deployment walkthrough
└── README.md
```

## Local preview

No build step required. Any static server works:

```
# Python
python3 -m http.server 8000

# Node (once, then serve)
npx serve .
```

Open http://localhost:8000.

## Deploy

See [`DEPLOY.md`](./DEPLOY.md). Short version: push to GitHub, connect the repo in Cloudflare Pages, done. Live at `https://southbarnservices.com`.

## Placeholders still to replace

- Gallery photos — currently Unsplash stock; swap for real project photos in `images/`
- Hero / About photos — also Unsplash; replace when ready
- License numbers — add to footer / about page once confirmed

Real contact info is already wired throughout: phone `(352) 646-9090`, public-facing email `GNPSteelTrusses@gmail.com`. The contact form's Formsubmit backend still posts to `southernbarnservices@gmail.com` — that endpoint was already verified, so leads route correctly while the brand-matched email is what customers see.

## Brand system

| Role            | Color      | Hex       |
|-----------------|------------|-----------|
| Primary red     | Deep red   | `#8a1c1c` |
| Primary green   | Forest     | `#2f4a2a` |
| Accent gold     | Gold       | `#c9a227` |
| Background      | Parchment  | `#fdf8ec` |
| Ink             | Near-black | `#1a1a1a` |

Fonts: `Playfair Display` (serif, headers) + `Inter` (sans, body).

## Roadmap

1. ~~Deploy static site~~ — live on Cloudflare Pages at `https://southbarnservices.com`
2. ~~Custom domain + DNS~~ — done
3. Swap remaining placeholder photos for real project shots
4. SEO pass (run `marketing:seo-audit`)
5. Add Google Business Profile link + reviews widget
6. Consider migrating to Astro or Eleventy if a blog / CMS is needed
