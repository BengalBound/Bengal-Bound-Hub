"""
bengalbound_core/settings/render.py
────────────────────────────────────
Free-tier Render deployment settings.
Set DJANGO_SETTINGS_MODULE=bengalbound_core.settings.render in Render dashboard.

Required env vars (set in Render → Environment):
  SECRET_KEY          — any long random string (Render can generate this)
  DATABASE_URL        — postgres:// URL from Supabase (or Render Postgres)

Optional env vars:
  FIELD_ENCRYPTION_KEY — valid Fernet key; defaults to a safe build key below
  ALLOWED_HOSTS        — comma-separated hostnames; defaults to * (fine for Render)
  EMAIL_HOST / EMAIL_HOST_USER / EMAIL_HOST_PASSWORD / EMAIL_PORT
                       — if not set, emails go to the console log only
  REDIS_URL            — if set, Celery uses it; otherwise tasks run synchronously
"""

import os

# Safe defaults — override in Render environment variables for real security
os.environ.setdefault('SECRET_KEY', 'change-me-in-render-dashboard')
os.environ.setdefault('FIELD_ENCRYPTION_KEY', 'HJjlUIRoq5d30B8h1dgdujtx5WscrJqJjEc4tWP5Kdg=')

from .base import *  # noqa: F401, F403, E402

import dj_database_url  # noqa: E402

DEBUG = False

_raw_hosts = os.environ.get('ALLOWED_HOSTS', '').strip()
_raw_hosts = _raw_hosts.replace('[', '').replace(']', '').replace('"', '').replace("'", "")
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]
if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS.extend(['.run.app', 'localhost', '127.0.0.1'])

# ── HTTPS (Render terminates SSL at the proxy layer) ──────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

CSRF_TRUSTED_ORIGINS = [
    'https://*.onrender.com',
    'https://*.netlify.app',
    'https://*.bengalbound.com',
]

# ── Database — Supabase (or any DATABASE_URL) ─────────────────────────────────
_db_url = os.environ.get('DATABASE_URL', '')
if _db_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_db_url,
            conn_max_age=600,
            ssl_require=True,
        )
    }
else:
    # Ephemeral SQLite in /tmp for guaranteed write permissions in containerized environments
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/tmp/db.sqlite3',
        }
    }

# ── Static files — whitenoise serves them from gunicorn ───────────────────────
# Insert whitenoise right after SecurityMiddleware
_security_idx = next(
    (i for i, m in enumerate(MIDDLEWARE) if 'SecurityMiddleware' in m), 0  # noqa: F405
)
MIDDLEWARE = (  # noqa: F405
    MIDDLEWARE[:_security_idx + 1]  # noqa: F405
    + ['whitenoise.middleware.WhiteNoiseMiddleware']
    + MIDDLEWARE[_security_idx + 1:]  # noqa: F405
)
# Robust fallback: use manifest storage if manifest exists, otherwise basic storage to prevent startup crash
if (STATIC_ROOT / 'staticfiles.json').exists():
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'

# ── Celery — run synchronously unless Redis is available ──────────────────────
_redis_url = os.environ.get('REDIS_URL', '')
if _redis_url:
    CELERY_BROKER_URL = _redis_url
    CELERY_RESULT_BACKEND = _redis_url
    CELERY_TASK_ALWAYS_EAGER = False
else:
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# ── Email — console log unless SMTP is configured ────────────────────────────
if os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ['EMAIL_HOST']
    EMAIL_HOST_USER = os.environ['EMAIL_HOST_USER']
    EMAIL_HOST_PASSWORD = os.environ['EMAIL_HOST_PASSWORD']
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS = True
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── Axes — disable IP lockouts on free tier (no persistent cache) ─────────────
AXES_ENABLED = False

# ── Remove debug toolbar ──────────────────────────────────────────────────────
INSTALLED_APPS = [a for a in INSTALLED_APPS if 'debug_toolbar' not in a]  # noqa: F405
MIDDLEWARE = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]
