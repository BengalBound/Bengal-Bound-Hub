from django.urls import path
from . import views

app_name = 'store_ops'

urlpatterns = [
    path('<slug:slug>/', views.store_ops_home, name='home'),
    path('<slug:slug>/stores/', views.store_list, name='store_list'),
    path('<slug:slug>/stores/<int:store_id>/', views.store_detail, name='store_detail'),
]
