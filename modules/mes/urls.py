from django.urls import path
from . import views, api

app_name = 'mes'

urlpatterns = [
    path('api/scanner/webhook/', api.scanner_event_webhook, name='api_scanner_webhook'),
    path('<slug:slug>/', views.mes_dashboard, name='dashboard'),
    path('<slug:slug>/executive-dashboard/', views.executive_dashboard, name='executive_dashboard'),
    path('<slug:slug>/work-centers/', views.mes_work_centers, name='work_centers'),
    path('<slug:slug>/production-orders/', views.mes_production_orders, name='production_orders'),
    path('<slug:slug>/production-orders/<int:order_id>/', views.mes_production_order_detail, name='order_detail'),
    path('<slug:slug>/downtime/', views.mes_downtime, name='downtime'),
    # Footwear production schedule
    path('<slug:slug>/footwear-schedule/', views.footwear_schedule_list, name='footwear_schedule_list'),
    path('<slug:slug>/footwear-schedule/<int:schedule_id>/', views.footwear_schedule_detail, name='footwear_schedule_detail'),
]
