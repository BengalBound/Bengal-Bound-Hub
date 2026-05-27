from django.urls import path
from . import views

app_name = 'b2b_portal'

urlpatterns = [
    path('<slug:slug>/', views.b2b_home, name='home'),
    path('<slug:slug>/customers/', views.customer_list, name='customer_list'),
    path('<slug:slug>/customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('<slug:slug>/orders/', views.order_list, name='order_list'),
    path('<slug:slug>/orders/<int:order_id>/', views.order_detail, name='order_detail'),
]
