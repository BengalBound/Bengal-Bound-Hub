from django.urls import path
from . import views

app_name = 'automation_bots'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
