from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.project_list, name='project_list'),
    path('new/', views.project_create, name='project_create'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('milestones/', views.milestones, name='milestones'),
]
