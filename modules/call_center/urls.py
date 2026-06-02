from django.urls import path
from . import views

app_name = 'call_center'

urlpatterns = [
    # Supervisor wallboard
    path('', views.dashboard, name='dashboard'),

    # Call log
    path('calls/', views.call_log, name='call_log'),
    path('calls/<int:pk>/', views.call_detail, name='call_detail'),

    # Agent console (softphone)
    path('agent/', views.agent_console, name='agent_console'),

    # IVR builder
    path('ivr/', views.ivr_list, name='ivr_list'),
    path('ivr/create/', views.ivr_detail, name='ivr_create'),
    path('ivr/<int:pk>/', views.ivr_detail, name='ivr_detail'),

    # Queue management
    path('queues/', views.queue_list, name='queue_list'),
    path('queues/create/', views.queue_detail, name='queue_create'),
    path('queues/<int:pk>/', views.queue_detail, name='queue_detail'),

    # Settings
    path('settings/', views.cc_settings, name='settings'),

    # JSON API for live wallboard updates
    path('api/stats/', views.api_queue_stats, name='api_stats'),
    path('api/agent-status/', views.api_set_agent_status, name='api_agent_status'),

    # Twilio webhooks (csrf_exempt, no auth — Twilio validates with X-Twilio-Signature)
    path('twilio/inbound/', views.twilio_inbound, name='twilio_inbound'),
    path('twilio/ivr/<int:menu_pk>/', views.twilio_ivr_response, name='twilio_ivr_response'),
    path('twilio/status/', views.twilio_status, name='twilio_status'),
    path('twilio/token/', views.twilio_token, name='twilio_token'),
]
