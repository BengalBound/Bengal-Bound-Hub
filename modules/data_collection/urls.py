from django.urls import path
from . import views

app_name = 'data_collection'

urlpatterns = [
    path('', views.dc_home, name='home'),
    path('forms/', views.form_list, name='form_list'),
    path('forms/<int:form_id>/builder/', views.form_builder, name='form_builder'),
    path('forms/<int:form_id>/responses/', views.form_detail, name='form_detail'),
    path('f/<int:form_id>/', views.public_form, name='public_form'),
]
