from django.urls import path
from . import views

app_name = 'bom'

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.bom_list, name='bom_list'),
    path('new/', views.bom_create, name='bom_create'),
    path('<int:pk>/', views.bom_detail, name='bom_detail'),
    path('work-centers/', views.work_centers, name='work_centers'),
    # Shoe article BOM builder
    path('shoe/', views.shoe_bom_list, name='shoe_bom_list'),
    path('shoe/<int:bom_id>/', views.shoe_bom_detail, name='shoe_bom_detail'),
]
