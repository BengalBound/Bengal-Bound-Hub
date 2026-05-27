from django.urls import path
from . import views

app_name = 'hospitality_ops'

urlpatterns = [
    path('', views.ops_home, name='home'),
    path('housekeeping/', views.housekeeping, name='housekeeping'),
    path('maintenance/', views.maintenance, name='maintenance'),
    path('service/', views.service_requests, name='service_requests'),
    path('concierge/', views.concierge, name='concierge'),
]
