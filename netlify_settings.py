"""
Settings for Netlify static export build.
Not used in production — only invoked by netlify.toml build command.
"""

import os

# Must be set before importing base (base.py requires it with no default)
os.environ.setdefault('SECRET_KEY', 'netlify-static-build-key-not-for-production')

from bengalbound_core.settings.base import *  # noqa: F401,F403,E402

DEBUG = False
ALLOWED_HOSTS = ['*']

# Isolated SQLite so the build never touches the dev db.sqlite3
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'netlify_build.db',  # noqa: F405
    }
}

# collectstatic will gather to netlify_dist/static/
STATIC_ROOT = BASE_DIR / 'netlify_dist' / 'static'  # noqa: F405

# Remove debug toolbar if present (not available in all envs)
INSTALLED_APPS = [a for a in INSTALLED_APPS if 'debug_toolbar' not in a]  # noqa: F405
MIDDLEWARE   = [m for m in MIDDLEWARE   if 'debug_toolbar' not in m]  # noqa: F405

# Disable axes lockouts during export client requests
AXES_ENABLED = False
