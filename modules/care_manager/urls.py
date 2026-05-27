from django.urls import path
from . import views

app_name = 'care_manager'

urlpatterns = [
    path('', views.care_home, name='home'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('rota/', views.staff_rota, name='staff_rota'),
    path('compliance/', views.compliance, name='compliance'),
]
