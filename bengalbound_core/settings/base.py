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
    'rest_framework',

    # Custom apps
    'accounts',
    'public_site',
    'workspace_admin',
    'console_admin',
    'community_forum',
    'serea',
    'booking_calendar',
    'hub.apps.HubConfig',
    'agents',
    'agents.aria',
    'agents.crux',
    'agents.mira',
    'agents.lead_hunter',
    'agents.atlas',
    'agents.babel',
    'agents.cash',
    'agents.clarity',
    'agents.concierge',
    'agents.content_architect',
    'agents.dox',
    'agents.flux',
    'agents.hera',
    'agents.kai',
    'agents.luma',
    'agents.medibook',
    'agents.merch',
    'agents.nexus',
    'agents.nova',
    'agents.oracle',
    'agents.payload',
    'agents.pulse',
    'agents.realt',
    'agents.reporting_bot',
    'agents.sage',
    'agents.scout',
    'agents.shield',
    'agents.tempo',
    'agents.voice_receptionist',
    'agents.content_strategist',


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
STATIC_ROOT = BASE_DIR / 'staticfiles'

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

FACEBOOK_WEBHOOK_VERIFY_TOKEN = env('FACEBOOK_WEBHOOK_VERIFY_TOKEN', default='')
FACEBOOK_APP_ID             = env('FACEBOOK_CLIENT_ID', default='')
FACEBOOK_APP_SECRET         = env('FACEBOOK_CLIENT_SECRET', default='')
FACEBOOK_OAUTH_REDIRECT_URI = env('FACEBOOK_OAUTH_REDIRECT_URI', default='')

# ── LiteLLM ───────────────────────────────────────────────────────────────────
LITELLM_BASE_URL   = env('LITELLM_BASE_URL',   default='https://ai.neurolinkit.com/v1')
LITELLM_MASTER_KEY = env('LITELLM_MASTER_KEY', default='')
SEREA_TASK_MODELS  = {
    'chat':       env('SEREA_MODEL_CHAT',       default='neural-chat'),
    'moderation': env('SEREA_MODEL_MODERATION', default='dolphin-mistral'),
    'content':    env('SEREA_MODEL_CONTENT',    default='glm4'),
    'analysis':   env('SEREA_MODEL_ANALYSIS',   default='qwen2.5-coder'),
    'quick':      env('SEREA_MODEL_QUICK',      default='phi4-mini'),
    'gemini':     env('GEMINI_MODEL',           default='gemini/gemini-1.5-flash'),
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
    # ── Serea platform engine (social/webhook layer) ──────────────────────────
    'serea-monitor-all':  {'task': 'serea.tasks.dispatch_monitor_to_all_agents',  'schedule': 600},
    'content-strategist-all':  {'task': 'serea.tasks.dispatch_content_to_all_agents',  'schedule': 300},
    'serea-briefing-all': {'task': 'serea.tasks.dispatch_briefing_to_all_agents', 'schedule': 86400},
    'serea-report-all':   {'task': 'serea.tasks.dispatch_reports_to_all_agents',  'schedule': 86400},

    # ── Aria — Customer Support ───────────────────────────────────────────────
    'aria-sla-check':        {'task': 'agents.aria.sla_breach_check',       'schedule': 1800},   # every 30 min
    'aria-auto-resolve':     {'task': 'agents.aria.auto_resolve_tickets',   'schedule': 14400},  # every 4 hr
    'aria-digest':           {'task': 'agents.aria.daily_support_digest',   'schedule': 86400},  # daily

    # ── Atlas — Executive Assistant ───────────────────────────────────────────
    'atlas-morning-brief':   {'task': 'agents.atlas.morning_briefing',      'schedule': 86400},
    'atlas-overdue-tasks':   {'task': 'agents.atlas.overdue_task_alert',    'schedule': 86400},
    'atlas-weekly-summary':  {'task': 'agents.atlas.weekly_summary',        'schedule': 604800},

    # ── Babel — Translation ───────────────────────────────────────────────────
    'babel-process-jobs':    {'task': 'agents.babel.process_queued_jobs',   'schedule': 3600},   # every 1 hr
    'babel-retry-failed':    {'task': 'agents.babel.retry_failed_jobs',     'schedule': 604800},

    # ── Cash — Payroll ────────────────────────────────────────────────────────
    'cash-payroll-reminder': {'task': 'agents.cash.monthly_payroll_reminder', 'schedule': 86400},
    'cash-anomaly-check':    {'task': 'agents.cash.anomaly_check_all',      'schedule': 86400},

    # ── Clarity — Feedback Analyst ────────────────────────────────────────────
    'clarity-score-themes':  {'task': 'agents.clarity.auto_score_themes',        'schedule': 86400},
    'clarity-weekly-digest': {'task': 'agents.clarity.weekly_insight_digest',    'schedule': 604800},

    # ── Concierge — Client Reception ─────────────────────────────────────────
    'concierge-process-emails':  {'task': 'agents.concierge.process_unclassified_emails', 'schedule': 7200},
    'concierge-follow-up':       {'task': 'agents.concierge.follow_up_pending_meetings',  'schedule': 86400},
    'concierge-inbox-digest':    {'task': 'agents.concierge.daily_inbox_digest',          'schedule': 86400},

    # ── Content Architect — Editorial Planner ─────────────────────────────────
    'content-arch-generate':    {'task': 'agents.content_architect.auto_generate_planned_entries', 'schedule': 86400},
    'content-arch-reminders':   {'task': 'agents.content_architect.publishing_reminders',         'schedule': 86400},

    # ── Crux — CRM Manager ───────────────────────────────────────────────────
    'crux-score-contacts':    {'task': 'agents.crux.score_new_contacts',    'schedule': 86400},
    'crux-pipeline-review':   {'task': 'agents.crux.daily_pipeline_review', 'schedule': 86400},
    'crux-dormant-alert':     {'task': 'agents.crux.dormant_contact_alert', 'schedule': 86400},

    # ── Dox — Technical Writer ────────────────────────────────────────────────
    'dox-scan-outdated':     {'task': 'agents.dox.scan_outdated_docs',         'schedule': 604800},
    'dox-auto-generate':     {'task': 'agents.dox.auto_generate_empty_pages',  'schedule': 86400},

    # ── Flux — Supply Chain ───────────────────────────────────────────────────
    'flux-overdue-po':          {'task': 'agents.flux.overdue_po_alert',             'schedule': 86400},
    'flux-supplier-review':     {'task': 'agents.flux.supplier_performance_review',  'schedule': 604800},

    # ── Hera — HR Agent ──────────────────────────────────────────────────────
    'hera-answer-queries':      {'task': 'agents.hera.auto_answer_pending_queries', 'schedule': 86400},
    'hera-onboarding-check':    {'task': 'agents.hera.overdue_onboarding_check',    'schedule': 86400},
    'hera-onboarding-status':   {'task': 'agents.hera.weekly_onboarding_status',    'schedule': 604800},

    # ── Kai — DevOps Engineer ─────────────────────────────────────────────────
    'kai-pipeline-health':      {'task': 'agents.kai.pipeline_health_monitor',      'schedule': 1800},  # every 30 min
    'kai-analyze-incidents':    {'task': 'agents.kai.auto_analyze_open_incidents',  'schedule': 86400},
    'kai-devops-digest':        {'task': 'agents.kai.daily_devops_digest',          'schedule': 86400},

    # ── Lead Hunter — B2B Prospector ─────────────────────────────────────────
    'lead-hunter-score':        {'task': 'agents.lead_hunter.score_new_prospects',     'schedule': 86400},
    'lead-hunter-sequences':    {'task': 'agents.lead_hunter.activate_ready_sequences','schedule': 86400},
    'lead-hunter-digest':       {'task': 'agents.lead_hunter.weekly_pipeline_digest',  'schedule': 604800},

    # ── Luma — Brand & PR ─────────────────────────────────────────────────────
    'luma-crisis-check':        {'task': 'agents.luma.crisis_alert_check',       'schedule': 1800},   # every 30 min
    'luma-scan-mentions':       {'task': 'agents.luma.scan_unanalysed_mentions', 'schedule': 86400},
    'luma-brand-digest':        {'task': 'agents.luma.weekly_brand_digest',      'schedule': 604800},

    # ── MediBook — Medical Scheduler ─────────────────────────────────────────
    'medibook-reminders':       {'task': 'agents.medibook.send_appointment_reminders', 'schedule': 3600},
    'medibook-no-shows':        {'task': 'agents.medibook.no_show_followup',           'schedule': 86400},
    'medibook-notes':           {'task': 'agents.medibook.generate_missing_notes',     'schedule': 86400},

    # ── Merch — eCommerce Manager ─────────────────────────────────────────────
    'merch-low-stock':          {'task': 'agents.merch.low_stock_alert',           'schedule': 86400},
    'merch-optimise-listings':  {'task': 'agents.merch.daily_listing_optimisation','schedule': 86400},
    'merch-reorder-check':      {'task': 'agents.merch.reorder_check',             'schedule': 86400},

    # ── Mira — Customer Success ───────────────────────────────────────────────
    'mira-at-risk-alert':       {'task': 'agents.mira.at_risk_customer_alert',  'schedule': 86400},
    'mira-generate-emails':     {'task': 'agents.mira.generate_pending_emails', 'schedule': 86400},
    'mira-health-digest':       {'task': 'agents.mira.weekly_health_digest',    'schedule': 604800},

    # ── Nexus — L&D Coordinator ───────────────────────────────────────────────
    'nexus-overdue-enrollments':{'task': 'agents.nexus.overdue_enrollment_alert',       'schedule': 86400},
    'nexus-generate-courses':   {'task': 'agents.nexus.auto_generate_course_content',   'schedule': 86400},
    'nexus-progress-report':    {'task': 'agents.nexus.weekly_progress_report',         'schedule': 604800},

    # ── Nova — Data Scientist ─────────────────────────────────────────────────
    'nova-process-queries':     {'task': 'agents.nova.process_pending_queries', 'schedule': 3600},
    'nova-data-digest':         {'task': 'agents.nova.weekly_data_digest',      'schedule': 604800},

    # ── Oracle — SEO Specialist ───────────────────────────────────────────────
    'oracle-seo-audit':         {'task': 'agents.oracle.weekly_seo_audit',      'schedule': 604800},
    'oracle-generate-fixes':    {'task': 'agents.oracle.auto_generate_fixes',   'schedule': 86400},

    # ── Payload — Procurement Manager ────────────────────────────────────────
    'payload-rfq-reminder':     {'task': 'agents.payload.rfq_deadline_reminder',        'schedule': 86400},
    'payload-evaluate-rfqs':    {'task': 'agents.payload.auto_evaluate_completed_rfqs', 'schedule': 86400},
    'payload-vendor-review':    {'task': 'agents.payload.vendor_performance_review',    'schedule': 604800},

    # ── Pulse — Market Research ───────────────────────────────────────────────
    'pulse-market-scan':        {'task': 'agents.pulse.weekly_market_scan',    'schedule': 604800},
    'pulse-alert-check':        {'task': 'agents.pulse.alert_threshold_check', 'schedule': 86400},

    # ── Realt — Real Estate Assistant ────────────────────────────────────────
    'realt-qualify-leads':      {'task': 'agents.realt.qualify_new_leads',      'schedule': 86400},
    'realt-optimise-listings':  {'task': 'agents.realt.optimise_new_listings',  'schedule': 86400},
    'realt-stale-leads':        {'task': 'agents.realt.stale_lead_follow_up',   'schedule': 86400},

    # ── Reporting Bot — Automated Reporting ──────────────────────────────────
    'reporting-bot-generate':   {'task': 'agents.reporting_bot.scheduled_report_generation', 'schedule': 86400},
    'reporting-bot-deliver':    {'task': 'agents.reporting_bot.deliver_ready_reports',       'schedule': 86400},

    # ── Sage — Legal Reviewer ─────────────────────────────────────────────────
    'sage-review-documents':    {'task': 'agents.sage.auto_review_queued_documents', 'schedule': 14400},
    'sage-high-risk-alert':     {'task': 'agents.sage.high_risk_document_alert',     'schedule': 86400},

    # ── Scout — Competitor Intel ──────────────────────────────────────────────
    'scout-analyse-changes':    {'task': 'agents.scout.analyse_unprocessed_changes', 'schedule': 86400},
    'scout-weekly-digest':      {'task': 'agents.scout.weekly_intel_digest',         'schedule': 604800},

    # ── Shield — IT Helpdesk ─────────────────────────────────────────────────
    'shield-sla-monitor':       {'task': 'agents.shield.sla_breach_monitor',       'schedule': 1800},   # every 30 min
    'shield-auto-resolve':      {'task': 'agents.shield.auto_resolve_open_tickets', 'schedule': 14400},

    # ── Serea Content — Content Strategist ───────────────────────────────────
    'content-strategist-generate':   {'task': 'agents.content_strategist.auto_generate_draft_pieces',    'schedule': 86400},
    'content-strategist-campaigns':  {'task': 'agents.content_strategist.campaign_strategy_generation',  'schedule': 86400},
    'content-strategist-digest':     {'task': 'agents.content_strategist.weekly_content_digest',         'schedule': 604800},

    # ── Tempo — Events Manager ────────────────────────────────────────────────
    'tempo-reminders':          {'task': 'agents.tempo.event_reminder_dispatch',    'schedule': 86400},
    'tempo-generate-plans':     {'task': 'agents.tempo.auto_generate_event_plans',  'schedule': 86400},
    'tempo-rsvp-followup':      {'task': 'agents.tempo.rsvp_followup',              'schedule': 86400},

    # ── Voice Receptionist — Phone AI ─────────────────────────────────────────
    'vr-reminders-2h':          {'task': 'agents.voice_receptionist.send_appointment_reminders_2h',   'schedule': 900},   # every 15 min
    'vr-reminders-24h':         {'task': 'agents.voice_receptionist.send_appointment_reminders_24h',  'schedule': 3600},  # hourly
    'vr-daily-digest':          {'task': 'agents.voice_receptionist.daily_call_digest',               'schedule': 86400},
    'vr-spam-cleanup':          {'task': 'agents.voice_receptionist.spam_blocklist_cleanup',          'schedule': 604800},
    'vr-weekly-report':         {'task': 'agents.voice_receptionist.weekly_analytics_report',         'schedule': 604800},
}

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
