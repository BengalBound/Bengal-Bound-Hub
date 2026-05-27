from django.urls import path
from . import views

app_name = 'slides'

urlpatterns = [
    path('', views.presentation_list, name='presentation_list'),
    path('new/', views.presentation_create, name='presentation_create'),
    path('<int:pk>/edit/', views.presentation_edit, name='presentation_edit'),
    path('<int:pk>/delete/', views.presentation_delete, name='presentation_delete'),
]
