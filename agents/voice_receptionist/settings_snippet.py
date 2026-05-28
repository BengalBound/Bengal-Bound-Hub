# ============================================================
# Bengal Bound — Voice Receptionist Settings Snippet
# PASTE these blocks into your existing bengal_bound/settings.py
# ============================================================

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # already in your settings.py

# -----------------------------------------------------------
# 1. Add to INSTALLED_APPS
# -----------------------------------------------------------
# INSTALLED_APPS += [
#     'voice_receptionist',
#     'django_apscheduler',
# ]

# -----------------------------------------------------------
# 2. diskcache — replaces Redis for session / call state
# -----------------------------------------------------------
CACHES = {
    'default': {
        'BACKEND': 'diskcache.DjangoCache',
        'LOCATION': BASE_DIR / 'cache',
        'TIMEOUT': 300,
        'OPTIONS': {
            'size_limit': 2 ** 30,  # 1 GB max
        },
    }
}

# -----------------------------------------------------------
# 3. Gmail SMTP (Django email backend — free via Google One)
# -----------------------------------------------------------
EMAIL_BACKEND     = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST        = 'smtp.gmail.com'
EMAIL_PORT        = 587
EMAIL_USE_TLS     = True
EMAIL_HOST_USER   = os.environ.get('GMAIL_ADDRESS', '')
EMAIL_HOST_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')

# -----------------------------------------------------------
# 4. SQLite test database (Django automatically uses this for tests)
# -----------------------------------------------------------
# Add the 'TEST' key inside your existing DATABASES['default'] dict:
#
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': ...,
#         # ... your existing Postgres config ...
#         'TEST': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': BASE_DIR / 'test_db.sqlite3',
#         },
#     }
# }

# -----------------------------------------------------------
# 5. Firebase + Google Cloud + Twilio credentials
# -----------------------------------------------------------
FIREBASE_SERVICE_ACCOUNT      = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH', '')
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '')
GEMINI_API_KEY                 = os.environ.get('GEMINI_API_KEY', '')
TWILIO_ACCOUNT_SID             = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN              = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER            = os.environ.get('TWILIO_PHONE_NUMBER', '')
CALENDAR_ENCRYPTION_KEY        = os.environ.get('CALENDAR_FERNET_KEY', '')
GOOGLE_CALENDAR_CLIENT_ID      = os.environ.get('GOOGLE_CALENDAR_CLIENT_ID', '')
GOOGLE_CALENDAR_CLIENT_SECRET  = os.environ.get('GOOGLE_CALENDAR_CLIENT_SECRET', '')
GOOGLE_CALENDAR_REDIRECT_URI   = os.environ.get('GOOGLE_CALENDAR_REDIRECT_URI', '')

# -----------------------------------------------------------
# 6. App-level config
# -----------------------------------------------------------
DEFAULT_FORWARDING_NUMBER      = os.environ.get('DEFAULT_FORWARDING_NUMBER', '')
BUSINESS_OWNER_EMAIL           = os.environ.get('BUSINESS_OWNER_EMAIL', '')

# -----------------------------------------------------------
# 7. DRF — APPEND FirebaseAuthentication (do not replace existing)
# -----------------------------------------------------------
# REST_FRAMEWORK = {
#     'DEFAULT_AUTHENTICATION_CLASSES': [
#         'rest_framework.authentication.SessionAuthentication',  # keep existing
#         'rest_framework.authentication.TokenAuthentication',    # keep existing (if used)
#         'voice_receptionist.auth.FirebaseAuthentication',       # <-- ADD THIS
#     ],
#     # ... rest of your DRF config unchanged ...
# }
