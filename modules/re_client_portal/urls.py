from django.urls import path
from . import views

app_name = 're_client_portal'

urlpatterns = [
    path('<slug:slug>/', views.portal_home, name='home'),
    path('<slug:slug>/clients/', views.client_list, name='client_list'),
    path('<slug:slug>/clients/<int:access_id>/', views.client_detail, name='client_detail'),
    path('view/<str:token>/', views.portal_view, name='portal_view'),
]
