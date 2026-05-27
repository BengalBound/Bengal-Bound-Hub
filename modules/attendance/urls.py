from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.index, name='index'),
    path('records/', views.attendance_records, name='attendance_records'),
    path('timesheets/', views.timesheets, name='timesheets'),
]
