from django.urls import path
from . import views

app_name = 'commission'

urlpatterns = [
    path('<slug:slug>/', views.commission_home, name='home'),
    path('<slug:slug>/entries/', views.commission_list, name='list'),
]
