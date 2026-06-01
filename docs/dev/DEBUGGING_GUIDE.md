# Developer Debugging Guide
# BengalBound HUB — BengalBound Ltd
**Version:** 1.0 | **Date:** June 2026 | **Audience:** Backend Developers

---

## Common Issues & Fixes

### 1. `no such table` on startup

**Symptom:** `django.db.utils.OperationalError: no such table: hub_businessinstance`

**Cause:** Migrations haven't run, or APScheduler starts before migrations complete.

**Fix:**
```bash
python manage.py migrate
python manage.py seed_modules
python manage.py seed_agents
```

APScheduler is guarded against management commands in `hub/apps.py` — it won't start during `migrate` or `collectstatic`.

---

### 2. Email verification blocking signup

**Symptom:** After signup, users are stuck on a "verify your email" screen and never get an email.

**Cause:** `ACCOUNT_EMAIL_VERIFICATION` is set to `'mandatory'` but no email backend is configured.

**Dev fix:** In `.env`:
```bash
# Disable email verification in dev
ACCOUNT_EMAIL_VERIFICATION=none
```

Or in `base.py` (temporary, revert before production):
```python
ACCOUNT_EMAIL_VERIFICATION = 'none'
```

**Production requirement:** Set `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` and use `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'`.

---

### 3. BusinessAccessMiddleware 403 on new URL pattern

**Symptom:** A new suite-first URL like `/hub/erp/<slug>/` returns 403 or redirects unexpectedly.

**Cause:** `BusinessAccessMiddleware` reads the first path segment after `/hub/` as the business slug.

**Fix:** Add the prefix to `_SKIP_SEGMENTS` in `hub/middleware.py`:
```python
_SKIP_SEGMENTS = {'erp', 'ai', 'onboard', ...}  # add your prefix here
```

---

### 4. Agent AI calls failing with 401

**Symptom:** `requests.exceptions.HTTPError: 401 Client Error` from `agent_chat()`.

**Cause:** `GROQ_API_KEY` is missing or wrong in `.env`.

**Fix:**
```bash
# .env
GROQ_API_KEY=gsk_...your_key_here
```

Get a free key at [console.groq.com](https://console.groq.com). The free tier gives 30,000 tokens/min which is enough for all 33 agents.

---

### 5. Static files 404 in development

**Symptom:** CSS/JS returning 404, page looks unstyled.

**Fix:**
```bash
python manage.py collectstatic --settings=bengalbound_core.settings.development
```

Or ensure `DEBUG=True` in `.env` — Django serves static files automatically in debug mode via `django.contrib.staticfiles`.

---

### 6. `CSRF token missing or incorrect`

**Symptom:** POST requests return 403 CSRF error.

**Cause:** The dev server is running on a port not in `CSRF_TRUSTED_ORIGINS`.

**Fix:** Always run on port 1234:
```bash
python manage.py runserver 0.0.0.0:1234
```

`CSRF_TRUSTED_ORIGINS` in `base.py` is set to `http://localhost:1234` and `http://127.0.0.1:1234`.

---

### 7. Subdomain routing not working locally

**Symptom:** `workspace.localhost:1234` routes to the main site instead of workspace admin.

**Fix:** Add to `C:\Windows\System32\drivers\etc\hosts` (run as Administrator):
```
127.0.0.1  workspace.localhost
127.0.0.1  console.localhost
127.0.0.1  community.localhost
```

---

### 8. Inspector blocking legitimate agent actions

**Symptom:** Agent actions return 403 with an Inspector compliance block.

**Debug steps:**
1. Check `inspector_compliancecheck` table for the blocking reason
2. Review the 5-check pipeline: Legal → Ethics → Cybersecurity → Data Privacy → Harm Prevention
3. The agent's `system_prompt` or input likely contains a flagged pattern

**Never disable Inspector in production.** In dev, you can temporarily set `INSPECTOR_BYPASS_KEY` (see `inspector/middleware.py`).

---

## Dev Tools & Commands

```bash
# Run dev server (always use port 1234)
python manage.py runserver 0.0.0.0:1234

# Open Django shell
python manage.py shell

# Reset and re-seed everything
python manage.py flush --no-input
python manage.py migrate
python manage.py seed_modules
python manage.py seed_agents
python manage.py createsuperuser

# Create a test business instance via shell
from hub.models import BusinessInstance
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.first()
biz = BusinessInstance.objects.create(owner=user, name="Test Co", slug="test-co")

# Check Inspector audit log
from inspector.models import ComplianceCheck
ComplianceCheck.objects.order_by('-created_at')[:10]
```

---

## Environment Variable Reference

| Variable | Dev default | Required? |
|---|---|---|
| `DEBUG` | `True` | Yes |
| `SECRET_KEY` | any string | Yes |
| `GROQ_API_KEY` | from console.groq.com | Yes (for AI) |
| `DATABASE_URL` | blank → SQLite | No (prod only) |
| `FIELD_ENCRYPTION_KEY` | generate with Fernet | Yes |
| `ACCOUNT_EMAIL_VERIFICATION` | `none` | Dev only |
| `LITELLM_BASE_URL` | blank → direct Groq | No |

---

## Useful Django Admin URLs (dev)

```
http://workspace.localhost:1234/django-admin/
http://workspace.localhost:1234/workspace/dashboard/
http://console.localhost:1234/console/
http://localhost:1234/hub/<your-slug>/
```

---

*BengalBound HUB — Developer Debugging Guide v1.0 — June 2026*
