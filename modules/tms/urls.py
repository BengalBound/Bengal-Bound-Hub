from django.urls import path
from . import views

app_name = 'tms'

urlpatterns = [
    path('<slug:slug>/', views.tms_dashboard, name='dashboard'),
    path('<slug:slug>/shipments/', views.shipment_list, name='shipment_list'),
    path('<slug:slug>/shipments/new/', views.shipment_create, name='shipment_create'),
    path('<slug:slug>/shipments/<int:shipment_id>/', views.shipment_detail, name='shipment_detail'),
    path('<slug:slug>/carriers/', views.carrier_list, name='carriers'),
    path('<slug:slug>/routes/', views.route_list, name='routes'),
    path('<slug:slug>/quotes/', views.quote_list, name='quotes'),
]
