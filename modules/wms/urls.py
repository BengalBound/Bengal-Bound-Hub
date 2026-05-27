from django.urls import path
from . import views

app_name = 'wms'

urlpatterns = [
    path('<slug:slug>/', views.wms_dashboard, name='dashboard'),
    path('<slug:slug>/zones/', views.zone_list, name='zones'),
    path('<slug:slug>/inbound/', views.inbound_list, name='inbound_list'),
    path('<slug:slug>/inbound/<int:receipt_id>/', views.inbound_detail, name='inbound_detail'),
    path('<slug:slug>/picks/', views.picklist_list, name='picklist_list'),
    path('<slug:slug>/picks/<int:pick_id>/', views.picklist_detail, name='picklist_detail'),
]
