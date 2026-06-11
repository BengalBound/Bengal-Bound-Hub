from django.urls import path
from . import views

app_name = 'accounts_payable'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
