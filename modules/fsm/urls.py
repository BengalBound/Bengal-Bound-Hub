from django.urls import path
from . import views

app_name = 'fsm'

urlpatterns = [
    path('dashboard/', views.fsm_dashboard, name='dashboard'),
    path('map/', views.map_dispatch, name='map_dispatch'),
    path('job/<int:job_id>/quote/', views.quote_builder, name='quote_builder'),
    path('job/<int:job_id>/sign/', views.signature_capture, name='signature_capture'),
    path('inventory/', views.inventory_sync, name='inventory_sync'),
]
