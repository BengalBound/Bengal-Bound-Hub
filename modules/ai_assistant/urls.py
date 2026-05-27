from django.urls import path
from . import views

app_name = 'ai_assistant'

urlpatterns = [
    path('', views.index, name='index'),
    path('new/', views.conversation_new, name='conversation_new'),
    path('conversations/<int:pk>/', views.conversation, name='conversation'),
    path('templates/', views.prompt_templates, name='prompt_templates'),
]
