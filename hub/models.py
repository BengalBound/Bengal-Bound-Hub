import secrets
from django.db import models
from django.utils import timezone
from accounts.models import User
from simple_history.models import HistoricalRecords


# ── Industry → Priority Module IDs mapping ────────────────────────────────────
INDUSTRY_MODULE_PRIORITY = {
    # Retail & Commerce
    'shop':          ['pos', 'inventory', 'invoicing', 'crm', 'loyalty', 'omnichannel', 'product_catalog', 'ecommerce', 'cloud_drive', 'business_calendar', 'data_studio'],
    # Real Estate
    'real_estate_agency': ['property_listings', 'deal_flow', 'crm', 'leads', 'commission', 're_marketing', 're_client_portal', 'contracts', 'documents', 'business_calendar', 'task_board', 'hr', 'reports_analytics', 'data_studio'],
    'real_estate_agent':  ['property_listings', 'deal_flow', 'crm', 'leads', 're_marketing', 're_client_portal', 'contracts', 'documents', 'business_calendar', 'task_board'],
    'wholesale':     ['inventory', 'order_mgmt', 'b2b_portal', 'wms', 'erp', 'crm', 'invoicing', 'tms', 'data_studio', 'product_catalog', 'accounting', 'accounts_payable', 'bank_reconciliation', 'tax_compliance', 'leads', 'contracts'],
    'retail_chain':  ['pos', 'inventory', 'store_ops', 'omnichannel', 'planogram', 'order_mgmt', 'crm', 'loyalty', 'data_studio', 'hr', 'payroll', 'reports_analytics'],
    # Enterprise & Tech
    'fintech':       ['ai_ops', 'neural_security', 'data_ecosystem', 'cloud_infra', 'accounting', 'crm', 'reports'],
    'healthcare':    ['data_ecosystem', 'automation_bots', 'care_manager', 'booking', 'crm', 'documents', 'reports', 'ai_ops', 'cloud_infra'],
    'ecommerce':     ['cloud_infra', 'ai_assistant', 'omnichannel', 'inventory', 'wms', 'crm', 'ecommerce', 'reports'],
    # Manufacturing
    'factory':       ['erp', 'mes', 'plm', 'production', 'bom', 'inventory', 'quality_control', 'maintenance', 'asset_management', 'cadcam', 'payroll', 'hr', 'attendance', 'accounts_payable', 'bank_reconciliation', 'tax_compliance', 'autonomous_ops', 'iot_network'],
    # General Business
    'business':      ['crm', 'invoicing', 'hr', 'payroll', 'accounting', 'accounts_payable', 'bank_reconciliation', 'tax_compliance', 'task_board', 'contracts', 'docs', 'business_calendar', 'call_center'],
    # Service Station
    'station':       ['pos', 'inventory', 'maintenance', 'crm', 'invoicing', 'shift_planning'],
    # Hospitality & Food
    'restaurant':    ['pos', 'table_mgmt', 'inventory', 'shift_planning', 'loyalty', 'invoicing', 'booking'],
    'hotel':         ['pms', 'channel_manager', 'rate_manager', 'hospitality_ops', 'booking', 'table_mgmt', 'invoicing', 'crm', 'group_bookings', 'shift_planning', 'hr', 'payroll', 'loyalty', 'accounting', 'reports'],
    'resort':        ['pms', 'channel_manager', 'rate_manager', 'hospitality_ops', 'group_bookings', 'booking', 'table_mgmt', 'invoicing', 'crm', 'loyalty', 'shift_planning', 'hr', 'payroll', 'accounting', 'data_studio'],
    'hostel':        ['pms', 'booking', 'channel_manager', 'invoicing', 'crm', 'loyalty', 'shift_planning', 'hr'],
    'travel_agency': ['travel_crm', 'itinerary', 'group_bookings', 'travel_desk', 'channel_manager', 'invoicing', 'crm', 'leads', 'accounting', 'documents', 'contracts', 'business_calendar', 'email_marketing'],
    'tour_operator': ['travel_crm', 'group_bookings', 'invoicing', 'crm', 'leads', 'channel_manager', 'accounting', 'documents', 'business_calendar', 'email_marketing'],
    'corporate_travel': ['travel_desk', 'travel_crm', 'group_bookings', 'expense', 'accounting', 'crm', 'invoicing', 'reports', 'contracts', 'documents'],
    'ota':           ['channel_manager', 'rate_manager', 'pms', 'travel_crm', 'group_bookings', 'invoicing', 'crm', 'accounting', 'data_studio', 'reports'],
    # Services & Healthcare
    'clinic':        ['care_manager', 'booking', 'crm', 'invoicing', 'hr', 'attendance', 'documents', 'data_collection'],
    # Personal Care
    'salon':         ['care_manager', 'booking', 'crm', 'pos', 'invoicing', 'loyalty', 'payroll', 'hr', 'data_collection', 'email_marketing', 'accounting', 'reports'],
    'spa':           ['care_manager', 'booking', 'crm', 'pos', 'invoicing', 'loyalty', 'shift_planning', 'payroll', 'hr', 'data_collection', 'email_marketing', 'accounting'],
    'care_home':     ['care_manager', 'hr', 'payroll', 'shift_planning', 'crm', 'invoicing', 'documents', 'data_collection', 'accounting', 'reports'],
    'personal_trainer': ['care_manager', 'booking', 'crm', 'invoicing', 'data_collection', 'email_marketing', 'accounting'],
    # Home & Garden
    'landscaping':   ['garden_ops', 'crm', 'invoicing', 'pos', 'inventory', 'shift_planning', 'hr', 'payroll', 'accounting', 'data_collection', 'reports'],
    'nursery':       ['garden_ops', 'pos', 'inventory', 'crm', 'invoicing', 'ecommerce', 'accounting', 'data_collection', 'reports'],
    'florist':       ['pos', 'inventory', 'crm', 'invoicing', 'garden_ops', 'booking', 'email_marketing', 'accounting', 'reports'],
    'plumber':       ['crm', 'invoicing', 'pos', 'inventory', 'booking', 'shift_planning', 'task_board', 'accounting', 'reports'],
    'carpenter':     ['crm', 'invoicing', 'pos', 'inventory', 'booking', 'shift_planning', 'task_board', 'accounting', 'reports'],
    'electrician':   ['crm', 'invoicing', 'pos', 'inventory', 'booking', 'shift_planning', 'task_board', 'accounting', 'reports'],
    # Education
    'school':        ['sis', 'lms', 'assessments', 'timetable', 'parent_portal', 'hr', 'attendance', 'payroll', 'invoicing', 'announcements', 'business_calendar', 'docs'],
    'training_center': ['lms', 'assessments', 'sis', 'timetable', 'invoicing', 'crm', 'hr', 'attendance', 'business_calendar', 'video_meet', 'docs'],
    'university':    ['sis', 'lms', 'assessments', 'timetable', 'parent_portal', 'hr', 'payroll', 'invoicing', 'crm', 'announcements', 'docs', 'business_calendar', 'contracts'],
    'tutoring_center': ['lms', 'assessments', 'timetable', 'sis', 'invoicing', 'crm', 'booking', 'business_calendar', 'video_meet'],
    'corporate_training': ['lms', 'assessments', 'data_studio', 'process_mapper', 'invoicing', 'crm', 'hr', 'docs', 'slides', 'video_meet'],
    'driving_school': ['crm', 'invoicing', 'booking', 'business_calendar', 'accounting', 'documents', 'reports', 'team_chat'],
    # Logistics
    'warehouse':     ['inventory', 'delivery', 'order_mgmt', 'bom', 'maintenance', 'hr'],
    # Professional Services
    'agency':        ['crm', 'leads', 'invoicing', 'contracts', 'task_board', 'hr', 'docs', 'sheets'],
    # Automotive
    'garage':        ['workshop', 'dvi', 'invoicing', 'crm', 'inventory', 'booking', 'pos', 'shift_planning', 'hr', 'attendance', 'email_marketing'],
    'dealership':    ['dms', 'dvi', 'crm', 'leads', 'invoicing', 'inventory', 'workshop', 'accounting', 'hr', 'delivery'],
    'auto_parts':    ['inventory', 'pos', 'invoicing', 'crm', 'order_mgmt', 'delivery', 'accounting', 'ecommerce'],
    'auto_supplier': ['erp', 'inventory', 'production', 'bom', 'quality_control', 'delivery', 'crm', 'invoicing', 'plm'],
    # Logistics & Supply Chain
    'logistics':              ['tms', 'wms', 'inventory', 'delivery', 'order_mgmt', 'crm', 'invoicing', 'hr', 'fleet', 'erp', 'reports'],
    'freight_forwarder':      ['tms', 'crm', 'invoicing', 'documents', 'contracts', 'accounting', 'leads', 'reports'],
    'courier':                ['tms', 'delivery', 'crm', 'invoicing', 'shift_planning', 'hr', 'attendance', 'pos'],
    # Consulting & Professional Services
    'consulting':             ['process_mapper', 'data_studio', 'crm', 'leads', 'invoicing', 'contracts', 'docs', 'slides', 'task_board', 'hr', 'reports', 'sheets'],
    'supply_chain_consulting':['process_mapper', 'data_studio', 'tms', 'wms', 'crm', 'leads', 'invoicing', 'contracts', 'docs', 'reports'],
    'it_consulting':          ['crm', 'leads', 'invoicing', 'contracts', 'task_board', 'docs', 'sheets', 'reports', 'ai_assistant', 'cloud_drive'],
    'legal':                  ['contracts', 'documents', 'crm', 'invoicing', 'billing', 'task_board', 'hr', 'business_calendar'],
    'accounting_firm':        ['accounting', 'accounts_payable', 'bank_reconciliation', 'tax_compliance', 'invoicing', 'crm', 'payroll', 'documents', 'contracts', 'reports', 'budgeting'],
    'other':                  ['crm', 'invoicing', 'hr', 'task_board', 'documents'],
}

# Module IDs available on the Freemium / basic tier
BASIC_MODULE_IDS = [
    'task_board', 'team_chat', 'announcements',
    'business_mail', 'business_calendar', 'cloud_drive',
    'crm', 'invoicing', 'hr', 'expense',
]


BUSINESS_TYPES = [
    ('shop', 'Retail Shop'),
    ('factory', 'Factory / Manufacturing'),
    ('business', 'General Business'),
    ('station', 'Service Station'),
    ('restaurant', 'Restaurant / Café'),
    ('hotel', 'Hotel / Hospitality'),
    ('resort', 'Resort / Boutique Hotel'),
    ('hostel', 'Hostel / Guest House'),
    ('clinic', 'Clinic / Healthcare'),
    ('school', 'School / Education'),
    ('training_center', 'Training Center / Academy'),
    ('university', 'University / College'),
    ('tutoring_center', 'Tutoring Center'),
    ('corporate_training', 'Corporate Training Provider'),
    ('driving_school', 'Driving School'),
    # Real Estate
    ('real_estate_agency', 'Real Estate Agency'),
    ('real_estate_agent', 'Independent Real Estate Agent'),
    # Retail & Wholesale
    ('wholesale', 'Wholesaler / Distributor'),
    ('retail_chain', 'Retail Chain / Multi-Location Store'),
    ('warehouse', 'Warehouse / Distribution'),
    ('agency', 'Agency / Professional Services'),
    # Automotive
    ('garage', 'Garage / Auto Repair Shop'),
    ('dealership', 'Vehicle Dealership'),
    ('auto_parts', 'Auto Parts Store'),
    ('auto_supplier', 'Automotive Supplier'),
    # Logistics & Supply Chain
    ('logistics', 'Logistics & Freight Company'),
    ('freight_forwarder', 'Freight Forwarder / Customs Broker'),
    ('courier', 'Courier & Last-Mile Delivery'),
    # Travel & Accommodation
    ('travel_agency', 'Travel Agency / Tour Operator'),
    ('tour_operator', 'Tour Operator'),
    ('corporate_travel', 'Corporate Travel Management'),
    ('ota', 'Online Travel Agency (OTA)'),
    # Personal Care
    ('salon', 'Hair & Beauty Salon'),
    ('spa', 'Spa & Wellness Centre'),
    ('care_home', 'Care Home / Assisted Living'),
    ('personal_trainer', 'Personal Trainer / Fitness'),
    # Home & Garden
    ('landscaping', 'Landscaping & Garden Services'),
    ('nursery', 'Garden Nursery / Plant Shop'),
    ('florist', 'Florist'),
    ('plumber', 'Plumbing & Home Services'),
    ('carpenter', 'Carpentry & Woodwork'),
    ('electrician', 'Electrical Services'),
    # Consulting & Professional Services
    ('consulting', 'Business Consulting Firm'),
    ('supply_chain_consulting', 'Supply Chain Consulting'),
    ('it_consulting', 'IT / Technology Consulting'),
    ('legal', 'Legal / Law Firm'),
    ('accounting_firm', 'Accounting / Audit Firm'),
    ('fintech', 'Financial Technology (Fintech)'),
    ('healthcare', 'Healthcare (HealthCXare)'),
    ('ecommerce', 'E-commerce & Retail'),
    ('other', 'Other'),
]

INSTALLATION_TYPES = [
    ('cloud', 'Cloud Hosted'),
    ('ip_locked', 'IP-Locked Cloud'),
    ('self_hosted', 'Self Hosted'),
]


class BusinessInstance(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_businesses')
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100, unique=True, help_text="Auto-generated URL key, e.g. 'acme-corp' → /hub/acme-corp/")
    business_type = models.CharField(max_length=30, choices=BUSINESS_TYPES, default='business')
    installation_type = models.CharField(max_length=20, choices=INSTALLATION_TYPES, default='cloud')

    tagline = models.CharField(max_length=200, blank=True)
    business_email = models.EmailField(blank=True)
    business_phone = models.CharField(max_length=30, blank=True)
    business_address = models.TextField(blank=True)
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True)

    # Storage quota (MB)
    storage_used_mb = models.FloatField(default=0.0)
    storage_limit_mb = models.FloatField(default=512.0)

    # IP-Locked: list of allowed IP addresses/CIDRs ["192.168.1.1", "10.0.0.0/24"]
    allowed_ips = models.JSONField(default=list, blank=True)

    # Self-Hosted: unique token used for backdoor sync
    sync_token = models.CharField(max_length=64, blank=True, null=True, unique=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    self_hosted_url = models.URLField(blank=True, help_text="Their server URL, used to push sync requests")

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_business_type_display()})"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('hub:hub_dashboard', kwargs={'slug': self.slug})

    @property
    def storage_percent(self):
        if self.storage_limit_mb == 0:
            return 0
        return round((self.storage_used_mb / self.storage_limit_mb) * 100, 1)

    def generate_sync_token(self):
        self.sync_token = secrets.token_hex(32)
        self.save(update_fields=['sync_token'])
        return self.sync_token

    def has_module(self, module_id):
        return self.modules.filter(module__module_id=module_id, is_active=True).exists()

    def active_module_ids(self):
        return list(self.modules.filter(is_active=True).values_list('module__module_id', flat=True))

    def get_icon(self):
        icons = {
            'shop': 'bi-shop', 'factory': 'bi-building-gear', 'business': 'bi-briefcase',
            'station': 'bi-fuel-pump', 'restaurant': 'bi-cup-hot', 'hotel': 'bi-building',
            'clinic': 'bi-hospital', 'school': 'bi-mortarboard', 'warehouse': 'bi-box-seam',
            'agency': 'bi-people', 'other': 'bi-grid',
        }
        return icons.get(self.business_type, 'bi-grid')


class ModuleCatalog(models.Model):
    CATEGORIES = [
        ('operations', 'Operations'),
        ('finance', 'Finance & Accounting'),
        ('people', 'People & HR'),
        ('sales', 'Sales & CRM'),
        ('communication', 'Communication'),
        ('production', 'Production & Manufacturing'),
        ('automotive', 'Automotive'),
        ('analytics', 'Analytics & Reports'),
        ('documents', 'Documents & Storage'),
        ('ai', 'AI & Automation'),
        ('web', 'Website & Marketing'),
        ('projects', 'Project Management'),
        ('it', 'Enterprise IT & Infrastructure'),
    ]

    module_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=CATEGORIES)
    icon = models.CharField(max_length=50, default='bi-puzzle')

    is_free = models.BooleanField(default=True)
    monthly_price_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    # ['all'] applies to every business type; otherwise list specific types e.g. ['shop','factory']
    applicable_to = models.JSONField(default=list)

    # module_ids that must be active before this one can be activated
    requires_modules = models.JSONField(default=list, blank=True)

    is_available = models.BooleanField(default=True)
    is_coming_soon = models.BooleanField(default=False)

    # Django URL namespace for the module (blank = no views implemented yet)
    url_namespace = models.CharField(max_length=50, blank=True)

    display_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} ({self.module_id})"

    def is_applicable_for(self, business_type):
        return 'all' in self.applicable_to or business_type in self.applicable_to


class TenantModule(models.Model):
    TIERS = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='modules')
    module = models.ForeignKey(ModuleCatalog, on_delete=models.CASCADE, related_name='tenant_activations')
    tier = models.CharField(max_length=20, choices=TIERS, default='free')

    is_active = models.BooleanField(default=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    # Module-specific runtime configuration as JSON
    config = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = [('business', 'module')]
        ordering = ['-activated_at']

    def __str__(self):
        return f"{self.business.name} — {self.module.name}"


ACCESS_LEVEL_MAP = {
    # Owner level (set programmatically, not via role)
    'owner': 10,
    # C-Suite / Executive (9)
    'ceo': 9, 'president': 9, 'managing_director': 9,
    # C-Suite officers (8)
    'cfo': 8, 'cto': 8, 'cio': 8, 'coo': 8, 'cmo': 8, 'chro': 8, 'cso': 8,
    # Directors (8)
    'director': 8, 'technical_director': 8, 'creative_director': 8,
    'finance_director': 8, 'operations_director': 8, 'sales_director': 8,
    'hr_director': 8, 'marketing_director': 8,
    # VP Level (7)
    'vp': 7, 'vp_sales': 7, 'vp_marketing': 7, 'vp_engineering': 7,
    'vp_operations': 7, 'vp_finance': 7,
    # Audit / Compliance (7)
    'audit_manager': 7, 'compliance_officer': 7,
    # Management (6)
    'manager': 6, 'department_manager': 6, 'project_manager': 6,
    'marketing_manager': 6, 'hr_manager': 6, 'finance_manager': 6,
    'operations_manager': 6, 'production_manager': 6, 'sales_manager': 6,
    'warehouse_manager': 6, 'quality_manager': 6, 'maintenance_manager': 6,
    'it_manager': 6, 'logistics_manager': 6, 'procurement_manager': 6,
    # Assistant Management (5)
    'assistant_manager': 5,
    # Supervisory / Specialist (5)
    'team_leader': 5, 'supervisor': 5,
    'accountant': 5, 'senior_accountant': 5,
    'hr': 5, 'hr_officer': 5,
    'engineer': 5, 'senior_engineer': 5,
    'designer': 5, 'senior_designer': 5,
    'analyst': 5, 'business_analyst': 5, 'data_analyst': 5,
    'it_officer': 5, 'it_specialist': 5,
    'legal_officer': 5, 'procurement_officer': 5,
    'production_supervisor': 5, 'quality_inspector': 5,
    'maintenance_engineer': 5,
    # Associates / Mid-level (4)
    'coordinator': 4, 'associate': 4,
    'marketing_staff': 4, 'marketing_officer': 4,
    'sales': 4, 'sales_officer': 4, 'sales_rep': 4,
    'support': 4, 'customer_support': 4,
    'logistics_officer': 4, 'warehouse_officer': 4,
    'purchasing_officer': 4,
    # Junior / Entry (3)
    'junior': 3, 'junior_engineer': 3, 'junior_designer': 3,
    'junior_accountant': 3, 'junior_analyst': 3,
    'assistant': 3, 'executive_assistant': 3, 'administrative_assistant': 3,
    # Staff (2)
    'staff': 2, 'operator': 2, 'technician': 2, 'driver': 2,
    'receptionist': 2, 'cashier': 2,
    # Trainee / Intern (1)
    'intern': 1, 'trainee': 1, 'apprentice': 1,
    # Viewer (1)
    'viewer': 1,
    # Custom position — access level read from CustomPosition model
    'custom': 3,
}


class BusinessEmployee(models.Model):
    ROLES = [
        # ── Executive ──
        ('ceo', 'CEO / Chief Executive Officer'),
        ('president', 'President'),
        ('managing_director', 'Managing Director'),
        # ── C-Suite Officers ──
        ('cfo', 'CFO / Chief Financial Officer'),
        ('cto', 'CTO / Chief Technology Officer'),
        ('cio', 'CIO / Chief Information Officer'),
        ('coo', 'COO / Chief Operations Officer'),
        ('cmo', 'CMO / Chief Marketing Officer'),
        ('chro', 'CHRO / Chief HR Officer'),
        ('cso', 'CSO / Chief Sales Officer'),
        # ── Directors ──
        ('director', 'Director'),
        ('technical_director', 'Technical Director'),
        ('creative_director', 'Creative Director'),
        ('finance_director', 'Finance Director'),
        ('operations_director', 'Operations Director'),
        ('sales_director', 'Sales Director'),
        ('hr_director', 'HR Director'),
        ('marketing_director', 'Marketing Director'),
        # ── VP Level ──
        ('vp', 'Vice President (VP)'),
        ('vp_sales', 'VP of Sales'),
        ('vp_marketing', 'VP of Marketing'),
        ('vp_engineering', 'VP of Engineering'),
        ('vp_operations', 'VP of Operations'),
        ('vp_finance', 'VP of Finance'),
        # ── Audit / Compliance ──
        ('audit_manager', 'Audit Manager'),
        ('compliance_officer', 'Compliance Officer'),
        # ── Management ──
        ('manager', 'Manager'),
        ('department_manager', 'Department Manager'),
        ('project_manager', 'Project Manager'),
        ('marketing_manager', 'Marketing Manager'),
        ('hr_manager', 'HR Manager'),
        ('finance_manager', 'Finance Manager'),
        ('operations_manager', 'Operations Manager'),
        ('production_manager', 'Production Manager'),
        ('sales_manager', 'Sales Manager'),
        ('warehouse_manager', 'Warehouse Manager'),
        ('quality_manager', 'Quality Manager'),
        ('maintenance_manager', 'Maintenance Manager'),
        ('it_manager', 'IT Manager'),
        ('logistics_manager', 'Logistics Manager'),
        ('procurement_manager', 'Procurement Manager'),
        # ── Assistant Management ──
        ('assistant_manager', 'Assistant Manager'),
        # ── Supervisory / Specialist ──
        ('team_leader', 'Team Leader'),
        ('supervisor', 'Supervisor'),
        ('accountant', 'Accountant'),
        ('senior_accountant', 'Senior Accountant'),
        ('hr', 'HR Officer'),
        ('hr_officer', 'HR Specialist'),
        ('engineer', 'Engineer'),
        ('senior_engineer', 'Senior Engineer'),
        ('designer', 'Designer'),
        ('senior_designer', 'Senior Designer'),
        ('analyst', 'Analyst'),
        ('business_analyst', 'Business Analyst'),
        ('data_analyst', 'Data Analyst'),
        ('it_officer', 'IT Officer'),
        ('it_specialist', 'IT Specialist'),
        ('legal_officer', 'Legal Officer'),
        ('procurement_officer', 'Procurement Officer'),
        ('production_supervisor', 'Production Supervisor'),
        ('quality_inspector', 'Quality Inspector'),
        ('maintenance_engineer', 'Maintenance Engineer'),
        # ── Associates / Mid-level ──
        ('coordinator', 'Coordinator'),
        ('associate', 'Associate'),
        ('marketing_staff', 'Marketing Staff'),
        ('marketing_officer', 'Marketing Officer'),
        ('sales', 'Sales Representative'),
        ('sales_officer', 'Sales Officer'),
        ('sales_rep', 'Sales Rep / Executive'),
        ('support', 'Customer Support'),
        ('customer_support', 'Customer Support Specialist'),
        ('logistics_officer', 'Logistics Officer'),
        ('warehouse_officer', 'Warehouse Officer'),
        ('purchasing_officer', 'Purchasing Officer'),
        # ── Junior / Entry ──
        ('junior', 'Junior Staff'),
        ('junior_engineer', 'Junior Engineer'),
        ('junior_designer', 'Junior Designer'),
        ('junior_accountant', 'Junior Accountant'),
        ('junior_analyst', 'Junior Analyst'),
        ('assistant', 'Assistant'),
        ('executive_assistant', 'Executive Assistant'),
        ('administrative_assistant', 'Administrative Assistant'),
        # ── Staff / Operators ──
        ('staff', 'Staff / Employee'),
        ('operator', 'Machine Operator'),
        ('technician', 'Technician'),
        ('driver', 'Driver'),
        ('receptionist', 'Receptionist'),
        ('cashier', 'Cashier'),
        # ── Trainee / Intern ──
        ('intern', 'Intern'),
        ('trainee', 'Trainee'),
        ('apprentice', 'Apprentice'),
        # ── View-only ──
        ('viewer', 'Viewer (Read Only)'),
        # ── Custom ──
        ('custom', 'Custom Position'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='employees')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='business_memberships')

    name = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    department = models.CharField(max_length=100, blank=True)
    role = models.CharField(max_length=30, choices=ROLES, default='staff')
    custom_position = models.ForeignKey(
        'CustomPosition', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='employees', help_text="Set when role='custom'"
    )
    pin_code = models.CharField(max_length=6, blank=True)

    # Empty list = access to all active modules; explicit list = restricted access
    accessible_modules = models.JSONField(default=list, blank=True)

    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()

    class Meta:
        ordering = ['name']
        unique_together = [('business', 'user')]

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) @ {self.business.name}"

    @property
    def access_level(self):
        if self.role == 'custom' and self.custom_position:
            return self.custom_position.access_level
        return ACCESS_LEVEL_MAP.get(self.role, 2)

    @property
    def display_role(self):
        if self.role == 'custom' and self.custom_position:
            return self.custom_position.name
        return self.get_role_display()

    @property
    def can_approve(self):
        return self.access_level >= 6

    @property
    def can_view_financials(self):
        if self.role == 'custom' and self.custom_position:
            return self.custom_position.perm_view_financials
        return self.access_level >= 7

    @property
    def is_executive(self):
        return self.access_level >= 9

    def has_permission(self, perm_name):
        """Check a named permission. Falls back to access_level for standard roles."""
        if self.role == 'custom' and self.custom_position:
            return getattr(self.custom_position, f'perm_{perm_name}', False)
        # Standard roles: derive from access level
        level = self.access_level
        defaults = {
            'view_financials': level >= 7,
            'approve_expenses': level >= 6,
            'manage_employees': level >= 8,
            'manage_modules': level >= 9,
            'access_reports': level >= 5,
            'manage_inventory': level >= 5,
            'manage_production': level >= 5,
            'manage_quality': level >= 5,
            'manage_assets': level >= 5,
            'manage_plm': level >= 6,
            'manage_erp': level >= 6,
            'manage_mes': level >= 5,
        }
        return defaults.get(perm_name, level >= 5)

    def can_access_module(self, module_id, required_role=None):
        """
        Check whether this employee can access the given module.
        accessible_modules may contain:
          - Strings (legacy format):  ["factory_ops"]
          - Dicts (new format):       [{"module": "factory_ops", "role": "manager"}]

        An empty list means full access to all active modules.
        required_role: if provided, also checks that the employee's role entry
        matches the required role (or higher access level).
        """
        if not self.accessible_modules:
            return True  # unrestricted

        for entry in self.accessible_modules:
            if isinstance(entry, str):
                if entry == module_id:
                    return True
            elif isinstance(entry, dict):
                if entry.get('module') == module_id:
                    if required_role is None:
                        return True
                    # Check role hierarchy: employee role must meet the required role level
                    emp_level = ACCESS_LEVEL_MAP.get(self.role, 2)
                    req_level = ACCESS_LEVEL_MAP.get(entry.get('role', ''), 1)
                    if emp_level >= req_level:
                        return True
        return False


class CustomPosition(models.Model):
    """
    CEO/MD-defined position with granular permissions and a custom access level.
    """
    ACCESS_CHOICES = [(i, str(i)) for i in range(1, 10)]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='custom_positions')
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True)
    access_level = models.PositiveSmallIntegerField(
        default=3, choices=ACCESS_CHOICES,
        help_text="1=viewer, 2=staff, 3=junior, 4=associate, 5=specialist, 6=manager, 7=director, 8=c-suite, 9=executive"
    )

    # Module-category permissions
    perm_view_financials = models.BooleanField(default=False)
    perm_approve_expenses = models.BooleanField(default=False)
    perm_manage_employees = models.BooleanField(default=False)
    perm_manage_modules = models.BooleanField(default=False)
    perm_access_reports = models.BooleanField(default=True)
    perm_manage_inventory = models.BooleanField(default=False)
    perm_manage_production = models.BooleanField(default=False)
    perm_manage_quality = models.BooleanField(default=False)
    perm_manage_assets = models.BooleanField(default=False)
    perm_manage_plm = models.BooleanField(default=False)
    perm_manage_erp = models.BooleanField(default=False)
    perm_manage_mes = models.BooleanField(default=False)

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('business', 'name')]
        ordering = ['-access_level', 'name']

    def __str__(self):
        return f"{self.name} (L{self.access_level}) @ {self.business.name}"


class ConnectorSession(models.Model):
    """
    Token issued to the connector desktop app, enabling remote access to
    an IP-locked or self-hosted business dashboard from any network.
    """
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='connector_sessions')
    token = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=100, blank=True, help_text="Friendly name, e.g. 'John's Laptop'")
    device_ip = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.label or self.token[:12]}… ({self.business.name})"

    @classmethod
    def generate(cls, business, label='', days_valid=30):
        import datetime
        return cls.objects.create(
            business=business,
            token=secrets.token_hex(32),
            label=label,
            expires_at=timezone.now() + datetime.timedelta(days=days_valid),
        )


class SyncLog(models.Model):
    """
    Audit trail for every sync operation between a self-hosted instance and the cloud.
    """
    SYNC_TYPES = [
        ('push', 'Push to Cloud'),
        ('pull', 'Pull from Cloud'),
        ('full', 'Full Sync'),
    ]
    STATUSES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='sync_logs')
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUSES)
    records_synced = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        ts = self.started_at.strftime('%Y-%m-%d %H:%M') if self.started_at else '—'
        return f"{self.get_sync_type_display()} — {self.business.name} ({ts})"


# ── Subscription System ────────────────────────────────────────────────────────

class HubPlanConfig(models.Model):
    """
    Workspace-admin-managed configuration for each subscription tier.
    One row per plan type; prices/limits updated from the admin panel.
    """
    PLAN_TYPES = [
        ('freemium', 'Freemium'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('advance', 'Advance'),
    ]

    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    tagline = models.CharField(max_length=255, blank=True)
    monthly_price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annual_price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    storage_gb = models.FloatField(default=5.0)

    # Installation type entitlements
    allows_cloud = models.BooleanField(default=True)
    allows_ip_locked = models.BooleanField(default=False)
    allows_self_hosted = models.BooleanField(default=False)

    # Module entitlements
    includes_basic_modules = models.BooleanField(default=True)
    includes_full_industry_set = models.BooleanField(default=False)   # Premium
    is_fully_customizable = models.BooleanField(default=False)         # Advance

    # Add-on pricing for Standard tier upgrades
    ip_locked_addon_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    self_hosted_addon_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_storage_price_per_gb = models.DecimalField(max_digits=8, decimal_places=2, default=0.50)

    # Advance plan: admin-set bundle discount
    advance_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    is_visible = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['monthly_price_usd']

    def __str__(self):
        return f"{self.display_name} (${self.monthly_price_usd}/mo)"

    @classmethod
    def get_plan(cls, plan_type):
        """Fetch plan config, falling back to defaults if not seeded yet."""
        DEFAULTS = {
            'freemium': {'storage_gb': 5,  'allows_cloud': True},
            'standard': {'storage_gb': 20, 'allows_cloud': True},
            'premium':  {'storage_gb': 50, 'allows_cloud': True, 'allows_ip_locked': True, 'includes_full_industry_set': True},
            'advance':  {'storage_gb': 100,'allows_cloud': True, 'allows_ip_locked': True, 'allows_self_hosted': True, 'is_fully_customizable': True},
        }
        try:
            return cls.objects.get(plan_type=plan_type)
        except cls.DoesNotExist:
            d = DEFAULTS.get(plan_type, DEFAULTS['freemium'])
            obj = cls(plan_type=plan_type, display_name=plan_type.title(), **d)
            return obj


class BusinessSubscription(models.Model):
    STATUS = [
        ('active', 'Active'),
        ('trial', 'Trial'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending Payment'),
    ]
    BILLING = [('monthly', 'Monthly'), ('annual', 'Annual')]
    PLAN_TYPES = [
        ('freemium', 'Freemium'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('advance', 'Advance'),
    ]

    business = models.OneToOneField(BusinessInstance, on_delete=models.CASCADE, related_name='subscription')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='freemium')
    status = models.CharField(max_length=20, choices=STATUS, default='active')
    billing_cycle = models.CharField(max_length=10, choices=BILLING, default='monthly')

    # Stripe Billing
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True, help_text="Stripe Subscription ID")
    stripe_price_id = models.CharField(max_length=255, blank=True, null=True, help_text="Stripe Price ID")

    # Storage
    extra_storage_gb = models.FloatField(default=0)

    # Standard: optional add-ons
    paid_ip_locked = models.BooleanField(default=False)
    paid_self_hosted = models.BooleanField(default=False)

    # Premium: chosen industry for included module set
    premium_industry = models.CharField(max_length=20, blank=True)

    # Advance: customized selection
    advance_selected_modules = models.JSONField(default=list, blank=True)
    advance_storage_gb = models.FloatField(default=100)
    advance_installation_types = models.JSONField(default=list, blank=True)
    advance_discount_applied = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    advance_monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.business.name} — {self.get_plan_type_display()} ({self.get_status_display()})"

    @property
    def plan_config(self):
        return HubPlanConfig.get_plan(self.plan_type)

    @property
    def total_storage_gb(self):
        if self.plan_type == 'advance':
            base = self.advance_storage_gb
        else:
            cfg = self.plan_config
            base = getattr(cfg, 'storage_gb', 5)
        return base + self.extra_storage_gb

    def allows_installation_type(self, install_type):
        if self.plan_type == 'advance':
            types = self.advance_installation_types or ['cloud']
            return install_type in types
        cfg = self.plan_config
        if install_type == 'cloud':
            return getattr(cfg, 'allows_cloud', True)
        if install_type == 'ip_locked':
            if self.paid_ip_locked:
                return True
            return getattr(cfg, 'allows_ip_locked', False)
        if install_type == 'self_hosted':
            if self.paid_self_hosted:
                return True
            return getattr(cfg, 'allows_self_hosted', False)
        return False

    def allows_module(self, module_id):
        """Check if this subscription grants access to the given module."""
        if self.plan_type == 'advance':
            return (not self.advance_selected_modules) or (module_id in self.advance_selected_modules)
        if self.plan_type in ('premium', 'standard', 'freemium'):
            if module_id in BASIC_MODULE_IDS:
                return True
            if self.plan_type == 'freemium':
                return False
            if self.plan_type == 'standard':
                # Standard gets basic only; additional modules require per-module payment
                return False
            if self.plan_type == 'premium':
                # Premium grants access to all modules
                return True
        return False

    def get_upgrade_required(self, module_id):
        """Return which plan type would grant this module, or None if already allowed."""
        if self.allows_module(module_id):
            return None
        if module_id in BASIC_MODULE_IDS:
            return None
        if self.plan_type == 'freemium':
            return 'standard'
        industry = self.premium_industry or (self.business.business_type if self.business else '')
        priority = INDUSTRY_MODULE_PRIORITY.get(industry, [])
        if module_id in priority:
            return 'premium'
        return 'advance'


class UserBusinessMembership(models.Model):
    """
    Explicit many-to-many membership: one user → many businesses (without owning them).
    BusinessInstance.owner is still the single owner; this covers invited members.
    """
    ROLES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
        ('viewer', 'Viewer'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hub_memberships')
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLES, default='member')
    invited_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_hub_invitations'
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('user', 'business')]
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} → {self.business.name} ({self.get_role_display()})"


class StorageIncreaseRequest(models.Model):
    STATUS = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='storage_requests')
    requested_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='storage_requests')
    requested_gb = models.FloatField()
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')
    approved_gb = models.FloatField(null=True, blank=True)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.business.name}: +{self.requested_gb}GB ({self.get_status_display()})"


class DashboardConfig(models.Model):
    business = models.OneToOneField(BusinessInstance, on_delete=models.CASCADE, related_name='dashboard_config')
    recommended_agents = models.JSONField(default=list, blank=True)
    layout = models.JSONField(default=dict, blank=True)  # contains widgets, layout, primary_color_suggestion
    language = models.CharField(max_length=50, default='English')
    currency = models.CharField(max_length=10, default='USD')
    payment_method = models.CharField(max_length=50, default='Stripe')
    dashboard_theme = models.CharField(max_length=50, default='default')
    primary_color = models.CharField(max_length=50, default='#63DCB8')
    is_configured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"DashboardConfig for {self.business.name}"

