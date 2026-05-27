from django.urls import path
from . import views

app_name = 'sheets'

urlpatterns = [
    path('', views.sheet_list, name='sheet_list'),
    path('new/', views.sheet_create, name='sheet_create'),
    path('<int:pk>/edit/', views.sheet_edit, name='sheet_edit'),
    path('<int:pk>/delete/', views.sheet_delete, name='sheet_delete'),
]
