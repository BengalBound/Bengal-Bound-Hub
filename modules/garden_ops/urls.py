from django.urls import path
from . import views

app_name = 'garden_ops'

urlpatterns = [
    path('', views.garden_home, name='home'),
    path('sites/', views.site_list, name='site_list'),
    path('sites/<int:site_id>/', views.site_detail, name='site_detail'),
    path('jobs/', views.job_list, name='job_list'),
    path('inventory/', views.inventory, name='inventory'),
]
