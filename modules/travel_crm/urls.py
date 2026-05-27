from django.urls import path
from . import views

app_name = 'travel_crm'

urlpatterns = [
    path('', views.tcrm_home, name='home'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('itineraries/', views.itinerary_list, name='itinerary_list'),
    path('itineraries/<int:itin_id>/', views.itinerary_detail, name='itinerary_detail'),
    path('bookings/', views.booking_list, name='booking_list'),
]
