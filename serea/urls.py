from django.urls import path
from . import views

app_name = 'serea'

urlpatterns = [
    # Human-in-the-loop: client approves or denies a pending permission request
    path('permission/<int:msg_id>/respond/', views.permission_respond, name='permission_respond'),

    # AJAX: send a direct message and trigger Serea's async reply
    path('agent/<int:agent_id>/send/', views.send_chat_message, name='send_chat_message'),

    # Polling-based chat history for a specific agent
    path('agent/<int:agent_id>/chat/', views.agent_chat, name='agent_chat'),

    # Moderation log feed for workspace_admin panel
    path('agent/<int:agent_id>/logs/', views.agent_logs, name='agent_logs'),

    # Facebook Messenger webhook — receives incoming DMs and comment events
    # GET: webhook verification   POST: incoming page events
    path('webhook/facebook/', views.facebook_webhook, name='facebook_webhook'),

    # Instagram webhook — receives DMs and comment events via Meta Webhooks
    # GET: webhook verification   POST: incoming Instagram events
    path('webhook/instagram/', views.instagram_webhook, name='instagram_webhook'),

    # LinkedIn — manual comment moderation trigger (LinkedIn webhooks require app review)
    path('agent/<int:agent_id>/linkedin/moderate/', views.trigger_linkedin_moderation, name='linkedin_moderate'),
]
