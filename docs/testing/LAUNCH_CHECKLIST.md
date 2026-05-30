# Pre-Launch Checklist
# BengalBound HUB — BengalBound Ltd
**Version:** 1.0 | **Date:** May 2026 | **Owner:** CTO + CEO

> Run this checklist before every market launch. Items marked [DONE] are already complete in the codebase.

---

## 1. Infrastructure

- [ ] Domain registered and pointing to Cloudflare DNS
- [ ] Netlify site live at `bengalbound.com` (public site)
- [ ] Render app live at `app.bengalbound.com` (Django backend)
- [ ] Supabase PostgreSQL connected (`DATABASE_URL` set in Render)
- [ ] SSL certificates active on all domains
- [ ] Custom 404 and 500 error pages working
- [ ] Health check endpoint `/` returns 200
- [ ] `ALLOWED_HOSTS` set correctly in production
- [ ] `DEBUG = False` confirmed in production
- [DONE] Whitenoise serving static files
- [ ] Media file storage configured (Cloudinary or S3 for uploads)

---

## 2. AI Agents

- [DONE] All 33 agent dashboards load (0 errors — tested with Playwright)
- [DONE] `GROQ_API_KEY` set and AI responding
- [DONE] `agent_chat()` works via litellm library (no proxy needed)
- [DONE] SereaBrain working with `llama-4-scout` (30k TPM)
- [ ] GROQ_API_KEY set in Render environment variables
- [ ] Test one live agent conversation in production
- [ ] `seed_agents` run — 33 agents in catalog
- [ ] `seed_modules` run — 83 modules available

---

## 3. Authentication & Security

- [DONE] Email + Google OAuth working (django-allauth)
- [DONE] 2FA (TOTP) available in console
- [DONE] IP lockout after 5 failed logins (django-axes)
- [DONE] HTTPS enforced
- [DONE] CSRF protection active
- [DONE] Field encryption working (FIELD_ENCRYPTION_KEY set)
- [ ] Test full signup → email verification → login flow
- [ ] Test Google OAuth in production
- [ ] Test 2FA setup and login
- [ ] Rate limiting on login endpoint

---

## 4. Public Site (Netlify)

- [DONE] `export_static` command works (all 12 pages exported)
- [DONE] `netlify.toml` configured
- [ ] All 12 pages loading on live Netlify URL
- [ ] Logo and images loading correctly
- [ ] Pricing page showing correct local prices
- [ ] Contact form submitting correctly
- [ ] Book Consultation form working
- [ ] Trial request form working
- [ ] Links to app (`/accounts/login/`, `/hub/`) working
- [ ] Mobile responsive on iPhone + Android
- [ ] Page speed score > 85 on Google PageSpeed

---

## 5. Payments

- [ ] Stripe account verified (live mode)
- [ ] `STRIPE_SECRET_KEY` + `STRIPE_PUBLISHABLE_KEY` set
- [ ] Test subscription purchase end-to-end
- [ ] Webhook handler receiving Stripe events
- [ ] Billing portal accessible from console
- [ ] Invoice PDF generating correctly
- [ ] Stripe Tax enabled for relevant regions
- [ ] SSLCommerz working (Bangladesh only)
- [ ] bKash payment tested (Bangladesh only)

---

## 6. Email

- [ ] SMTP credentials set (`EMAIL_HOST`, `EMAIL_HOST_USER`, etc.)
- [ ] Welcome email sending on signup
- [ ] Password reset email working
- [ ] Email verification link working
- [ ] From address is `noreply@bengalbound.com` (not @gmail)
- [ ] Emails not going to spam (check SPF/DKIM/DMARC)
- [ ] Unsubscribe link in all marketing emails

---

## 7. Legal & Compliance

- [ ] Privacy Policy page live at `/privacy/`
- [ ] Terms of Service page live at `/terms/`
- [ ] Cookie consent banner visible on first visit
- [ ] "Powered by AI" disclosure in agent chat interfaces
- [ ] GDPR data request contact published
- [ ] Company registration complete (RJSC Bangladesh / Wyoming LLC)
- [ ] TIN/VAT registered (Bangladesh)

---

## 8. Business Operations

- [ ] Support email configured and monitored (`support@bengalbound.com`)
- [ ] Status page live (e.g. status.bengalbound.com via BetterUptime free)
- [ ] Oncall/alerting set up for downtime
- [ ] Database backup schedule configured (Supabase auto-backups)
- [ ] Error monitoring set up (Sentry free tier)
- [ ] Analytics tracking live (Google Analytics 4 or Plausible)

---

## 9. Content

- [ ] At least 3 blog posts published
- [ ] Homepage hero content populated via CMS (HomepageContent model)
- [ ] Pricing tiers populated in database (AIEmployeeTier + HubPlanConfig)
- [ ] At least 6 services populated in Service model
- [ ] FAQ populated (minimum 5 questions)
- [ ] Demo video embedded on homepage

---

## 10. Pre-Launch Testing

Run these commands before going live:

```bash
# Full management check
python manage.py check --deploy --settings=bengalbound_core.settings.render

# Run Playwright agent tests
python scripts/test_agents_ui.py

# Test public site export
python manage.py export_static --settings=netlify_settings

# Check AI is working
python -c "
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'bengalbound_core.settings.development'
django.setup()
from agents.utils import agent_chat
print(agent_chat([{'role':'user','content':'hello'}]))
"
```

Expected: all 33 agents pass, AI responds, export completes with 12 pages.

---

## 11. Post-Launch (First 48 Hours)

- [ ] Monitor Render logs for errors (`render.com/logs`)
- [ ] Monitor Sentry for exceptions
- [ ] Check Supabase dashboard for DB connections
- [ ] Confirm first real user signup completes end-to-end
- [ ] Respond to first 10 support inquiries within 2 hours
- [ ] Monitor Groq API usage (stay within 30k TPM limit)
- [ ] Check Google Search Console for indexing
