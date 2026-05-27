from django.urls import path
from . import views, api_views

app_name = 'crm'

urlpatterns = [
    path('', views.index, name='index'),
    path('contacts/', views.contacts, name='contacts'),
    path('contacts/new/', views.contact_create, name='contact_create'),
    path('contacts/<int:pk>/', views.contact_detail, name='contact_detail'),
    path('deals/', views.deals, name='deals'),
    path('deals/new/', views.deal_create, name='deal_create'),
    path('deals/<int:pk>/', views.deal_detail, name='deal_detail'),
    path('deals/<int:pk>/move/', views.deal_move, name='deal_move'),
    path('activities/', views.activities, name='activities'),

    # CSV exports
    path('export/contacts/', views.export_contacts_csv, name='export_contacts'),
    path('export/deals/', views.export_deals_csv, name='export_deals'),

    # JSON API
    path('api/contacts/', api_views.api_contacts, name='api_contacts'),
    path('api/contacts/<int:pk>/', api_views.api_contact_detail, name='api_contact_detail'),
    path('api/deals/', api_views.api_deals, name='api_deals'),
    path('api/deals/<int:pk>/', api_views.api_deal_detail, name='api_deal_detail'),
]
