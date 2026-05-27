from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.index, name='index'),
    path('folders/', views.folder_view, name='folder_view'),
    path('folders/<int:folder_id>/', views.folder_view, name='folder_view_id'),
    path('files/<int:pk>/', views.document_detail, name='document_detail'),
]
