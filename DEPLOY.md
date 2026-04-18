# Deployment Walkthrough

Target: **Cloudflare Pages**, git-connected to GitHub, free `*.pages.dev` subdomain for now.

**Why Cloudflare Pages:** unlimited bandwidth, unlimited requests, free SSL, global CDN. No surprise overage bills if a Facebook ad brings a traffic spike.

Contact form uses **Formsubmit.co** — unlimited free submissions, goes straight to `southernbarnservices@gmail.com` (the no-dots variant of the real inbox; Gmail treats them as the same address).

---

## 1. Push to GitHub

In your terminal, from inside `southern-barn-builders/`:

```bash
# Initialize (skip the first two if you already ran them)
git init
git add .
git commit -m "Initial site"

# Create a new empty repo at https://github.com/new
# Name it: southern-barn-builders  (keep it Private or Public, your call)
# Do NOT add a README/license there — we already have one.

# Then back in your terminal:
git branch -M main
git remote add origin https://github.com/<your-username>/southern-barn-builders.git
git push -u origin main
```

## 2. Connect Cloudflare Pages to GitHub

1. Go to https://dash.cloudflare.com and sign in (or sign up — free).
2. In the left sidebar, click **Workers & Pages**.
3. Click **Create** → **Pages** tab → **Connect to Git**.
4. Authorize Cloudflare to access your GitHub (you can limit it to just this one repo).
5. Select `southern-barn-builders` → **Begin setup**.
6. Build settings — **leave everything blank**:
   - Framework preset: **None**
   - Build command: *(empty)*
   - Build output directory: *(empty — or `/`)*
7. Click **Save and Deploy**.

First deploy takes ~30 seconds. You'll get a URL like `https://southern-barn-builders.pages.dev`.

## 3. Activate Formsubmit.co (one-time)

The first time you submit the form, Formsubmit emails `southernbarnservices@gmail.com` with an activation link. Click it once and future submissions arrive silently.

1. Open the live site → submit a test quote.
2. Check the Gmail inbox for an email from Formsubmit — click the confirm link.
3. From then on, every real submission arrives as a clean formatted email.

## 4. Verify everything works

- Visit every nav link. Confirm they all load.
- Submit the quote form. Confirm you land on `/thanks.html` and get the email.
- Check on phone (narrow viewport) — nav hamburger should work.

## 5. Auto-deploy on every push

From here on, every `git push origin main` triggers a new deploy automatically. Each pull request also gets its own preview URL — handy for reviewing copy changes before they go live.

## 6. Custom domain (later)

When you buy a domain (recommend [Cloudflare Registrar](https://www.cloudflare.com/products/registrar/) at ~$10/yr wholesale, no renewal markup):

1. Cloudflare Pages → your project → **Custom domains** → **Set up a custom domain**.
2. Enter the domain. If registered at Cloudflare, DNS is auto-configured. If registered elsewhere, follow the CNAME instructions.
3. SSL cert auto-provisions within minutes.
4. Update `sitemap.xml`, `robots.txt`, and any absolute URLs in JSON-LD to use the new domain.

## Cost summary

| Piece | Service | Cost |
|---|---|---|
| Hosting + SSL + CDN | Cloudflare Pages | $0 |
| Contact form | Formsubmit.co | $0 |
| Auto-deploy from git | GitHub | $0 |
| Domain (when ready) | Cloudflare Registrar | ~$10/yr |

**Total: $0 today, ~$10/year once you add a domain.**

## Troubleshooting

- **CSS not loading**: confirm the `css/` folder made it into the repo (`git ls-files | grep css`).
- **Form submits but no email arrives**: did you click the Formsubmit activation link on the first submission? Check spam folder.
- **Clean URL redirects 404**: confirm `_redirects` is at the repo root and committed.
- **Build fails**: confirm build command is empty — this is a static site, no build needed.
- **Want a different form email**: edit the `action=` URL in `contact.html` to `https://formsubmit.co/<your-email>`.
