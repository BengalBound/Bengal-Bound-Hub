"""
hub_tags — custom template tags for the BengalBound Hub sidebar.

Provides `module_url` which safely resolves a module's landing URL given its
url_namespace and the business slug. If the namespace / view-name doesn't exist
(e.g. module not yet fully implemented) it returns '#' instead of crashing.

IMPORTANT: Keep MODULE_URL_MAP in sync with _MODULE_URL_MAP in
hub/context_processors.py — both must reference the same view names.
"""
from django import template
from django.urls import reverse, NoReverseMatch

register = template.Library()

# ── Module namespace → (view_name, uses_slug) ────────────────────────────────
# True  = URL pattern expects a `slug` kwarg
# False = URL pattern has no slug (older flat-mounted modules)
MODULE_URL_MAP = {
    # Collaboration
    'task_board':        ('task_board:board_list',      True),
    'team_chat':         ('team_chat:channel_list',     True),
    # CRM & Sales
    'crm':               ('crm:index',                  True),
    'leads':             ('leads:index',                True),
    'invoicing':         ('invoicing:index',            True),
    'contracts':         ('contracts:index',            True),
    # HR & People
    'hr':                ('hr:index',                   True),
    'payroll':           ('payroll:index',              True),
    'recruitment':       ('recruitment:index',          True),
    'attendance':        ('attendance:index',           True),
    'shift_planning':    ('shift_planning:index',       True),
    'training':          ('training:index',             True),
    'expense':           ('expense:index',              True),
    # Finance
    'accounting':        ('accounting:index',           True),
    'budgeting':         ('budgeting:index',            True),
    'financials':        ('financials:index',           True),
    # Project Management
    'projects':          ('projects:index',             True),
    # Factory Operations Hub
    'factory_ops':       ('factory_ops:index',          True),
    # Operations
    'inventory':         ('inventory:product_list',    True),
    'order_mgmt':        ('order_mgmt:home',           True),
    'bom':               ('bom:home',                  True),
    'production':        ('production:home',           True),
    'quality_control':   ('quality_control:home',      True),
    'maintenance':       ('maintenance:home',          True),
    'delivery':          ('delivery:home',             True),
    # Commerce
    'pos':               ('pos:pos_home',              True),
    'ecommerce':         ('ecommerce:home',            True),
    'loyalty':           ('loyalty:home',              True),
    'booking':           ('booking:home',              True),
    'table_mgmt':        ('table_mgmt:home',           True),
    # Marketing & Comms
    'email_marketing':   ('email_marketing:home',      True),
    'announcements':     ('announcements:home',        True),
    'documents':         ('documents:home',            True),
    'website':           ('website:home',              True),
    # Intelligence
    'reports':           ('reports:index',             True),
    'ai_analytics':      ('ai_analytics:index',       True),
    'ai_assistant':      ('ai_assistant:index',       True),
    'dashboard_pro':     ('dashboard_pro:index',       True),
    # Creation Suite
    'docs':              ('docs:doc_list',             True),
    'sheets':            ('sheets:sheet_list',         True),
    'slides':            ('slides:presentation_list',  True),
    'forms_builder':     ('forms_builder:form_list',   True),
    # Communication & Productivity
    'business_mail':     ('business_mail:mail_home',   True),
    'video_meet':        ('video_meet:meet_home',      True),
    'cloud_drive':       ('cloud_drive:drive_home',    True),
    'business_calendar': ('business_calendar:calendar_home', True),
    # Manufacturing & Industrial (mounted at hub/<ns>/<slug>/)
    'erp':               ('erp:dashboard',             True),
    'mes':               ('mes:dashboard',             True),
    'plm':               ('plm:dashboard',             True),
    'cadcam':            ('cadcam:home',               True),
    'asset_management':  ('asset_management:dashboard',True),
    # Automotive
    'workshop':          ('workshop:dashboard',        True),
    'dms':               ('dms:dashboard',             True),
    'dvi':               ('dvi:home',                  True),
    # Logistics
    'tms':               ('tms:dashboard',             True),
    'wms':               ('wms:dashboard',             True),
    # Consulting & Analytics
    'data_studio':       ('data_studio:home',          True),
    'process_mapper':    ('process_mapper:home',       True),
    # Education
    'sis':               ('sis:dashboard',             True),
    'lms':               ('lms:home',                 True),
    'assessments':       ('assessments:home',          True),
    'timetable':         ('timetable:home',            True),
    'parent_portal':     ('parent_portal:home',        True),
    # Retail & Wholesale
    'omnichannel':       ('omnichannel:home',          True),
    'planogram':         ('planogram:home',            True),
    'product_catalog':   ('product_catalog:home',      True),
    'b2b_portal':        ('b2b_portal:home',           True),
    'store_ops':         ('store_ops:home',            True),
    # Real Estate
    'property_listings': ('property_listings:home',    True),
    'deal_flow':         ('deal_flow:home',            True),
    'commission':        ('commission:home',           True),
    're_marketing':      ('re_marketing:home',         True),
    're_client_portal':  ('re_client_portal:home',     True),
    # Travel & Accommodation
    'pms':               ('pms:home',                 True),
    'channel_manager':   ('channel_manager:home',      True),
    'rate_manager':      ('rate_manager:home',         True),
    'travel_crm':        ('travel_crm:home',           True),
    'group_bookings':    ('group_bookings:home',       True),
    'travel_desk':       ('travel_desk:home',          True),
    'hospitality_ops':   ('hospitality_ops:home',      True),
    # Personal Care & Home & Garden
    'care_manager':      ('care_manager:home',         True),
    'garden_ops':        ('garden_ops:home',           True),
    'data_collection':   ('data_collection:home',      True),
}


@register.simple_tag
def module_url(namespace, slug):
    """
    Return the URL for a module's landing page.
    Falls back to '#' if the namespace/view is not yet implemented.

    Usage in templates:
        {% load hub_tags %}
        {% module_url tm.module.url_namespace current_business.slug as mod_url %}
        <a href="{{ mod_url }}">...</a>
    """
    if not namespace:
        return '#'
    entry = MODULE_URL_MAP.get(namespace)
    if not entry:
        return '#'
    view_name, uses_slug = entry
    try:
        if uses_slug:
            return reverse(view_name, kwargs={'slug': slug})
        else:
            return reverse(view_name)
    except NoReverseMatch:
        return '#'
