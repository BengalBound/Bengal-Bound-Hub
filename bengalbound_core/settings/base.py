"""
bengalbound_core/settings/base.py
──────────────────────────────────
Shared settings loaded by both development.py and production.py.
Contains NO environment-specific or secret values — those live in
the subclass files and are injected via environment variables.

Never import this file directly. Use:
  DJANGO_SETTINGS_MODULE=bengalbound_core.settings.development  (local)
  DJANGO_SETTINGS_MODULE=bengalbound_core.settings.production   (server)
"""

from pathlib import Path
import os
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Environment ───────────────────────────────────────────────────────────────
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
)
# In production, remove this line and inject secrets via the OS environment.
# The .env file is gitignored and only used locally.
environ.Env.read_env(BASE_DIR / '.env')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

SECRET_KEY = env('SECRET_KEY')                     # required — no default

DEBUG = env('DEBUG')                                # False by default (safe)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])

# ── Installed apps ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.facebook',
    'allauth.socialaccount.providers.github',

    'axes',
    'simple_history',
    'django_otp',
    'django_otp.plugins.otp_totp',

    # Custom apps
    'accounts',
    'public_site',
    'workspace_admin',
    'console_admin',
    'community_forum',
    'serea',
    'booking_calendar',
    'hub.apps.HubConfig',

    # Modules — Project Management
    'modules.projects',

    # Modules — Factory Operations Hub
    'modules.factory_ops',

    # Modules — core collaboration
    'modules.task_board',
    'modules.team_chat',

    # Modules — CRM & Sales
    'modules.crm',
    'modules.leads',
    'modules.invoicing',
    'modules.contracts',

    # Modules — HR & People
    'modules.hr',
    'modules.payroll',
    'modules.recruitment',
    'modules.attendance',
    'modules.shift_planning',
    'modules.training',
    'modules.expense',

    # Modules — Finance
    'modules.accounting',
    'modules.budgeting',
    'modules.financials',

    # Modules — Operations
    'modules.inventory',
    'modules.order_mgmt',
    'modules.bom',
    'modules.production',
    'modules.quality_control',
    'modules.maintenance',
    'modules.delivery',

    # Modules — Commerce
    'modules.pos',
    'modules.ecommerce',
    'modules.loyalty',
    'modules.booking',
    'modules.table_mgmt',

    # Modules — Marketing & Comms
    'modules.email_marketing',
    'modules.announcements',
    'modules.documents',
    'modules.website',

    # Modules — Intelligence
    'modules.reports',
    'modules.ai_analytics',
    'modules.ai_assistant',
    'modules.dashboard_pro',

    # Modules — Creation Suite
    'modules.docs',
    'modules.sheets',
    'modules.slides',
    'modules.forms_builder',

    # Modules — Communication & Productivity
    'modules.business_mail',
    'modules.video_meet',
    'modules.cloud_drive',
    'modules.business_calendar',

    # Modules — Manufacturing & Industrial
    'modules.erp',
    'modules.mes',
    'modules.plm',
    'modules.cadcam',
    'modules.asset_management',

    # Modules — Automotive
    'modules.workshop',
    'modules.dms',
    'modules.dvi',

    # Modules — Logistics & Supply Chain
    'modules.tms',
    'modules.wms',

    # Modules — Consulting & Analytics
    'modules.data_studio',
    'modules.process_mapper',

    # Modules — Education
    'modules.sis',
    'modules.lms',
    'modules.assessments',
    'modules.timetable',
    'modules.parent_portal',

    # Modules — Real Estate
    'modules.property_listings',
    'modules.deal_flow',
    'modules.commission',
    'modules.re_marketing',
    'modules.re_client_portal',

    # Modules — Retail & Wholesale
    'modules.omnichannel',
    'modules.planogram',
    'modules.product_catalog',
    'modules.b2b_portal',
    'modules.store_ops',

    # Modules — Travel & Accommodation
    'modules.pms',
    'modules.channel_manager',
    'modules.rate_manager',
    'modules.travel_crm',
    'modules.group_bookings',
    'modules.travel_desk',
    'modules.hospitality_ops',

    # Modules — Personal Care & Home & Garden
    'modules.care_manager',
    'modules.garden_ops',
    'modules.data_collection',
]

AUTH_USER_MODEL = 'accounts.User'

# ── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'axes.middleware.AxesMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
    'bengalbound_core.middleware.SubdomainRoutingMiddleware',
    'hub.middleware.BusinessAccessMiddleware',
]

# Trusted proxies for safe IP detection (empty = trust REMOTE_ADDR only)
TRUSTED_PROXIES = env.list('TRUSTED_PROXIES', default=[])

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:1234',
    'http://workspace.localhost:1234',
    'http://console.localhost:1234',
    'http://community.localhost:1234',
    'http://127.0.0.1:1234',
]

ROOT_URLCONF = 'bengalbound_core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'console_admin.context_processors.console_modules_processor',
                'hub.context_processors.hub_context',
            ],
            'builtins': [
                'console_admin.templatetags.console_tags',
            ],
        },
    },
]

WSGI_APPLICATION = 'bengalbound_core.wsgi.application'

# ── Database ──────────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ── Password validation ───────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ── Internationalisation ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ── Static & media ────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

DEFAULT_FROM_EMAIL = 'noreply@bengalbound.local'

# ── Serea AI Engine ───────────────────────────────────────────────────────────
GROQ_API_KEY               = env('GROQ_API_KEY', default='')
OPENAI_API_KEY             = env('OPENAI_API_KEY', default='')
OPENROUTER_API_KEY         = env('OPENROUTER_API_KEY', default='')
GOOGLE_SERVICE_ACCOUNT_JSON = env('GOOGLE_SERVICE_ACCOUNT_JSON', default='')

FACEBOOK_WEBHOOK_VERIFY_TOKEN = env('FACEBOOK_WEBHOOK_VERIFY_TOKEN')  # required
FACEBOOK_APP_ID             = env('FACEBOOK_CLIENT_ID', default='')
FACEBOOK_APP_SECRET         = env('FACEBOOK_CLIENT_SECRET', default='')
FACEBOOK_OAUTH_REDIRECT_URI = env('FACEBOOK_OAUTH_REDIRECT_URI', default='')

# ── LiteLLM ───────────────────────────────────────────────────────────────────
LITELLM_BASE_URL   = env('LITELLM_BASE_URL',   default='https://ai.neurolinkit.com/v1')
LITELLM_MASTER_KEY = env('LITELLM_MASTER_KEY')  # required
SEREA_TASK_MODELS  = {
    'chat':       env('SEREA_MODEL_CHAT',       default='neural-chat'),
    'moderation': env('SEREA_MODEL_MODERATION', default='dolphin-mistral'),
    'content':    env('SEREA_MODEL_CONTENT',    default='glm4'),
    'analysis':   env('SEREA_MODEL_ANALYSIS',   default='qwen2.5-coder'),
    'quick':      env('SEREA_MODEL_QUICK',      default='phi4-mini'),
}

# ── Encryption ────────────────────────────────────────────────────────────────
FIELD_ENCRYPTION_KEY = env('FIELD_ENCRYPTION_KEY', default='')

# ── Celery ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='memory://')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='cache+memory://')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

if CELERY_BROKER_URL == 'memory://':
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_STORE_EAGER_RESULT = True

CELERY_BEAT_SCHEDULE = {
    'serea-monitor-all': {
        'task': 'serea.tasks.dispatch_monitor_to_all_agents',
        'schedule': 600,
    },
    'serea-content-all': {
        'task': 'serea.tasks.dispatch_content_to_all_agents',
        'schedule': 300,
    },
    'serea-briefing-all': {
        'task': 'serea.tasks.dispatch_briefing_to_all_agents',
        'schedule': 86400,
    },
    'serea-report-all': {
        'task': 'serea.tasks.dispatch_reports_to_all_agents',
        'schedule': 86400,
    },
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# ── Django Axes ───────────────────────────────────────────────────────────────
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = 1
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = None

# ── Allauth ───────────────────────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'axes.backends.AxesStandaloneBackend',
]

SITE_ID = 1

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': env('GOOGLE_CLIENT_ID', default=''),
            'secret': env('GOOGLE_CLIENT_SECRET', default=''),
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
    'facebook': {
        'APP': {
            'client_id': env('FACEBOOK_CLIENT_ID', default=''),
            'secret': env('FACEBOOK_CLIENT_SECRET', default=''),
            'key': ''
        },
        'METHOD': 'oauth2',
        'SCOPE': ['email', 'public_profile'],
        'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
        'INIT_PARAMS': {'cookie': True},
        'FIELDS': ['id', 'first_name', 'last_name', 'middle_name', 'name',
                   'name_format', 'picture', 'short_name'],
        'EXCHANGE_TOKEN': True,
        'VERIFIED_EMAIL': False,
        'VERSION': 'v13.0',
    },
    'github': {
        'APP': {
            'client_id': env('GITHUB_CLIENT_ID', default=''),
            'secret': env('GITHUB_CLIENT_SECRET', default=''),
        }
    }
}
