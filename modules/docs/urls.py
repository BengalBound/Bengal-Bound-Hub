from django.urls import path
from . import views

app_name = 'docs'

urlpatterns = [
    path('', views.doc_list, name='doc_list'),
    path('new/', views.doc_create, name='doc_create'),
    path('<int:pk>/edit/', views.doc_edit, name='doc_edit'),
    path('<int:pk>/view/', views.doc_view, name='doc_view'),
    path('<int:pk>/delete/', views.doc_delete, name='doc_delete'),
    path('<int:pk>/share/', views.doc_share, name='doc_share'),
]
