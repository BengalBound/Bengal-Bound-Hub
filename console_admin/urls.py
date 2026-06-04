from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views, views_billing, views_totp, views_agents
from django.contrib.auth import views as auth_views

app_name = 'console_admin'

urlpatterns = [
    path('accounts/', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Include Serea agent endpoints (for chat API, permissions, etc.)
    path('serea/', include('serea.urls')),
    
    # Veritas KYB
    path('veritas/', include('modules.veritas.urls', namespace='veritas')),

    # Core
    path('', views.dashboard, name='dashboard'),
    path('activate-module/', views.activate_module, name='activate_module'),
    path('my-ai/', views.my_ai, name='my_ai'),
    path('hire-ai/', views.hire_ai, name='hire_ai'),
    path('onboarding/', views.serea_onboarding, name='serea_onboarding'),
    
    # Hybrid Onboarding Flow
    path('setup/', views.hybrid_onboarding, name='hybrid_onboarding'),
    path('setup/chat/', views.api_onboarding_chat, name='api_onboarding_chat'),
    path('setup/checkout/', views.process_onboarding_checkout, name='process_onboarding_checkout'),
    path('setup/kyb/', include('modules.veritas.user_urls', namespace='veritas_user')),
    
    path('manage-ai/<int:ai_id>/', views.manage_ai, name='manage_ai'),
    path('fire-ai/<int:ai_id>/', views.fire_ai, name='fire_ai'),
    path('nowpayments/webhook/', views.nowpayments_webhook, name='nowpayments_webhook'),

    # AI Workforce Hub
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('ai-chat/<int:ai_id>/', views.ai_chat, name='ai_chat_with'),
    path('tasks/', views.task_management, name='task_management'),
    path('tasks/new/', views.task_create, name='task_create'),
    path('training/', views.ai_training, name='ai_training'),

    # Operations
    path('tickets/', views.tickets, name='tickets'),
    path('tools/', views.tools, name='tools'),

    # Serea Setup
    path('platforms/', views.serea_platforms, name='serea_platforms'),
    path('platforms/facebook/connect/', views.serea_fb_connect, name='serea_fb_connect'),
    path('platforms/facebook/callback/', views.serea_fb_callback, name='serea_fb_callback'),
    path('platforms/facebook/select/', views.serea_fb_page_select, name='serea_fb_page_select'),
    path('workspace/', views.serea_workspace, name='serea_workspace'),

    # Daily Reports
    path('reports/', views.daily_reports, name='daily_reports'),
    path('reports/<int:report_id>/', views.daily_report_detail, name='daily_report_detail'),

    # Billing portal
    path('billing/', views_billing.billing_overview, name='billing_overview'),
    path('billing/invoice/<int:sub_id>/', views_billing.billing_invoice_detail, name='billing_invoice_detail'),
    path('billing/invoice/<int:sub_id>/download/', views_billing.billing_invoice_pdf, name='billing_invoice_pdf'),
    path('billing/plan/', views_billing.billing_plan_change, name='billing_plan_change'),

    # Two-factor auth (TOTP)
    path('security/totp/setup/', views_totp.totp_setup, name='totp_setup'),
    path('security/totp/verify/', views_totp.totp_verify, name='totp_verify'),
    path('security/totp/disable/', views_totp.totp_disable, name='totp_disable'),

    # Notification center
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/mark-read/', views.notifications_mark_read, name='notifications_mark_read'),

    # AI Agent workspaces
    path('agents/', views_agents.agents_overview, name='agents_overview'),
    path('agents/<slug:agent_slug>/', views_agents.agent_workspace, name='agent_workspace'),

    # Data exports
    path('export/moderation-logs/', views.export_moderation_logs_csv, name='export_moderation_logs'),
] + static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static') \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
