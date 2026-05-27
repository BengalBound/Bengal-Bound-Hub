from django.urls import path
from . import views

app_name = 'hr'

urlpatterns = [
    path('', views.index, name='index'),
    path('employees/', views.employees, name='employees'),
    path('employees/new/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('departments/', views.departments, name='departments'),
    path('leave/', views.leave_management, name='leave_management'),
    path('performance/', views.performance, name='performance'),
]
