from django.urls import path
from . import views

app_name = 'team_chat'

urlpatterns = [
    path('', views.channel_list, name='channel_list'),
    path('channels/create/', views.channel_create, name='channel_create'),
    path('channels/<int:channel_id>/send/', views.message_send, name='message_send'),
    path('channels/<int:channel_id>/poll/', views.message_poll, name='message_poll'),
    path('messages/<int:message_id>/delete/', views.message_delete, name='message_delete'),
    path('messages/<int:message_id>/react/', views.reaction_toggle, name='reaction_toggle'),
]
