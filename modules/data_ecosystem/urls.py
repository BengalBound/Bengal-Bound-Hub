from django.urls import path
from . import views

app_name = 'data_ecosystem'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
