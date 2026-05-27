from django.urls import path
from . import views

app_name = 'asset_management'

urlpatterns = [
    path('<slug:slug>/', views.asset_dashboard, name='dashboard'),
    path('<slug:slug>/assets/', views.asset_list, name='asset_list'),
    path('<slug:slug>/assets/new/', views.asset_create, name='asset_create'),
    path('<slug:slug>/assets/<int:asset_id>/', views.asset_detail, name='asset_detail'),
    path('<slug:slug>/work-orders/', views.asset_work_orders, name='work_orders'),
    path('<slug:slug>/categories/', views.asset_categories, name='categories'),
]
