from django.urls import path, include
from django.conf import settings

# ──────────────────────────────────────────────────────────────────────────────
# Pattern B — slug lives INSIDE the module's own URLconf
# Mount at hub/<module_prefix>/ so the module gets: <slug:slug>/
# ──────────────────────────────────────────────────────────────────────────────
_MODULE_SLUG_INNER = [
    path('hub/assessments/',       include('modules.assessments.urls',       namespace='assessments')),
    path('hub/asset_management/',  include('modules.asset_management.urls',  namespace='asset_management')),
    path('hub/b2b_portal/',        include('modules.b2b_portal.urls',        namespace='b2b_portal')),
    path('hub/cadcam/',            include('modules.cadcam.urls',            namespace='cadcam')),
    path('hub/commission/',        include('modules.commission.urls',        namespace='commission')),
    path('hub/data_studio/',       include('modules.data_studio.urls',       namespace='data_studio')),
    path('hub/deal_flow/',         include('modules.deal_flow.urls',         namespace='deal_flow')),
    path('hub/dms/',               include('modules.dms.urls',               namespace='dms')),
    path('hub/dvi/',               include('modules.dvi.urls',               namespace='dvi')),
    path('hub/erp/',               include('modules.erp.urls',               namespace='erp')),
    path('hub/lms/',               include('modules.lms.urls',               namespace='lms')),
    path('hub/mes/',               include('modules.mes.urls',               namespace='mes')),
    path('hub/omnichannel/',       include('modules.omnichannel.urls',       namespace='omnichannel')),
    path('hub/parent_portal/',     include('modules.parent_portal.urls',     namespace='parent_portal')),
    path('hub/planogram/',         include('modules.planogram.urls',         namespace='planogram')),
    path('hub/plm/',               include('modules.plm.urls',               namespace='plm')),
    path('hub/process_mapper/',    include('modules.process_mapper.urls',    namespace='process_mapper')),
    path('hub/product_catalog/',   include('modules.product_catalog.urls',   namespace='product_catalog')),
    path('hub/property_listings/', include('modules.property_listings.urls', namespace='property_listings')),
    path('hub/re_client_portal/',  include('modules.re_client_portal.urls',  namespace='re_client_portal')),
    path('hub/re_marketing/',      include('modules.re_marketing.urls',      namespace='re_marketing')),
    path('hub/sis/',               include('modules.sis.urls',               namespace='sis')),
    path('hub/store_ops/',         include('modules.store_ops.urls',         namespace='store_ops')),
    path('hub/timetable/',         include('modules.timetable.urls',         namespace='timetable')),
    path('hub/tms/',               include('modules.tms.urls',               namespace='tms')),
    path('hub/wms/',               include('modules.wms.urls',               namespace='wms')),
    path('hub/workshop/',          include('modules.workshop.urls',          namespace='workshop')),
]

# ──────────────────────────────────────────────────────────────────────────────
# Pattern A — slug supplied by the outer URLconf
# Mount at hub/<slug:slug>/<module_prefix>/ so views receive slug via kwargs
# ──────────────────────────────────────────────────────────────────────────────
_MODULE_SLUG_OUTER = [
    path('hub/<slug:slug>/accounting/',        include('modules.accounting.urls',        namespace='accounting')),
    path('hub/<slug:slug>/ai_analytics/',      include('modules.ai_analytics.urls',      namespace='ai_analytics')),
    path('hub/<slug:slug>/ai_assistant/',      include('modules.ai_assistant.urls',      namespace='ai_assistant')),
    path('hub/<slug:slug>/announcements/',     include('modules.announcements.urls',     namespace='announcements')),
    path('hub/<slug:slug>/attendance/',        include('modules.attendance.urls',        namespace='attendance')),
    path('hub/<slug:slug>/bom/',               include('modules.bom.urls',               namespace='bom')),
    path('hub/<slug:slug>/booking/',           include('modules.booking.urls',           namespace='booking')),
    path('hub/<slug:slug>/budgeting/',         include('modules.budgeting.urls',         namespace='budgeting')),
    path('hub/<slug:slug>/business_calendar/', include('modules.business_calendar.urls', namespace='business_calendar')),
    path('hub/<slug:slug>/business_mail/',     include('modules.business_mail.urls',     namespace='business_mail')),
    path('hub/<slug:slug>/care_manager/',      include('modules.care_manager.urls',      namespace='care_manager')),
    path('hub/<slug:slug>/channel_manager/',   include('modules.channel_manager.urls',   namespace='channel_manager')),
    path('hub/<slug:slug>/cloud_drive/',       include('modules.cloud_drive.urls',       namespace='cloud_drive')),
    path('hub/<slug:slug>/contracts/',         include('modules.contracts.urls',         namespace='contracts')),
    path('hub/<slug:slug>/crm/',               include('modules.crm.urls',               namespace='crm')),
    path('hub/<slug:slug>/dashboard_pro/',     include('modules.dashboard_pro.urls',     namespace='dashboard_pro')),
    path('hub/<slug:slug>/data_collection/',   include('modules.data_collection.urls',   namespace='data_collection')),
    path('hub/<slug:slug>/delivery/',          include('modules.delivery.urls',          namespace='delivery')),
    path('hub/<slug:slug>/docs/',              include('modules.docs.urls',              namespace='docs')),
    path('hub/<slug:slug>/documents/',         include('modules.documents.urls',         namespace='documents')),
    path('hub/<slug:slug>/ecommerce/',         include('modules.ecommerce.urls',         namespace='ecommerce')),
    path('hub/<slug:slug>/email_marketing/',   include('modules.email_marketing.urls',   namespace='email_marketing')),
    path('hub/<slug:slug>/expense/',           include('modules.expense.urls',           namespace='expense')),
    path('hub/<slug:slug>/factory/',           include('modules.factory_ops.urls',       namespace='factory_ops')),
    path('hub/<slug:slug>/financials/',        include('modules.financials.urls',        namespace='financials')),
    path('hub/<slug:slug>/forms_builder/',     include('modules.forms_builder.urls',     namespace='forms_builder')),
    path('hub/<slug:slug>/garden_ops/',        include('modules.garden_ops.urls',        namespace='garden_ops')),
    path('hub/<slug:slug>/group_bookings/',    include('modules.group_bookings.urls',    namespace='group_bookings')),
    path('hub/<slug:slug>/hospitality_ops/',   include('modules.hospitality_ops.urls',   namespace='hospitality_ops')),
    path('hub/<slug:slug>/hr/',                include('modules.hr.urls',                namespace='hr')),
    path('hub/<slug:slug>/inventory/',         include('modules.inventory.urls',         namespace='inventory')),
    path('hub/<slug:slug>/invoicing/',         include('modules.invoicing.urls',         namespace='invoicing')),
    path('hub/<slug:slug>/leads/',             include('modules.leads.urls',             namespace='leads')),
    path('hub/<slug:slug>/loyalty/',           include('modules.loyalty.urls',           namespace='loyalty')),
    path('hub/<slug:slug>/maintenance/',       include('modules.maintenance.urls',       namespace='maintenance')),
    path('hub/<slug:slug>/order_mgmt/',        include('modules.order_mgmt.urls',        namespace='order_mgmt')),
    path('hub/<slug:slug>/payroll/',           include('modules.payroll.urls',           namespace='payroll')),
    path('hub/<slug:slug>/pms/',               include('modules.pms.urls',               namespace='pms')),
    path('hub/<slug:slug>/pos/',               include('modules.pos.urls',               namespace='pos')),
    path('hub/<slug:slug>/projects/',          include('modules.projects.urls',          namespace='projects')),
    path('hub/<slug:slug>/production/',        include('modules.production.urls',        namespace='production')),
    path('hub/<slug:slug>/quality_control/',   include('modules.quality_control.urls',   namespace='quality_control')),
    path('hub/<slug:slug>/rate_manager/',      include('modules.rate_manager.urls',      namespace='rate_manager')),
    path('hub/<slug:slug>/recruitment/',       include('modules.recruitment.urls',       namespace='recruitment')),
    path('hub/<slug:slug>/reports/',           include('modules.reports.urls',           namespace='reports')),
    path('hub/<slug:slug>/sheets/',            include('modules.sheets.urls',            namespace='sheets')),
    path('hub/<slug:slug>/shift_planning/',    include('modules.shift_planning.urls',    namespace='shift_planning')),
    path('hub/<slug:slug>/slides/',            include('modules.slides.urls',            namespace='slides')),
    path('hub/<slug:slug>/table_mgmt/',        include('modules.table_mgmt.urls',        namespace='table_mgmt')),
    path('hub/<slug:slug>/board/',             include('modules.task_board.urls',        namespace='task_board')),
    path('hub/<slug:slug>/chat/',              include('modules.team_chat.urls',         namespace='team_chat')),
    path('hub/<slug:slug>/training/',          include('modules.training.urls',          namespace='training')),
    path('hub/<slug:slug>/travel_crm/',        include('modules.travel_crm.urls',        namespace='travel_crm')),
    path('hub/<slug:slug>/travel_desk/',       include('modules.travel_desk.urls',       namespace='travel_desk')),
    path('hub/<slug:slug>/video_meet/',        include('modules.video_meet.urls',        namespace='video_meet')),
    path('hub/<slug:slug>/website/',           include('modules.website.urls',           namespace='website')),
]

urlpatterns = [
    # ── Business Hub core (module store, employees, subscription, settings) ──
    path('hub/', include('hub.urls', namespace='hub')),

    # ── All 81 module URLconfs ────────────────────────────────────────────────
    *_MODULE_SLUG_INNER,
    *_MODULE_SLUG_OUTER,

    # ── Console dashboard & workspace management ──────────────────────────────
    path('', include('console_admin.urls', namespace='console_admin')),

    # ── Auth ─────────────────────────────────────────────────────────────────
    path('accounts/', include('allauth.urls')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),

    # ── Public site fallback ─────────────────────────────────────────────────
    path('', include('public_site.urls', namespace='public_site')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
