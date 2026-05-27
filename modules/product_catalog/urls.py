from django.urls import path
from . import views

app_name = 'product_catalog'

urlpatterns = [
    path('<slug:slug>/', views.catalog_home, name='home'),
    path('<slug:slug>/catalogs/new/', views.catalog_create, name='catalog_create'),
    path('<slug:slug>/catalogs/<int:catalog_id>/', views.catalog_detail, name='catalog_detail'),
    path('view/<str:token>/', views.catalog_public, name='catalog_public'),
]
