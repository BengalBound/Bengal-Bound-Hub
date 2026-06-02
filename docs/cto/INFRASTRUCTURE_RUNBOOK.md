# CTO Infrastructure Runbook
# BengalBound HUB — BengalBound Ltd
**Version:** 1.0 | **Date:** June 2026 | **Owner:** CTO

---

## Production Infrastructure Overview

| Service | Platform | Plan | Purpose |
|---|---|---|---|
| Django backend | Cloud Run | Free → Starter ($7/mo) | Main application server |
| Database | Supabase | Free (500MB) → Pro ($25/mo) | PostgreSQL |
| AI inference | Groq | Free (30k TPM) | All 33 AI agents |
| Static files | Whitenoise (via Cloud Run) | Free | CSS/JS/images |
| DNS + CDN | Cloudflare | Free | Edge layer, SSL |
| Email | Brevo | Free (300/day) | Transactional email |
| Error tracking | Sentry (planned) | Free | Exception monitoring |

---

## Critical Environment Variables (Cloud Run)

| Variable | Description | How to rotate |
|---|---|---|
| `SECRET_KEY` | Django secret key | Generate new, re-deploy |
| `FIELD_ENCRYPTION_KEY` | Fernet key for encrypted fields | **Never rotate** — data is lost |
| `DATABASE_URL` | Supabase postgres:// URI | Update in Cloud Run dashboard |
| `GROQ_API_KEY` | Groq AI inference key | Replace key in dashboard |
| `STRIPE_SECRET_KEY` | Payment processing | Replace, update Stripe webhooks |

---

## Cloud Run Deployment

### Auto-Deploy on Push
Cloud Run is connected to the `main` branch of `github.com/Adre-melech/BengalBound`. Any push to `main` triggers a new deployment.

### Manual Deploy Steps
```bash
# Trigger via Cloud Run dashboard or CLI
render deploy --service bengalbound-web
```

### Build Process (render.yaml)
```
pip install -r requirements.txt
python manage.py migrate --settings=bengalbound_core.settings.render
python manage.py seed_modules --settings=bengalbound_core.settings.render
python manage.py seed_agents --settings=bengalbound_core.settings.render
python manage.py collectstatic --no-input --settings=bengalbound_core.settings.render
```

### Cloud Run-Specific Settings (`settings/render.py`)
- `DEBUG = False`
- Whitenoise serves static files (no Nginx)
- Celery tasks run eagerly (no Redis needed)
- `AXES_ENABLED = False` (no persistent cache on free tier)
- Email falls back to console log if `EMAIL_HOST` not configured

---

## Database Management

### Connection
```bash
# Get connection string from Supabase dashboard
# Project Settings → Database → Connection String → URI
psql "postgres://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"
```

### Backup
Supabase auto-backs up on paid plans. On free tier, run manual exports weekly:
```bash
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

### Migration Safety Rules
1. Always run `migrate` on a separate deploy step before merging new models
2. Never use `--fake` migrations in production
3. Audit tables (`inspector_compliancecheck`) are INSERT-only — never run DELETE/UPDATE on them
4. Test migrations on a Supabase branch database before applying to production

---

## AI Infrastructure

### Current Setup (Dev + Cloud Run)
```
GROQ_API_KEY → litellm library → Groq API (llama-4-scout-17b, 30k TPM free)
```

No proxy server needed. All 33 agents share the 30k TPM free tier, which is sufficient for up to ~50 active tenants.

### Production Upgrade Path (VPS)

**Stage 1 (0–50 clients): Cloud Run + Groq free**
- Zero AI cost, zero infrastructure setup

**Stage 2 (50–200 clients): Hetzner CX42 + LiteLLM proxy**
```
Nginx → Gunicorn → LiteLLM proxy → Groq (paid) + OpenRouter
                                 → Ollama (local, zero variable cost)
```

**Stage 3 (200–1000 clients): Hetzner AX52 + Ollama**
```
Nginx → Gunicorn (Django) → LiteLLM proxy → Ollama (local llama3:8b)
Celery Worker → Redis
PostgreSQL (local, replicated)
```

### LiteLLM Config Template (for VPS)
```yaml
# /etc/litellm/config.yaml
model_list:
  - model_name: neural-chat
    litellm_params:
      model: ollama/mistral:7b
      api_base: http://localhost:11434
  - model_name: gemini/gemini-1.5-flash
    litellm_params:
      model: gemini/gemini-1.5-flash
      api_key: os.environ/GEMINI_API_KEY
  - model_name: groq/llama-4-scout
    litellm_params:
      model: groq/meta-llama/llama-4-scout-17b-16e-instruct
      api_key: os.environ/GROQ_API_KEY
```

---

## VPS Setup Commands (Hetzner)

```bash
# Initial server setup
apt update && apt upgrade -y
apt install -y python3.12 python3-pip postgresql nginx redis-server certbot

# Clone and setup
git clone https://github.com/Adre-melech/BengalBound.git /srv/bengalbound
cd /srv/bengalbound/dev-backoffice
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env with production values

# Migrations
DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production python manage.py migrate
DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production python manage.py seed_modules
DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production python manage.py seed_agents
DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production python manage.py collectstatic --no-input

# Start services
systemctl enable gunicorn celery nginx
systemctl start gunicorn celery nginx
```

---

## SSL / HTTPS

### Cloud Run + Cloudflare
Cloud Run provides free TLS. Cloudflare adds edge SSL. Set Cloudflare SSL mode to **Full (Strict)**.

### VPS (Let's Encrypt via Certbot)
```bash
certbot --nginx -d bengalbound.com -d www.bengalbound.com -d workspace.bengalbound.com -d console.bengalbound.com
```

---

## Security Checklist

- [ ] `SECRET_KEY` is at least 50 random characters, not committed to git
- [ ] `FIELD_ENCRYPTION_KEY` stored safely (loss = encrypted data permanently unreadable)
- [ ] `DEBUG = False` in production (render.py / production.py handle this)
- [ ] `ALLOWED_HOSTS` set explicitly
- [ ] Database on private network only (no public IP)
- [ ] Django admin only accessible from `workspace.` subdomain
- [ ] `AXES_ENABLED = True` in production (brute-force protection)
- [ ] Email verification re-enabled before launch
- [ ] Stripe webhooks using live keys and pointing to correct endpoint
- [ ] Cloudflare WAF + DDoS protection active

---

## Incident Response

### Site Down
1. Check Cloud Run dashboard → service logs
2. Check database status at Supabase dashboard
3. Check Groq status at status.groq.com
4. Roll back if recent deploy caused issue: Cloud Run → Deploys → Rollback

### AI Agents Not Responding
1. Check `GROQ_API_KEY` validity
2. Check Groq rate limits (30k TPM on free tier)
3. Check `inspector_compliancecheck` for unexpected blocks
4. Test with `python manage.py shell` → `agent_chat([{"role":"user","content":"test"}])`

### Data Breach Protocol
1. Immediately rotate `SECRET_KEY` and `FIELD_ENCRYPTION_KEY` (new key only — old data inaccessible)
2. Invalidate all sessions: `python manage.py clearsessions`
3. Revoke Stripe and OAuth keys
4. Notify affected tenants within 72 hours (GDPR requirement)
5. Document in `docs/compliance/` incident log

---

*BengalBound HUB — CTO Infrastructure Runbook v1.0 — June 2026*
