from collections import OrderedDict
from django.urls import reverse
from .models import BusinessInstance, TenantModule, BusinessEmployee

# ── Module → URL mapping ──────────────────────────────────────────────────────
_MODULE_URL_MAP = {
    'task_board':        ('task_board:board_list',           True),
    'team_chat':         ('team_chat:channel_list',          True),
    'crm':               ('crm:index',                      True),
    'leads':             ('leads:index',                    True),
    'invoicing':         ('invoicing:index',                True),
    'contracts':         ('contracts:index',                True),
    'hr':                ('hr:index',                       True),
    'payroll':           ('payroll:index',                  True),
    'recruitment':       ('recruitment:index',              True),
    'attendance':        ('attendance:index',               True),
    'shift_planning':    ('shift_planning:index',           True),
    'training':          ('training:index',                 True),
    'expense':           ('expense:index',                  True),
    'accounting':        ('accounting:index',               True),
    'budgeting':         ('budgeting:index',                True),
    'financials':        ('financials:index',               True),
    'projects':          ('projects:index',                 True),
    'factory_ops':       ('factory_ops:index',              True),
    'inventory':         ('inventory:index',                True),
    'order_mgmt':        ('order_mgmt:index',               True),
    'bom':               ('bom:index',                      True),
    'production':        ('production:index',               True),
    'quality_control':   ('quality_control:index',         True),
    'maintenance':       ('maintenance:index',              True),
    'delivery':          ('delivery:index',                 True),
    'pos':               ('pos:index',                      True),
    'ecommerce':         ('ecommerce:index',                True),
    'loyalty':           ('loyalty:index',                  True),
    'booking':           ('booking:index',                  True),
    'table_mgmt':        ('table_mgmt:index',               True),
    'email_marketing':   ('email_marketing:index',          True),
    'announcements':     ('announcements:index',            True),
    'documents':         ('documents:index',                True),
    'website':           ('website:index',                  True),
    'reports':           ('reports:index',                  True),
    'ai_analytics':      ('ai_analytics:index',            True),
    'ai_assistant':      ('ai_assistant:index',            True),
    'dashboard_pro':     ('dashboard_pro:index',            True),
    'docs':              ('docs:doc_list',                  True),
    'sheets':            ('sheets:sheet_list',              True),
    'slides':            ('slides:presentation_list',       True),
    'forms_builder':     ('forms_builder:form_list',        True),
    'business_mail':     ('business_mail:mail_home',        True),
    'video_meet':        ('video_meet:meet_home',           True),
    'cloud_drive':       ('cloud_drive:drive_home',         True),
    'business_calendar': ('business_calendar:calendar_home', True),
    'erp':               ('erp:dashboard',                  True),
    'mes':               ('mes:dashboard',                  True),
    'plm':               ('plm:dashboard',                  True),
    'cadcam':            ('cadcam:home',                    True),
    'asset_management':  ('asset_management:dashboard',     True),
    'workshop':          ('workshop:dashboard',             True),
    'dms':               ('dms:dashboard',                  True),
    'dvi':               ('dvi:home',                       True),
    'tms':               ('tms:dashboard',                  True),
    'wms':               ('wms:dashboard',                  True),
    'data_studio':       ('data_studio:home',               True),
    'process_mapper':    ('process_mapper:home',            True),
    'sis':               ('sis:dashboard',                  True),
    'lms':               ('lms:home',                       True),
    'assessments':       ('assessments:home',               True),
    'timetable':         ('timetable:home',                 True),
    'parent_portal':     ('parent_portal:home',             True),
    'omnichannel':       ('omnichannel:home',               True),
    'planogram':         ('planogram:home',                 True),
    'product_catalog':   ('product_catalog:home',           True),
    'b2b_portal':        ('b2b_portal:home',                True),
    'store_ops':         ('store_ops:home',                 True),
    'property_listings': ('property_listings:home',         True),
    'deal_flow':         ('deal_flow:home',                 True),
    'commission':        ('commission:home',                True),
    're_marketing':      ('re_marketing:home',              True),
    're_client_portal':  ('re_client_portal:home',          True),
    'pms':               ('pms:home',                       True),
    'channel_manager':   ('channel_manager:home',           True),
    'rate_manager':      ('rate_manager:home',              True),
    'travel_crm':        ('travel_crm:home',                True),
    'group_bookings':    ('group_bookings:home',            True),
    'travel_desk':       ('travel_desk:home',               True),
    'hospitality_ops':   ('hospitality_ops:home',           True),
    'care_manager':      ('care_manager:home',              True),
    'garden_ops':        ('garden_ops:home',                True),
    'data_collection':   ('data_collection:home',           True),
}

# ── Module categories — drives sidebar grouping and dashboard tiles ───────────
MODULE_CATEGORIES = OrderedDict([
    ('Operations', {
        'icon': 'bi-gear-wide-connected', 'color': '#f97316',
        'ids': ['factory_ops', 'mes', 'production', 'workshop', 'maintenance',
                'quality_control', 'asset_management', 'bom', 'cadcam', 'plm',
                'process_mapper', 'planogram', 'store_ops', 'erp'],
    }),
    ('Finance & Accounting', {
        'icon': 'bi-cash-stack', 'color': '#22c55e',
        'ids': ['accounting', 'financials', 'invoicing', 'payroll', 'budgeting',
                'expense', 'commission'],
    }),
    ('People & HR', {
        'icon': 'bi-people-fill', 'color': '#38bdf8',
        'ids': ['hr', 'attendance', 'recruitment', 'training', 'shift_planning'],
    }),
    ('Sales & CRM', {
        'icon': 'bi-graph-up-arrow', 'color': '#c084fc',
        'ids': ['crm', 'leads', 'deal_flow', 'dms', 'b2b_portal', 'loyalty',
                're_client_portal', 'contracts'],
    }),
    ('Marketing & Commerce', {
        'icon': 'bi-bag-heart', 'color': '#ec4899',
        'ids': ['pos', 'ecommerce', 'omnichannel', 'email_marketing',
                'product_catalog', 're_marketing', 'booking', 'table_mgmt'],
    }),
    ('Communications', {
        'icon': 'bi-chat-dots-fill', 'color': '#818cf8',
        'ids': ['business_mail', 'team_chat', 'video_meet', 'announcements'],
    }),
    ('Analytics & Reports', {
        'icon': 'bi-bar-chart-fill', 'color': '#fbbf24',
        'ids': ['reports', 'dashboard_pro', 'data_studio', 'ai_analytics'],
    }),
    ('Documents & Storage', {
        'icon': 'bi-folder2-open', 'color': '#94a3b8',
        'ids': ['cloud_drive', 'documents', 'docs', 'slides', 'sheets',
                'forms_builder', 'data_collection'],
    }),
    ('Projects & Tasks', {
        'icon': 'bi-kanban-fill', 'color': '#10b981',
        'ids': ['projects', 'task_board'],
    }),
    ('Logistics & Supply', {
        'icon': 'bi-truck', 'color': '#f59e0b',
        'ids': ['inventory', 'wms', 'tms', 'delivery', 'order_mgmt'],
    }),
    ('Industry Specific', {
        'icon': 'bi-building', 'color': '#e2e8f0',
        'ids': ['pms', 'channel_manager', 'rate_manager', 'hospitality_ops',
                'group_bookings', 'sis', 'lms', 'assessments', 'timetable',
                'parent_portal', 'travel_crm', 'travel_desk', 'care_manager',
                'garden_ops', 'property_listings', 'dvi'],
    }),
    ('AI & Automation', {
        'icon': 'bi-robot', 'color': '#a78bfa',
        'ids': ['ai_assistant'],
    }),
])


def _resolve_module_url(namespace, slug):
    """Return the URL for a module's landing page, or '#' if not yet implemented."""
    if not namespace:
        return '#'
    entry = _MODULE_URL_MAP.get(namespace)
    if not entry:
        return '#'
    view_name, uses_slug = entry
    try:
        return reverse(view_name, kwargs={'slug': slug}) if uses_slug else reverse(view_name)
    except Exception:
        return '#'


def hub_context(request):
    """
    Injects business hub context into every template.
    Provides: current_business, hub_active_modules, hub_active_module_items,
              hub_active_module_categories, hub_is_owner, hub_employee,
              user_businesses.
    """
    ctx = {
        'current_business': None,
        'hub_active_modules': [],
        'hub_active_module_objects': [],
        'hub_active_module_items': [],
        'hub_active_module_categories': [],
        'hub_is_owner': False,
        'hub_employee': None,
        'user_businesses': [],
    }

    if not request.user.is_authenticated:
        return ctx

    biz = getattr(request, 'current_business', None)

    if biz:
        ctx['current_business'] = biz
        ctx['hub_is_owner'] = biz.owner == request.user

        active_qs = TenantModule.objects.filter(
            business=biz, is_active=True
        ).select_related('module').order_by('module__display_order')

        ctx['hub_active_module_objects'] = active_qs

        active_ids = [tm.module.module_id for tm in active_qs]
        ctx['hub_active_modules'] = active_ids

        items_by_id = {}
        all_items = []
        for tm in active_qs:
            item = {
                'tm': tm,
                'url': _resolve_module_url(tm.module.url_namespace, biz.slug),
            }
            all_items.append(item)
            items_by_id[tm.module.module_id] = item

        ctx['hub_active_module_items'] = all_items

        # Build categorized groups for the sidebar
        categorized = []
        for cat_name, cat_meta in MODULE_CATEGORIES.items():
            cat_items = [items_by_id[mid] for mid in cat_meta['ids'] if mid in items_by_id]
            if cat_items:
                categorized.append({
                    'name': cat_name,
                    'icon': cat_meta['icon'],
                    'color': cat_meta['color'],
                    'items': cat_items,
                })
        ctx['hub_active_module_categories'] = categorized

        # Current user's employee record for this business
        ctx['hub_employee'] = BusinessEmployee.objects.filter(
            business=biz, user=request.user, is_active=True
        ).first()

    ctx['user_businesses'] = BusinessInstance.objects.filter(
        owner=request.user, is_active=True
    ).only('name', 'slug', 'business_type')[:10]

    return ctx
