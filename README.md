# django-business-starter

[![tests](https://github.com/canugurfst/django-business-starter/actions/workflows/tests.yml/badge.svg)](https://github.com/canugurfst/django-business-starter/actions/workflows/tests.yml)

The Django setup I start every small-business website from. It covers the parts every one of those sites needs (deployment, security, SEO, an admin the owner can edit, a contact form that emails them), so each client project can focus on its own design and content.

It is deliberately small: one app, three content models, no frontend build step. Each decision below is something I can explain to a client or a reviewer.

**Stack:** Django 5.2 · Python 3.11 · PostgreSQL (SQLite locally) · WhiteNoise · Gunicorn · Postmark · Railway

---

## Quick start

```bash
git clone https://github.com/canugurfst/django-business-starter.git
cd django-business-starter
python -m venv env
env/Scripts/activate            # Windows; on macOS/Linux: source env/bin/activate
pip install -r requirements.txt

cp .env.example .env            # then put a real key in DJANGO_SECRET_KEY
python manage.py migrate
python manage.py seed_demo      # placeholder settings, pages and services
python manage.py createsuperuser
python manage.py runserver
```

Site: http://127.0.0.1:8000 · Admin: http://127.0.0.1:8000/admin/

Run the tests with `python manage.py test`.

---

## What's included

| Area | What you get |
|---|---|
| Settings | One env-driven `settings.py`, safe defaults, SQLite → Postgres via `DATABASE_URL` |
| Security | HTTPS redirect, HSTS, secure cookies, proxy-aware TLS, hidden admin path, refuses to boot without a secret key |
| Content admin | Site settings, pages and services the owner edits themselves, with publish toggles and ordering |
| SEO | `sitemap.xml`, `robots.txt`, meta descriptions, canonical URLs, Open Graph, LocalBusiness JSON-LD, www → apex redirect, noindex for previews |
| Contact form | Saved to the database, emailed via Postmark, honeypot spam filter, admin inbox |
| Tests + CI | 18 tests; GitHub Actions runs them and checks for missing migrations on every push |
| Deploy | `railway.json`: collectstatic on build, migrate on start, Gunicorn |

```
config/            project settings, URLs, WSGI
core/
  models.py        SiteSettings, Page, Service, ContactMessage
  admin.py         admin tuned for non-technical owners
  views.py         pages, contact form, robots.txt
  sitemaps.py      sitemap built from published content
  middleware.py    canonical host redirect, noindex header
  context_processors.py   site details + SEO values for every template
  emails.py        contact notification
  tests.py
static/css/        a neutral stylesheet each project replaces
```

---

## Why it's built this way

### One settings file, configured by environment variables

There is no `settings/dev.py` and `settings/prod.py`. The same code runs on my laptop and on Railway; only environment variables differ (`.env` locally, service variables in production).

- **One source of truth.** A split setup drifts: something fixed in `prod.py` is forgotten in `dev.py`, and the bug only shows up after deploying.
- **Safe defaults.** `DEBUG` is off unless explicitly set. If someone forgets to configure it, the site fails closed, not open.
- **No secret fallback.** If `DJANGO_SECRET_KEY` is missing, the app refuses to start. A hard-coded fallback key would be public the moment the repo is.

`.env.example` lists every variable with a comment on what it does.

### Security

When `DEBUG` is off:

- **HTTPS everywhere:** `SECURE_SSL_REDIRECT`, secure session and CSRF cookies.
- **Proxy-aware:** Railway terminates TLS and forwards plain HTTP, so `SECURE_PROXY_SSL_HEADER` tells Django the original request was HTTPS. Without it you get redirect loops.
- **HSTS starts at one hour,** not one year. A misconfigured domain with a one-year HSTS header locks visitors out for a year. Raise `DJANGO_HSTS_SECONDS` once HTTPS on the real domain is confirmed working. `includeSubDomains` and `preload` are opt-in for the same reason.
- **Admin is not at `/admin/`.** `DJANGO_ADMIN_URL` moves it, which cuts out most automated login attempts. It is also kept out of `robots.txt`, because robots.txt is public.
- **Always on:** `X-Frame-Options: DENY`, `nosniff`, a strict referrer policy, Django's CSRF and password validators.

A test runs `manage.py check --deploy` against the production configuration, so a regression fails CI.

### Content the owner can edit

Clients want to change their phone number or add a service without emailing a developer. The admin is set up for them, not for developers:

- **Site settings** (name, tagline, contact details) is a single entry; the admin link opens it directly instead of a list with one row.
- **Pages and services** have *published* and *order* toggles editable from the list view, so hiding or reordering doesn't mean deleting.
- **SEO fields** (meta title, meta description) are on every page and service, collapsed by default, with character limits that match what search engines show.
- **Body text is plain text** rendered with Django's `linebreaks` filter, which escapes HTML. Owners can't break the layout or inject scripts. A project that needs rich text adds an editor deliberately.
- **Pages can't take reserved URLs** like `services` or `contact`.

`seed_demo` fills an empty database with placeholder content. It only creates what is missing, so running it again never overwrites admin edits.

### SEO

The basics most small-business sites miss:

- **`sitemap.xml`** is generated from published pages and services, with `lastmod` taken from the last edit. Hide a service in the admin and it leaves the sitemap.
- **`robots.txt`** points to the sitemap.
- **Per-page meta description and title**, falling back to site-wide defaults.
- **Canonical URL** on every page from `SITE_URL`, plus Open Graph tags for link previews.
- **LocalBusiness structured data (JSON-LD)** built from the admin's site settings. It is escaped so a business name can't break out of the `<script>` tag (there's a test for that).
- **Canonical host:** with `CANONICAL_HOST=example.com`, `www.example.com` 301-redirects to `example.com`, so search engines see one site, not two.
- **Preview protection:** `SITE_NOINDEX=True` on a Railway preview sends `X-Robots-Tag: noindex` and a blocking `robots.txt`, so an unfinished site never gets indexed. Remove it at launch.

Clean URLs come from slugs: `/services/consulting/`, `/about/`.

### Contact form

- **Saved first, emailed second.** Each submission is stored in the database before the notification is sent. If the email provider is down, nothing is lost: it's in the admin inbox, flagged `email_sent = False`, and the failure is logged.
- **Reply-To is the visitor,** so the owner just hits reply.
- **Honeypot, not CAPTCHA.** A hidden field that people don't see and simple bots fill in. There's no friction for real visitors, and bots get the normal success page, so they can't tell they were filtered.
- **Post/redirect/get:** refreshing after sending doesn't send it twice.
- **Postmark via django-anymail** in production, console backend locally. Switching provider is a settings change, not a code change.

### Static and media files

WhiteNoise serves compressed, cache-busted static files straight from Gunicorn, so a site this size needs no nginx or CDN. Uploaded images go to `MEDIA_ROOT`. On Railway, mount a volume and point `MEDIA_ROOT` at it, or uploads disappear on redeploy.

---

## Deploying to Railway

1. Create a project from this GitHub repo and add a **PostgreSQL** service. Railway injects `DATABASE_URL`.
2. Set variables on the web service:

   | Variable | Example |
   |---|---|
   | `DJANGO_SECRET_KEY` | a freshly generated key |
   | `DJANGO_ADMIN_URL` | `manage-7f3k/` |
   | `SITE_NOINDEX` | `True` (until launch) |
   | `CONTACT_EMAIL` | where form notifications go |
   | `POSTMARK_SERVER_TOKEN`, `DEFAULT_FROM_EMAIL` | from Postmark, with a verified sender |

3. Deploy. `railway.json` runs `collectstatic` at build time, then `migrate` and Gunicorn on start.
4. Run `python manage.py seed_demo` and `createsuperuser` once (Railway shell, or locally against the database's public URL).
5. **At launch:** add the custom domain, set `SITE_URL`, `CANONICAL_HOST`, `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS`, remove `SITE_NOINDEX`, and submit `/sitemap.xml` in Google Search Console. A week later, raise `DJANGO_HSTS_SECONDS` to `31536000`.

Migrations run on every start, so a deploy that includes a schema change applies it before traffic arrives.

---

## Not included, on purpose

- **A frontend framework or build step.** Server-rendered templates are fast, accessible and cheap to maintain for brochure sites. Add one when a project needs it.
- **Multi-language.** Many of my sites are bilingual, but how (separate fields, `django-modeltranslation`, separate pages) depends on the client, so it isn't in the base.
- **Rich-text editing, a blog, analytics, cookie banners.** Each is a per-project decision.

---

## About

Built by Can Ugur, a freelance Django developer: [canugurfst.com](https://canugurfst.com). This is the base I extract from client work; client code and content stay in their own private repositories.

Licensed under the [MIT License](LICENSE).
