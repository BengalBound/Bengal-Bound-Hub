from django.urls import path
from . import views

app_name = 'recruitment'

urlpatterns = [
    path('', views.index, name='index'),
    path('jobs/', views.job_list, name='job_list'),
    path('jobs/new/', views.job_create, name='job_create'),
    path('jobs/<int:pk>/', views.job_detail, name='job_detail'),
    path('applications/', views.application_list, name='application_list'),
    path('applications/<int:pk>/', views.application_detail, name='application_detail'),
]
