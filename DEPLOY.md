# Deployment Walkthrough

Target: **Netlify**, git-connected to GitHub, free subdomain (`*.netlify.app`) for now.

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

## 2. Connect Netlify to GitHub

1. Go to https://app.netlify.com and sign in (use "Sign up with GitHub" if new).
2. Click **Add new site → Import an existing project → Deploy with GitHub**.
3. Authorize Netlify to access your repos (you can limit it to just this one).
4. Select `southern-barn-builders`.
5. Build settings — **leave everything blank**. Our `netlify.toml` already sets `publish = "."`.
6. Click **Deploy site**.

First deploy takes ~30 seconds. You'll get a URL like `https://zealous-curie-a1b2c3.netlify.app`.

## 3. Rename the site (optional)

1. In Netlify: **Site configuration → Change site name**.
2. Pick something like `southern-barn-builders` → `https://southern-barn-builders.netlify.app`.

## 4. Verify the quote form

The contact form is wired to **Netlify Forms**:

1. Submit a test quote on the live site.
2. In Netlify: **Forms** tab → you should see the submission.
3. Set up email notifications: **Forms → Settings and usage → Form notifications → Add notification → Email notification** → enter your real email.

If submissions don't appear, check: the hidden input `<input type="hidden" name="form-name" value="quote" />` must be inside `<form>`.

## 5. Auto-deploy on every push

From here on, every `git push origin main` triggers a new deploy automatically. You can preview branches with deploy previews by opening a PR.

## 6. Custom domain (later)

When you buy a domain:

1. Netlify: **Domain management → Add a domain** → enter the domain.
2. Follow the DNS instructions (either point nameservers to Netlify, or add a CNAME/A record at your registrar).
3. Netlify auto-provisions a free Let's Encrypt SSL cert.

## Troubleshooting

- **CSS not loading**: confirm the `css/` folder made it into the repo (`git ls-files | grep css`).
- **Form doesn't submit**: Netlify detects forms at deploy time — you must redeploy after adding/editing `<form>` tags.
- **Clean URL redirects 404**: check `netlify.toml` is at repo root and committed.
