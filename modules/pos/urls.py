from django.urls import path
from . import views

app_name = 'pos'

urlpatterns = [
    path('', views.index, name='index'),
    path('sessions/<int:pk>/', views.session_detail, name='session_detail'),
    path('sessions/<int:session_pk>/orders/<int:order_pk>/', views.order_detail, name='order_detail'),
]
