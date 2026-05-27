from django.urls import path
from . import views

app_name = 'deal_flow'

urlpatterns = [
    path('<slug:slug>/', views.deal_home, name='home'),
    path('<slug:slug>/deals/', views.deal_list, name='deal_list'),
    path('<slug:slug>/deals/add/', views.deal_add, name='deal_add'),
    path('<slug:slug>/deals/<int:deal_id>/', views.deal_detail, name='deal_detail'),
]
