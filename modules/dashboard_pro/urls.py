from django.urls import path
from . import views

app_name = 'dashboard_pro'

urlpatterns = [
    path('', views.index, name='index'),
    path('list/', views.dashboard_list, name='dashboard_list'),
    path('<int:pk>/', views.dashboard_view, name='dashboard_view'),
]
