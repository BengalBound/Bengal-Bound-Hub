from django.urls import path
from . import views

app_name = 'iot_network'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
