from django.urls import path
from . import views

app_name = 'forms_builder'

urlpatterns = [
    path('', views.form_list, name='form_list'),
    path('new/', views.form_create, name='form_create'),
    path('<int:pk>/edit/', views.form_edit, name='form_edit'),
    path('<int:pk>/responses/', views.form_responses, name='form_responses'),
    path('<int:pk>/delete/', views.form_delete, name='form_delete'),
    path('f/<slug:form_slug>/', views.form_public, name='form_public'),
]
