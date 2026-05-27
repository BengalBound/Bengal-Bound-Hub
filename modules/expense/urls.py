from django.urls import path
from . import views

app_name = 'expense'

urlpatterns = [
    path('', views.index, name='index'),
    path('claims/', views.claims, name='claims'),
    path('claims/new/', views.claim_create, name='claim_create'),
    path('claims/<int:pk>/', views.claim_detail, name='claim_detail'),
]
