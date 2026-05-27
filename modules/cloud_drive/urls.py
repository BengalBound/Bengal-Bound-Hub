from django.urls import path
from . import views

app_name = 'cloud_drive'

urlpatterns = [
    path('', views.drive_home, name='drive_home'),
    path('folder/<int:folder_id>/', views.drive_folder, name='drive_folder'),
    path('upload/', views.drive_upload, name='drive_upload'),
    path('new-folder/', views.drive_new_folder, name='drive_new_folder'),
    path('file/<int:file_id>/delete/', views.drive_file_delete, name='drive_file_delete'),
    path('file/<int:file_id>/star/', views.drive_file_star, name='drive_file_star'),
]
