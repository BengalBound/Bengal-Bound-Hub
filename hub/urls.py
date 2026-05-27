from django.urls import path
from . import views

app_name = 'hub'

urlpatterns = [
    # Hub landing — business selector for multi-business owners
    path('', views.hub_landing, name='hub_landing'),
    path('create/', views.hub_create, name='hub_create'),

    # Per-business routes — all scoped under /hub/<slug>/
    path('<slug:slug>/', views.hub_dashboard, name='hub_dashboard'),
    path('<slug:slug>/portal/', views.hub_employee_portal, name='hub_employee_portal'),
    path('<slug:slug>/modules/', views.hub_module_store, name='hub_module_store'),
    path('<slug:slug>/modules/activate/', views.hub_activate_module, name='hub_activate_module'),
    path('<slug:slug>/modules/deactivate/', views.hub_deactivate_module, name='hub_deactivate_module'),

    path('<slug:slug>/employees/', views.hub_employees, name='hub_employees'),
    path('<slug:slug>/employees/add/', views.hub_add_employee, name='hub_add_employee'),
    path('<slug:slug>/employees/<int:emp_id>/toggle/', views.hub_toggle_employee, name='hub_toggle_employee'),
    path('<slug:slug>/employees/<int:emp_id>/edit/', views.hub_employee_edit, name='hub_employee_edit'),

    # Custom positions (CEO/MD only)
    path('<slug:slug>/positions/', views.hub_positions, name='hub_positions'),
    path('<slug:slug>/positions/create/', views.hub_position_create, name='hub_position_create'),
    path('<slug:slug>/positions/<int:pos_id>/edit/', views.hub_position_edit, name='hub_position_edit'),
    path('<slug:slug>/positions/<int:pos_id>/delete/', views.hub_position_delete, name='hub_position_delete'),

    path('<slug:slug>/settings/', views.hub_settings, name='hub_settings'),
    path('<slug:slug>/settings/ip-access/', views.hub_ip_access, name='hub_ip_access'),
    path('<slug:slug>/settings/ip-access/add/', views.hub_add_ip, name='hub_add_ip'),
    path('<slug:slug>/settings/ip-access/remove/', views.hub_remove_ip, name='hub_remove_ip'),

    path('<slug:slug>/connector/', views.hub_connector, name='hub_connector'),
    path('<slug:slug>/connector/generate/', views.hub_generate_token, name='hub_generate_token'),
    path('<slug:slug>/connector/<int:session_id>/revoke/', views.hub_revoke_token, name='hub_revoke_token'),

    path('<slug:slug>/sync/', views.hub_sync, name='hub_sync'),
    path('<slug:slug>/sync/regenerate-token/', views.hub_regenerate_sync_token, name='hub_regenerate_sync_token'),

    # Subscription management
    path('<slug:slug>/subscription/', views.hub_subscription, name='hub_subscription'),
    path('<slug:slug>/subscription/advance-quote/', views.hub_advance_quote, name='hub_advance_quote'),

    # API endpoint for self-hosted backdoor sync (token auth, no session required)
    path('api/sync/', views.hub_sync_api, name='hub_sync_api'),

    # Module store alias
    path('<slug:slug>/store/', views.hub_module_store, name='hub_store'),

    # Business membership management (invite / remove non-owner members)
    path('<slug:slug>/members/', views.hub_members, name='hub_members'),
    path('<slug:slug>/members/invite/', views.hub_invite_member, name='hub_invite_member'),
    path('<slug:slug>/members/<int:membership_id>/remove/', views.hub_remove_member, name='hub_remove_member'),

    # Business onboarding wizard (triggered after hub_create)
    path('<slug:slug>/onboarding/', views.hub_onboarding, name='hub_onboarding'),
]
