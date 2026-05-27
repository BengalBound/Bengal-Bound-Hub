from django.urls import path
from . import views

app_name = 'dms'

urlpatterns = [
    path('<slug:slug>/', views.dms_dashboard, name='dashboard'),
    path('<slug:slug>/stock/', views.vehicle_list, name='vehicle_list'),
    path('<slug:slug>/stock/add/', views.vehicle_add, name='vehicle_add'),
    path('<slug:slug>/stock/<int:stock_id>/', views.vehicle_detail, name='vehicle_detail'),
    path('<slug:slug>/deals/', views.deal_list, name='deal_list'),
    path('<slug:slug>/deals/new/', views.deal_create, name='deal_create'),
    path('<slug:slug>/deals/<int:deal_id>/', views.deal_detail, name='deal_detail'),
]
