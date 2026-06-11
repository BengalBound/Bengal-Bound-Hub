from django.urls import path
from . import views

app_name = 'cloud_infra'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
