# Southern Barn Builders LLC — Website

Static multi-page marketing site for Southern Barn Builders LLC, a pole barn builder headquartered in Southwest Florida serving all of Florida and into South Georgia.

## Stack

- Plain HTML + CSS (no build step, no framework)
- Google Fonts: Playfair Display + Inter
- Custom SVG service-area map (inline in `service-area.html`)
- Form handling via [Netlify Forms](https://docs.netlify.com/forms/setup/)

## Structure

```
southern-barn-builders/
├── index.html            Home
├── services.html         Services grid + process
├── gallery.html          Photo gallery
├── service-area.html     FL + GA coverage map
├── about.html            Company story + values
├── contact.html          Quote request form (Netlify Forms)
├── css/
│   └── styles.css        Shared stylesheet
├── images/               (real project photos go here)
├── netlify.toml          Netlify config (headers, redirects)
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

See [`DEPLOY.md`](./DEPLOY.md). Short version: push to GitHub, connect the repo in Netlify, done.

## Placeholders to replace before launch

- Phone: `(239) 555-0142` (appears in header, footer, contact page)
- Email: `info@southernbarnbuilders.com`
- Gallery photos — currently Unsplash stock; swap for real project photos in `images/`
- Hero / About photos — also Unsplash; replace when ready
- License numbers — add to footer / about page once confirmed

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

1. Deploy static site to Netlify (in progress)
2. Swap placeholder content for real info
3. Custom domain + DNS
4. SEO pass (run `marketing:seo-audit` once live)
5. Add Google Business Profile link + reviews widget
6. Consider migrating to Astro or Eleventy if a blog / CMS is needed
