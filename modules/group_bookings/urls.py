from django.urls import path
from . import views

app_name = 'group_bookings'

urlpatterns = [
    path('', views.gb_home, name='home'),
    path('rfp/', views.rfp_list, name='rfp_list'),
    path('rfp/<int:rfp_id>/', views.rfp_detail, name='rfp_detail'),
    path('rfp/<int:rfp_id>/rooming/', views.rooming_list, name='rooming_list'),
]
