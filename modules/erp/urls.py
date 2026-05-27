from django.urls import path
from . import views

app_name = 'erp'

urlpatterns = [
    path('<slug:slug>/', views.erp_dashboard, name='dashboard'),
    path('<slug:slug>/ledger/', views.erp_ledger, name='ledger'),
    path('<slug:slug>/journal/', views.erp_journal, name='journal'),
    path('<slug:slug>/journal/new/', views.erp_journal_create, name='journal_create'),
    path('<slug:slug>/vendors/', views.erp_vendors, name='vendors'),
    path('<slug:slug>/purchase-orders/', views.erp_purchase_orders, name='purchase_orders'),
    path('<slug:slug>/purchase-orders/<int:po_id>/', views.erp_purchase_order_detail, name='po_detail'),
    path('<slug:slug>/cost-centers/', views.erp_cost_centers, name='cost_centers'),
]
