from django.urls import path
from . import views

app_name = 'ecommerce'

urlpatterns = [
    path('', views.index, name='index'),
    path('stores/', views.store_list, name='store_list'),
    path('products/', views.products, name='products'),
    path('orders/', views.orders, name='orders'),
    path('orders/<int:pk>/', views.order_detail, name='order_detail'),
]
