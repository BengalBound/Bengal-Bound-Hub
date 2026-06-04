"""
bengalbound_core/settings/development.py
─────────────────────────────────────────
Local development overrides.
Active when DJANGO_SETTINGS_MODULE=bengalbound_core.settings.development
(default set in manage.py so you never need to think about it locally).

⚠ Never run this in production — debug_toolbar leaks internals and
  DEBUG=True disables security hardening.
"""

from .base import *  # noqa: F401, F403

DEBUG = True
TESTING = True  # Enables mock Firebase token bypass in accounts/views.py

ALLOWED_HOSTS += [                              # noqa: F405
    '.localhost',
    '127.0.0.1',
    '.ngrok-free.dev',
    '.ngrok.io',
]

# ── Dev tools ─────────────────────────────────────────────────────────────────
INSTALLED_APPS += ['debug_toolbar']             # noqa: F405

MIDDLEWARE = [                                  # noqa: F405
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE                                  # noqa: F405

INTERNAL_IPS = ['127.0.0.1']

# ── Email — print to terminal, no SMTP needed ────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ACCOUNT_EMAIL_VERIFICATION = 'none'

# ── Celery — run tasks synchronously so no broker is required ────────────────
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── Cache — use local-memory instead of Redis for local dev ──────────────────
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# ── Test Database Override ───────────────────────────────────────────────────
import sys
if 'pytest' in sys.modules:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
