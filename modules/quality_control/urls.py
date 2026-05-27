from django.urls import path
from . import views

app_name = 'quality_control'

urlpatterns = [
    path('', views.index, name='index'),
    path('inspections/', views.inspections, name='inspections'),
    path('inspections/<int:pk>/', views.inspection_detail, name='inspection_detail'),
    path('ncr/', views.nonconformances, name='nonconformances'),
    path('templates/', views.qc_templates, name='qc_templates'),
    # Shoe defect log
    path('shoe-defects/', views.shoe_defect_log, name='shoe_defect_log'),
]
