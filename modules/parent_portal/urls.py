from django.urls import path
from . import views

app_name = 'parent_portal'
urlpatterns = [
    path('<slug:slug>/', views.portal_home, name='home'),
    path('<slug:slug>/reports/', views.report_list, name='report_list'),
    path('<slug:slug>/reports/<int:report_id>/', views.report_detail, name='report_detail'),
    path('<slug:slug>/messages/', views.message_list, name='message_list'),
    path('<slug:slug>/announcements/', views.announcement_list, name='announcement_list'),
    path('report/<str:token>/', views.report_public, name='report_public'),
]
