from django.urls import path
from . import views

app_name = 'workshop'

urlpatterns = [
    path('<slug:slug>/', views.workshop_dashboard, name='dashboard'),
    path('<slug:slug>/jobs/', views.job_card_list, name='job_list'),
    path('<slug:slug>/jobs/new/', views.job_card_create, name='job_create'),
    path('<slug:slug>/jobs/<int:job_id>/', views.job_card_detail, name='job_detail'),
    path('<slug:slug>/bays/', views.service_bays, name='service_bays'),
    path('<slug:slug>/history/', views.vehicle_history, name='vehicle_history'),
    path('<slug:slug>/history/<str:reg>/', views.vehicle_history_detail, name='vehicle_history_detail'),
]
