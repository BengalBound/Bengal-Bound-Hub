from django.urls import path
from . import views

app_name = 'order_mgmt'

urlpatterns = [
    path('', views.index, name='index'),
    path('orders/', views.purchase_orders, name='purchase_orders'),
    path('orders/new/', views.po_create, name='po_create'),
    path('orders/<int:pk>/', views.po_detail, name='po_detail'),
    path('vendors/', views.vendors, name='vendors'),
]
