from django.urls import path
from . import views

app_name = 'maintenance'

urlpatterns = [
    path('', views.index, name='index'),
    path('assets/', views.assets, name='assets'),
    path('work-orders/', views.work_orders, name='work_orders'),
]
