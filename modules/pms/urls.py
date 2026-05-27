from django.urls import path
from . import views

app_name = 'pms'

urlpatterns = [
    path('', views.pms_home, name='home'),
    path('rooms/', views.room_list, name='room_list'),
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/add/', views.reservation_add, name='reservation_add'),
    path('reservations/<int:res_id>/', views.reservation_detail, name='reservation_detail'),
    path('guests/', views.guest_list, name='guest_list'),
    path('housekeeping/', views.housekeeping, name='housekeeping'),
]
