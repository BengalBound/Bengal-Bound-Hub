from django.urls import path
from . import views

app_name = 'sis'
urlpatterns = [
    path('<slug:slug>/', views.sis_dashboard, name='dashboard'),
    path('<slug:slug>/students/', views.student_list, name='student_list'),
    path('<slug:slug>/students/add/', views.student_add, name='student_add'),
    path('<slug:slug>/students/<int:student_id>/', views.student_detail, name='student_detail'),
]
