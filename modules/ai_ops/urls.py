from django.urls import path
from . import views

app_name = 'ai_ops'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
