from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    path('', views.index, name='index'),
    path('orders/', views.manufacturing_orders, name='manufacturing_orders'),
    path('orders/<int:pk>/', views.mo_detail, name='mo_detail'),
    path('kpi/', views.kpi_dashboard, name='kpi_dashboard'),
]
