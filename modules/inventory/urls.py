from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.index, name='index'),
    path('products/', views.products, name='products'),
    path('products/new/', views.product_create, name='product_create'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('warehouses/', views.warehouses, name='warehouses'),
    path('movements/', views.movements, name='movements'),
]
