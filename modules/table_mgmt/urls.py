from django.urls import path
from . import views

app_name = 'table_mgmt'

urlpatterns = [
    path('', views.index, name='index'),
    path('floor/', views.floor_plan, name='floor_plan'),
    path('reservations/', views.reservations, name='reservations'),
]
