from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth import views as auth_views
from django.contrib import admin

app_name = 'workspace_admin'

urlpatterns = [
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='workspace_admin/auth/login.html',
        next_page='/'
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Map native admin to subdomain to support CMS editing
    path('admin/', admin.site.urls),

    # Core
    path('', views.dashboard, name='dashboard'),
    path('users/manage/', views.manage_user, name='manage_user'),

    # Phase 6 Section Views
    path('ai-oversight/', views.ai_oversight, name='ai_oversight'),
    path('projects/', views.project_control, name='project_control'),
    path('crm/', views.crm_support, name='crm_support'),
    path('data/', views.data_traffic, name='data_traffic'),
    path('marketing/', views.marketing, name='marketing'),
    path('monitoring/', views.project_monitoring, name='project_monitoring'),

    # Serea AI Config
    path('serea-config/', views.serea_agent_config, name='serea_config'),

    # AI Tiers Config
    path('ai-tiers/', views.ai_tiers, name='ai_tiers'),

    # CMS Control
    path('cms/', views.cms_control, name='cms_control'),
    path('cms/<str:model_name>/', views.cms_list, name='cms_list'),
    path('cms/<str:model_name>/new/', views.cms_form, name='cms_create'),
    path('cms/<str:model_name>/<int:pk>/edit/', views.cms_form, name='cms_edit'),
    path('cms/<str:model_name>/<int:pk>/delete/', views.cms_delete, name='cms_delete'),

    # Community Forum Admin
    path('forum/', views.forum_management, name='forum_management'),
    path('forum/topic/<int:pk>/', views.forum_topic_detail, name='forum_topic_detail'),

    # Internal Office Mgmt
    path('office/projects/', views.office_projects, name='office_projects'),
    path('office/tasks/', views.office_tasks, name='office_tasks'),
    path('office/finance/', views.office_finance, name='office_finance'),

    # Hub Subscription & Pricing Management
    path('hub/plans/', views.hub_plans, name='hub_plans'),
    path('hub/module-pricing/', views.module_pricing, name='module_pricing'),
    path('hub/subscriptions/', views.hub_subscriptions, name='hub_subscriptions'),
    path('hub/storage-requests/', views.storage_requests, name='storage_requests'),
    path('hub/advance-quotes/', views.advance_quotes, name='advance_quotes'),
] + static(settings.STATIC_URL, document_root=settings.BASE_DIR / 'static') \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
