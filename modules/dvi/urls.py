from django.urls import path
from . import views

app_name = 'dvi'

urlpatterns = [
    path('<slug:slug>/', views.dvi_home, name='home'),
    path('<slug:slug>/new/', views.inspection_create, name='inspection_create'),
    path('<slug:slug>/inspections/<int:inspection_id>/', views.inspection_detail, name='inspection_detail'),
    path('<slug:slug>/templates/', views.template_list, name='templates'),
    path('report/<str:token>/', views.inspection_report_public, name='report_public'),
]
