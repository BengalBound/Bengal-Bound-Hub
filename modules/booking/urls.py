from django.urls import path
from . import views

app_name = 'booking'

urlpatterns = [
    path('', views.index, name='index'),
    path('services/', views.services, name='services'),
    path('bookings/', views.bookings, name='bookings'),
    path('bookings/<int:pk>/', views.booking_detail, name='booking_detail'),
]
