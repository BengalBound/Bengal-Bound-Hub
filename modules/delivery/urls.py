from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    path('', views.index, name='index'),
    path('orders/', views.delivery_orders, name='delivery_orders'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
    path('drivers/', views.drivers, name='drivers'),
    path('routes/', views.routes, name='routes'),
]
