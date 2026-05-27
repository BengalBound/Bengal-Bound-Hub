from django.urls import path
from . import views

app_name = 'loyalty'

urlpatterns = [
    path('', views.index, name='index'),
    path('programs/', views.programs, name='programs'),
    path('programs/<int:pk>/', views.program_detail, name='program_detail'),
    path('members/', views.members, name='members'),
    path('members/<int:pk>/', views.member_detail, name='member_detail'),
]
