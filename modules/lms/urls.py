from django.urls import path
from . import views

app_name = 'lms'
urlpatterns = [
    path('<slug:slug>/', views.lms_home, name='home'),
    path('<slug:slug>/courses/', views.course_list, name='course_list'),
    path('<slug:slug>/courses/new/', views.course_create, name='course_create'),
    path('<slug:slug>/courses/<int:course_id>/', views.course_detail, name='course_detail'),
]
