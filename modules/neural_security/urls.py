from django.urls import path
from . import views

app_name = 'neural_security'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
