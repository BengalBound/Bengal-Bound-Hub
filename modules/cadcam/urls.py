from django.urls import path
from . import views

app_name = 'cadcam'

urlpatterns = [
    path('<slug:slug>/', views.cadcam_home, name='home'),
    path('<slug:slug>/projects/new/', views.cadcam_project_create, name='project_create'),
    path('<slug:slug>/projects/<int:project_id>/', views.cadcam_project_detail, name='project_detail'),
]
