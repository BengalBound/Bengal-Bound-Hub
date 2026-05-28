from django.urls import path
from . import views

urlpatterns = [
    path('webhook/<str:token>/', views.inbound_webhook, name='agent_inbound_webhook'),
    path('permission/<int:pk>/respond/', views.permission_respond, name='agent_permission_respond'),
]
