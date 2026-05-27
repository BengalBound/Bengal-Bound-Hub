from django.urls import path
from . import views

app_name = 'property_listings'

urlpatterns = [
    path('<slug:slug>/', views.property_home, name='home'),
    path('<slug:slug>/properties/', views.property_list, name='property_list'),
    path('<slug:slug>/properties/add/', views.property_add, name='property_add'),
    path('<slug:slug>/properties/<int:property_id>/', views.property_detail, name='property_detail'),
]
