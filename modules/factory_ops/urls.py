from django.urls import path
from . import views, api_views

app_name = 'factory_ops'

urlpatterns = [
    # Dashboard
    path('', views.index, name='index'),
    path('mis/', views.mis_report, name='mis'),
    path('approvals/', views.approvals, name='approvals'),

    # Production Flow
    path('production/', views.production, name='production'),
    path('production/<int:pk>/', views.production_detail, name='production_detail'),
    path('planning/', views.production_planning, name='planning'),
    path('inventory/', views.product_inventory, name='inventory'),
    path('raw-materials/', views.raw_materials, name='raw_materials'),
    path('stock-movements/', views.stock_movements, name='stock_movements'),
    path('wip/', views.wip_inventory, name='wip'),
    path('finished-goods/', views.finished_goods, name='finished_goods'),
    path('daily-report/', views.daily_report, name='daily_report'),
    path('attendance/', views.attendance, name='attendance'),
    path('material-consumption/', views.material_consumption, name='material_consumption'),

    # Industrial Engineering
    path('time-study/', views.time_study, name='time_study'),
    path('smv/', views.smv_study, name='smv'),
    path('capacity/', views.capacity_study, name='capacity'),
    path('costing/', views.style_costing, name='costing'),

    # Quality & Operations
    path('qc/', views.qc_inspections, name='qc'),
    path('rework/', views.rework_defects, name='rework'),
    path('sops/', views.factory_sops, name='sops'),

    # Commercial
    path('buyers/', views.buyers, name='buyers'),
    path('sales/', views.sales_pipeline, name='sales'),
    path('orders/', views.customer_orders, name='orders'),
    path('invoices/', views.invoices, name='invoices'),
    path('invoices/<int:pk>/print/', views.invoice_print, name='invoice_print'),
    path('vendors/', views.vendors, name='vendors'),
    path('supplier-scorecard/', views.supplier_scorecard, name='supplier_scorecard'),

    # Distribution & Sales Force
    path('distribution/', views.distribution, name='distribution'),
    path('wholesale/', views.wholesale, name='wholesale'),
    path('sales-team/', views.sales_team, name='sales_team'),
    path('targets/', views.sales_targets, name='targets'),
    path('tasks/', views.tasks, name='tasks'),
    path('marketing/', views.marketing, name='marketing'),

    # Finance & Admin
    path('financials/', views.financials_report, name='financials'),
    path('ar-ap/', views.ar_ap_ledger, name='ar_ap'),
    path('banking/', views.banking, name='banking'),
    path('hr/', views.hr_roster, name='hr'),

    # Floor Management
    path('hourly-board/', views.hourly_production_board, name='hourly_board'),
    path('petty-cash/', views.petty_cash, name='petty_cash'),
    path('worker-advances/', views.worker_advances, name='worker_advances'),

    # Performance & Incentives
    path('kpi-templates/', views.kpi_templates, name='kpi_templates'),
    path('evaluations/', views.evaluations, name='evaluations'),
    path('sales-incentives/', views.sales_incentives, name='sales_incentives'),

    # Sample Development
    path('sample-orders/', views.sample_orders, name='sample_orders'),

    # Settings (owner only)
    path('settings/', views.factory_settings, name='settings'),

    # JSON API
    path('api/production/', api_views.api_production_orders, name='api_production'),
    path('api/production/<int:pk>/', api_views.api_production_order_detail, name='api_production_detail'),
    path('api/materials/', api_views.api_raw_materials, name='api_materials'),
    path('api/qc/', api_views.api_qc_summary, name='api_qc'),

    # CSV exports
    path('export/production/', views.export_production_csv, name='export_production'),
    path('export/daily-report/', views.export_daily_report_csv, name='export_daily_report'),
    path('export/inventory/', views.export_inventory_csv, name='export_inventory'),
    path('export/ar-ap/', views.export_arap_csv, name='export_arap'),
    path('export/attendance/', views.export_attendance_csv, name='export_attendance'),
    path('export/invoices/', views.export_invoices_csv, name='export_invoices'),
]
