from django.urls import path
from . import views

app_name = 'contracts'

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.contract_list, name='contract_list'),
    path('new/', views.contract_create, name='contract_create'),
    path('<int:pk>/', views.contract_detail, name='contract_detail'),
    path('templates/', views.templates, name='templates'),
]
