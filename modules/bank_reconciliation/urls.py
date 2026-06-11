from django.urls import path
from . import views

app_name = 'bank_reconciliation'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]
