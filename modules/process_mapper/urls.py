from django.urls import path
from . import views

app_name = 'process_mapper'

urlpatterns = [
    path('<slug:slug>/', views.pm_home, name='home'),
    path('<slug:slug>/processes/', views.process_list, name='process_list'),
    path('<slug:slug>/processes/new/', views.process_create, name='process_create'),
    path('<slug:slug>/processes/<int:map_id>/', views.process_detail, name='process_detail'),
]
