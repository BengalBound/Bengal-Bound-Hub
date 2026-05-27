from django.urls import path
from . import views

app_name = 'shift_planning'

urlpatterns = [
    path('', views.index, name='index'),
    path('periods/', views.periods, name='periods'),
    path('periods/<int:period_id>/schedule/', views.schedule, name='schedule'),
    path('templates/', views.shift_templates, name='shift_templates'),
    path('swaps/', views.swap_requests, name='swap_requests'),
]
