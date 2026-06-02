"""
URL configuration for bengalbound_core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from modules.forms_builder.views import form_public
from public_site.sitemaps import StaticPageSitemap, BlogSitemap

_sitemaps = {
    'static': StaticPageSitemap,
    'blog': BlogSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('billing/', include('billing.urls')),
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('', include('public_site.urls', namespace='public_site')),
    path('workspace/', include('workspace_admin.urls', namespace='workspace_admin')),
    path('console/', include('console_admin.urls', namespace='console_admin')),
    path('community/', include('community_forum.urls', namespace='community_forum')),
    path('i18n/', include('django.conf.urls.i18n')),

    # API v1
    path('api/v1/', include('bengalbound_core.api_urls')),

    # Swagger / OpenAPI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('hub/<slug:slug>/board/', include('modules.task_board.urls', namespace='task_board')),
    path('hub/<slug:slug>/chat/', include('modules.team_chat.urls', namespace='team_chat')),

    # Call Center
    path('hub/<slug:slug>/call-center/', include('modules.call_center.urls', namespace='call_center')),

    # CRM & Sales
    path('hub/<slug:slug>/crm/', include('modules.crm.urls', namespace='crm')),
    path('hub/<slug:slug>/leads/', include('modules.leads.urls', namespace='leads')),
    path('hub/<slug:slug>/invoicing/', include('modules.invoicing.urls', namespace='invoicing')),
    path('hub/<slug:slug>/contracts/', include('modules.contracts.urls', namespace='contracts')),

    # HR & People
    path('hub/<slug:slug>/hr/', include('modules.hr.urls', namespace='hr')),
    path('hub/<slug:slug>/payroll/', include('modules.payroll.urls', namespace='payroll')),
    path('hub/<slug:slug>/recruitment/', include('modules.recruitment.urls', namespace='recruitment')),
    path('hub/<slug:slug>/attendance/', include('modules.attendance.urls', namespace='attendance')),
    path('hub/<slug:slug>/shifts/', include('modules.shift_planning.urls', namespace='shift_planning')),
    path('hub/<slug:slug>/training/', include('modules.training.urls', namespace='training')),
    path('hub/<slug:slug>/expense/', include('modules.expense.urls', namespace='expense')),

    # Finance
    path('hub/<slug:slug>/accounting/', include('modules.accounting.urls', namespace='accounting')),
    path('hub/<slug:slug>/budgeting/', include('modules.budgeting.urls', namespace='budgeting')),
    path('hub/<slug:slug>/financials/', include('modules.financials.urls', namespace='financials')),

    # Project Management
    path('hub/<slug:slug>/projects/', include('modules.projects.urls', namespace='projects')),

    # Factory Operations Hub
    path('hub/<slug:slug>/factory/', include('modules.factory_ops.urls', namespace='factory_ops')),

    # Operations
    path('hub/<slug:slug>/inventory/', include('modules.inventory.urls', namespace='inventory')),
    path('hub/<slug:slug>/orders/', include('modules.order_mgmt.urls', namespace='order_mgmt')),
    path('hub/<slug:slug>/bom/', include('modules.bom.urls', namespace='bom')),
    path('hub/<slug:slug>/production/', include('modules.production.urls', namespace='production')),
    path('hub/<slug:slug>/quality/', include('modules.quality_control.urls', namespace='quality_control')),
    path('hub/<slug:slug>/maintenance/', include('modules.maintenance.urls', namespace='maintenance')),
    path('hub/<slug:slug>/delivery/', include('modules.delivery.urls', namespace='delivery')),

    # Commerce
    path('hub/<slug:slug>/pos/', include('modules.pos.urls', namespace='pos')),
    path('hub/<slug:slug>/ecommerce/', include('modules.ecommerce.urls', namespace='ecommerce')),
    path('hub/<slug:slug>/loyalty/', include('modules.loyalty.urls', namespace='loyalty')),
    path('hub/<slug:slug>/booking/', include('modules.booking.urls', namespace='booking')),
    path('hub/<slug:slug>/tables/', include('modules.table_mgmt.urls', namespace='table_mgmt')),

    # Marketing & Comms
    path('hub/<slug:slug>/email-marketing/', include('modules.email_marketing.urls', namespace='email_marketing')),
    path('hub/<slug:slug>/announcements/', include('modules.announcements.urls', namespace='announcements')),
    path('hub/<slug:slug>/documents/', include('modules.documents.urls', namespace='documents')),
    path('hub/<slug:slug>/website/', include('modules.website.urls', namespace='website')),

    # Intelligence
    path('hub/<slug:slug>/reports/', include('modules.reports.urls', namespace='reports')),
    path('hub/<slug:slug>/analytics/', include('modules.ai_analytics.urls', namespace='ai_analytics')),
    path('hub/<slug:slug>/assistant/', include('modules.ai_assistant.urls', namespace='ai_assistant')),
    path('hub/<slug:slug>/dashboard-pro/', include('modules.dashboard_pro.urls', namespace='dashboard_pro')),

    # Creation Suite
    path('hub/<slug:slug>/docs/', include('modules.docs.urls', namespace='docs')),
    path('hub/<slug:slug>/sheets/', include('modules.sheets.urls', namespace='sheets')),
    path('hub/<slug:slug>/slides/', include('modules.slides.urls', namespace='slides')),
    path('hub/<slug:slug>/forms/', include('modules.forms_builder.urls', namespace='forms_builder')),

    # Communication & Productivity
    path('hub/<slug:slug>/mail/', include('modules.business_mail.urls', namespace='business_mail')),
    path('hub/<slug:slug>/meet/', include('modules.video_meet.urls', namespace='video_meet')),
    path('hub/<slug:slug>/drive/', include('modules.cloud_drive.urls', namespace='cloud_drive')),
    path('hub/<slug:slug>/calendar/', include('modules.business_calendar.urls', namespace='business_calendar')),

    # Manufacturing & Industrial
    path('hub/erp/', include('modules.erp.urls', namespace='erp')),
    path('hub/mes/', include('modules.mes.urls', namespace='mes')),
    path('hub/plm/', include('modules.plm.urls', namespace='plm')),
    path('hub/cadcam/', include('modules.cadcam.urls', namespace='cadcam')),
    path('hub/assets/', include('modules.asset_management.urls', namespace='asset_management')),

    # Automotive
    path('hub/workshop/', include('modules.workshop.urls', namespace='workshop')),
    path('hub/dms/', include('modules.dms.urls', namespace='dms')),
    path('hub/dvi/', include('modules.dvi.urls', namespace='dvi')),

    # Logistics & Supply Chain
    path('hub/tms/', include('modules.tms.urls', namespace='tms')),
    path('hub/wms/', include('modules.wms.urls', namespace='wms')),

    # Consulting & Analytics
    path('hub/data-studio/', include('modules.data_studio.urls', namespace='data_studio')),
    path('hub/process-mapper/', include('modules.process_mapper.urls', namespace='process_mapper')),

    # Education
    path('hub/sis/', include('modules.sis.urls', namespace='sis')),
    path('hub/lms/', include('modules.lms.urls', namespace='lms')),
    path('hub/assessments/', include('modules.assessments.urls', namespace='assessments')),
    path('hub/timetable/', include('modules.timetable.urls', namespace='timetable')),
    path('hub/parent-portal/', include('modules.parent_portal.urls', namespace='parent_portal')),

    # Real Estate
    path('hub/properties/', include('modules.property_listings.urls', namespace='property_listings')),
    path('hub/deals/', include('modules.deal_flow.urls', namespace='deal_flow')),
    path('hub/commission/', include('modules.commission.urls', namespace='commission')),
    path('hub/re-marketing/', include('modules.re_marketing.urls', namespace='re_marketing')),
    path('hub/re-portal/', include('modules.re_client_portal.urls', namespace='re_client_portal')),

    # Retail & Wholesale
    path('hub/omnichannel/', include('modules.omnichannel.urls', namespace='omnichannel')),
    path('hub/planogram/', include('modules.planogram.urls', namespace='planogram')),
    path('hub/product-catalog/', include('modules.product_catalog.urls', namespace='product_catalog')),
    path('hub/b2b/', include('modules.b2b_portal.urls', namespace='b2b_portal')),
    path('hub/store-ops/', include('modules.store_ops.urls', namespace='store_ops')),

    # Travel & Accommodation
    path('hub/<slug:slug>/pms/', include('modules.pms.urls', namespace='pms')),
    path('hub/<slug:slug>/channels/', include('modules.channel_manager.urls', namespace='channel_manager')),
    path('hub/<slug:slug>/rates/', include('modules.rate_manager.urls', namespace='rate_manager')),
    path('hub/<slug:slug>/travel-crm/', include('modules.travel_crm.urls', namespace='travel_crm')),
    path('hub/<slug:slug>/groups/', include('modules.group_bookings.urls', namespace='group_bookings')),
    path('hub/<slug:slug>/travel-desk/', include('modules.travel_desk.urls', namespace='travel_desk')),
    path('hub/<slug:slug>/hosp-ops/', include('modules.hospitality_ops.urls', namespace='hospitality_ops')),

    # Personal Care & Home & Garden
    path('hub/<slug:slug>/care/', include('modules.care_manager.urls', namespace='care_manager')),
    path('hub/<slug:slug>/garden/', include('modules.garden_ops.urls', namespace='garden_ops')),
    path('hub/<slug:slug>/data/', include('modules.data_collection.urls', namespace='data_collection')),

    # Public form submission (no business slug — accessible without login)
    path('f/<slug:form_slug>/', form_public, name='form_public'),

    path('hub/', include('hub.urls', namespace='hub')),
    path('serea/', include('serea.urls', namespace='serea')),
    path('agents/', include('agents.urls')),

    # Generic agent API — run / logs / status / approvals / decide (all 30 agents)
    path('hub/<slug:slug>/agents/<str:agent_slug>/api/', include('agents.api_urls')),

    # AI Agents REST APIs
    path('hub/<slug:slug>/agents/aria/', include('agents.aria.urls', namespace='aria')),
    path('hub/<slug:slug>/agents/crux/', include('agents.crux.urls', namespace='crux')),
    path('hub/<slug:slug>/agents/mira/', include('agents.mira.urls', namespace='mira')),
    path('hub/<slug:slug>/agents/lead-hunter/', include('agents.lead_hunter.urls', namespace='lead_hunter')),
    path('hub/<slug:slug>/agents/atlas/', include('agents.atlas.urls', namespace='atlas')),
    path('hub/<slug:slug>/agents/babel/', include('agents.babel.urls', namespace='babel')),
    path('hub/<slug:slug>/agents/cash/', include('agents.cash.urls', namespace='cash')),
    path('hub/<slug:slug>/agents/clarity/', include('agents.clarity.urls', namespace='clarity')),
    path('hub/<slug:slug>/agents/concierge/', include('agents.concierge.urls', namespace='concierge')),
    path('hub/<slug:slug>/agents/content-architect/', include('agents.content_architect.urls', namespace='content_architect')),
    path('hub/<slug:slug>/agents/dox/', include('agents.dox.urls', namespace='dox')),
    path('hub/<slug:slug>/agents/flux/', include('agents.flux.urls', namespace='flux')),
    path('hub/<slug:slug>/agents/hera/', include('agents.hera.urls', namespace='hera')),
    path('hub/<slug:slug>/agents/kai/', include('agents.kai.urls', namespace='kai')),
    path('hub/<slug:slug>/agents/luma/', include('agents.luma.urls', namespace='luma')),
    path('hub/<slug:slug>/agents/medibook/', include('agents.medibook.urls', namespace='medibook')),
    path('hub/<slug:slug>/agents/merch/', include('agents.merch.urls', namespace='merch')),
    path('hub/<slug:slug>/agents/nexus/', include('agents.nexus.urls', namespace='nexus')),
    path('hub/<slug:slug>/agents/nova/', include('agents.nova.urls', namespace='nova')),
    path('hub/<slug:slug>/agents/oracle/', include('agents.oracle.urls', namespace='oracle')),
    path('hub/<slug:slug>/agents/payload/', include('agents.payload.urls', namespace='payload')),
    path('hub/<slug:slug>/agents/pulse/', include('agents.pulse.urls', namespace='pulse')),
    path('hub/<slug:slug>/agents/realt/', include('agents.realt.urls', namespace='realt')),
    path('hub/<slug:slug>/agents/reporting-bot/', include('agents.reporting_bot.urls', namespace='reporting_bot')),
    path('hub/<slug:slug>/agents/sage/', include('agents.sage.urls', namespace='sage')),
    path('hub/<slug:slug>/agents/scout/', include('agents.scout.urls', namespace='scout')),
    path('hub/<slug:slug>/agents/shield/', include('agents.shield.urls', namespace='shield')),
    path('hub/<slug:slug>/agents/tempo/', include('agents.tempo.urls', namespace='tempo')),
    path('hub/<slug:slug>/agents/voice-receptionist/', include('agents.voice_receptionist.urls', namespace='voice_receptionist')),
    path('hub/<slug:slug>/agents/content-strategist/', include('agents.content_strategist.urls', namespace='content_strategist')),
    path('hub/<slug:slug>/agents/sylvia/', include('agents.pitch_presenter.urls', namespace='pitch_presenter')),
    path('hub/<slug:slug>/agents/scribe/', include('agents.scribe.urls', namespace='scribe')),
    path('hub/<slug:slug>/agents/chloe/', include('agents.video_concierge.urls', namespace='video_concierge')),

    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': _sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
