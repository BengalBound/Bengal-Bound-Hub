"""
bengalbound_core/settings/production.py
─────────────────────────────────────────
Production overrides — security-hardened, no .env file dependency.
Active when DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production

All secrets MUST be injected as OS environment variables on the server.
Do NOT commit a .env file to production. base.py calls environ.Env.read_env()
which is a no-op when the .env file doesn't exist.
"""

from .base import *  # noqa: F401, F403
import environ

env = environ.Env()

DEBUG = False

# ── Security hardening ────────────────────────────────────────────────────────
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000          # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# ── Static files — run `collectstatic` before deploying ──────────────────────
STATIC_ROOT = BASE_DIR / 'staticfiles'          # noqa: F405

# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True

# ── Database — PostgreSQL in production ──────────────────────────────────────
# Set DATABASE_URL in the server environment, e.g.:
#   postgres://user:password@host:5432/bengalbound
import dj_database_url
_db_url = env('DATABASE_URL', default='')
if _db_url:
    DATABASES = {'default': dj_database_url.config(default=_db_url, conn_max_age=600, ssl_require=True)}
# If DATABASE_URL is not set, falls back to base.py SQLite (not recommended for production).

# ── Logging ───────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'serea': {'level': 'INFO', 'handlers': ['console'], 'propagate': False},
        'django.security': {'level': 'WARNING', 'handlers': ['console'], 'propagate': False},
    },
}

# ── Celery — use Redis in production ─────────────────────────────────────────
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = False
