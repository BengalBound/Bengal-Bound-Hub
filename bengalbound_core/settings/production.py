"""
bengalbound_core/settings/production.py
─────────────────────────────────────────
Production settings — Google Cloud Run, Render, or any container host.
DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production

All secrets injected as environment variables. No .env file in production.
"""

import os

# Safe fallbacks so the container starts even if an env var is missing.
# Override all of these in Cloud Run → Variables & Secrets.
os.environ.setdefault('SECRET_KEY', 'insecure-default-change-in-cloud-run')
os.environ.setdefault('FIELD_ENCRYPTION_KEY', 'dD0JVWMzh1pqJfZkyI1KDrehE7SL9qzMjYwKILQPsSQ=')

from .base import *  # noqa: F401, F403
import dj_database_url

DEBUG = False

_raw_hosts = os.environ.get('ALLOWED_HOSTS', '').strip()
# Clean up bracket/quote syntax if entered as literal arrays by mistake
_raw_hosts = _raw_hosts.replace('[', '').replace(']', '').replace('"', '').replace("'", "")
ALLOWED_HOSTS = [h.strip() for h in _raw_hosts.split(',') if h.strip()]

# Robust wildcard fallback for Cloud Run & localhost
if not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS:
    ALLOWED_HOSTS = ['*']
else:
    # Ensure it always matches run.app and local hosts
    ALLOWED_HOSTS.extend(['.run.app', 'localhost', '127.0.0.1'])

CSRF_TRUSTED_ORIGINS = [
    'https://*.run.app',           # Google Cloud Run
    'https://*.bengalbound.com',   # Production domain
    'https://bengalbound.com',
]
# Append any extra origins from env: CSRF_TRUSTED_ORIGINS=https://myapp.run.app
_extra = os.environ.get('CSRF_TRUSTED_ORIGINS_EXTRA', '')
if _extra:
    CSRF_TRUSTED_ORIGINS += [u.strip() for u in _extra.split(',') if u.strip()]

# ── Security ──────────────────────────────────────────────────────────────────
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

# ── Static files — whitenoise serves directly from gunicorn ──────────────────
from pathlib import Path
STATIC_ROOT = Path('/tmp/staticfiles')
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

# ── Database ──────────────────────────────────────────────────────────────────
_db_url = os.environ.get('DATABASE_URL', '')
if _db_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_db_url,
            conn_max_age=600,
            ssl_require='sslmode' not in _db_url,
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

# ── Email — Brevo SMTP (free 300/day) or any SMTP ────────────────────────────
# Brevo setup: https://app.brevo.com → Transactional → SMTP & API
# Set EMAIL_HOST, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD in Cloud Run env vars
if os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND      = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST         = os.environ['EMAIL_HOST']
    EMAIL_HOST_USER    = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    EMAIL_PORT         = int(os.environ.get('EMAIL_PORT', 587))
    EMAIL_USE_TLS      = True
    DEFAULT_FROM_EMAIL = os.environ.get(
        'DEFAULT_FROM_EMAIL', f'BengalBound <noreply@bengalbound.com>'
    )
else:
    # No SMTP configured — emails go to Cloud Run logs (safe fallback)
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# ── Celery — use Redis if available, otherwise run tasks synchronously ────────
_redis = os.environ.get('REDIS_URL', '')
if _redis:
    CELERY_BROKER_URL        = _redis
    CELERY_RESULT_BACKEND    = _redis
    CELERY_TASK_ALWAYS_EAGER = False
else:
    CELERY_BROKER_URL        = 'memory://'
    CELERY_RESULT_BACKEND    = 'cache+memory://'
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True

# ── Remove debug toolbar ──────────────────────────────────────────────────────
INSTALLED_APPS = [a for a in INSTALLED_APPS if 'debug_toolbar' not in a]  # noqa: F405
MIDDLEWARE     = [m for m in MIDDLEWARE if 'debug_toolbar' not in m]

# ── Axes — disable if no persistent cache ─────────────────────────────────────
if not _redis:
    AXES_ENABLED = False

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{levelname} {asctime} {module} {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'serea':           {'level': 'INFO',    'handlers': ['console'], 'propagate': False},
        'django.security': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
    },
}
