from django.db import models
from django.conf import settings

# Tracking Models
class TrafficLog(models.Model):
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_consent_given = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ip_address} - {self.timestamp}"

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

# WaaS and AI Tracking Models
class WaaSSite(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='waas_sites')
    domain = models.CharField(max_length=255, unique=True)
    api_key = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.domain

class AIEmployeeTier(models.Model):
    TIERS = (
        ('intern', 'Intern Level (Free)'),
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
    )
    # Roles the AI Employee can be assigned (e.g. Social Media Moderator, Support Agent)
    AI_ROLES = (
        ('social_media_moderator', 'Social Media Moderator'),
        ('support_agent', 'Support Agent'),
        ('content_writer', 'Content Writer'),
        ('data_analyst', 'Data Analyst'),
        ('sales_assistant', 'Sales Assistant'),
        ('general', 'General Purpose'),
    )
    name = models.CharField(max_length=20, choices=TIERS, unique=True)
    description = models.TextField()
    token_limit = models.IntegerField(help_text="Tokens per month, 0 for unlimited", default=1000000)
    role = models.CharField(max_length=50, choices=AI_ROLES, default='general', help_text="Primary function of this AI Employee tier")
    n8n_workflow_json = models.JSONField(null=True, blank=True, help_text="n8n workflow configuration JSON for this tier")
    monthly_price_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, help_text="Monthly price in USD. 0 = Free tier.")

    def __str__(self):
        return self.get_name_display()

class HiredAIEmployee(models.Model):
    employer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='hired_ais')
    tier = models.ForeignKey(AIEmployeeTier, on_delete=models.SET_NULL, null=True)
    agent_catalog = models.ForeignKey('agents.AgentCatalog', on_delete=models.SET_NULL, null=True, blank=True, related_name='hired_instances')
    ai_name = models.CharField(max_length=100, default="Serea")
    tokens_used_this_month = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    hired_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ai_name} ({self.employer.email})"

class Subscription(models.Model):
    """
    Tracks which client has hired which AI tier and the NowPayments billing cycle.
    Created automatically when a client completes an AI hiring payment.
    """
    BILLING_STATUS = (
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
        ('trialing', 'Trialing'),
    )
    BILLING_CYCLE = (
        ('monthly', 'Monthly'),
        ('annual', 'Annual'),
    )
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    hired_ai = models.OneToOneField(HiredAIEmployee, on_delete=models.CASCADE, related_name='subscription')
    tier = models.ForeignKey(AIEmployeeTier, on_delete=models.SET_NULL, null=True)
    # NowPayments Integration Fields
    nowpayments_order_id = models.CharField(max_length=255, blank=True, null=True, help_text="NowPayments payment ID")
    nowpayments_invoice_url = models.URLField(blank=True, null=True)
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE, default='monthly')
    status = models.CharField(max_length=20, choices=BILLING_STATUS, default='trialing')
    amount_paid_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    # Billing Period
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    next_renewal_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Sub #{self.id} - {self.client.email} [{self.tier}] ({self.status})"

# Admin Management Models
class UserNotification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{'Read' if self.is_read else 'Unread'}] {self.title} - {self.user.email}"

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    description = models.CharField(max_length=255, help_text="What was purchased? (e.g. Mid Tier AI Employee)")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.client.email} ({self.status})"

class ModulePricingConfig(models.Model):
    """Per-module pricing set by workspace admin. Linked by module_id string."""
    module_id = models.CharField(max_length=50, unique=True)
    module_name = models.CharField(max_length=100, blank=True)
    monthly_price_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    annual_price_usd = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['module_name']

    def __str__(self):
        return f"{self.module_name or self.module_id}: ${self.monthly_price_usd}/mo"


class AdvancePlanQuote(models.Model):
    """Custom quote for an Advance plan client."""
    STATUS = [
        ('pending', 'Pending Review'),
        ('sent', 'Quote Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    business = models.ForeignKey(
        'bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='advance_quotes'
    )
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='advance_quotes'
    )
    selected_modules = models.JSONField(default=list, help_text="List of module_ids")
    requested_storage_gb = models.FloatField(default=100)
    installation_types = models.JSONField(default=list, help_text="e.g. ['cloud','ip_locked']")
    notes = models.TextField(blank=True)

    # Admin sets these
    base_price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    final_price_usd = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    admin_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Quote for {self.business.name} ({self.get_status_display()})"


class Affiliate(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='affiliate_profile')
    affiliate_code = models.CharField(max_length=50, unique=True)
    commission_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Affiliate: {self.user.email} ({self.affiliate_code})"

# Internal Project & Task Management
class Project(models.Model):
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='client_projects')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=(
        ('planning', 'Planning'),
        ('active', 'Active'),
        ('review', 'In Review'),
        ('completed', 'Completed'),
        ('on_hold', 'On Hold')
    ), default='planning')
    manager = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_projects', limit_choices_to={'role__in': ['super_admin', 'manager']})
    start_date = models.DateField(null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Task(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=(
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done')
    ), default='todo')
    priority = models.CharField(max_length=20, choices=(
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ), default='medium')
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks', limit_choices_to={'role__in': ['super_admin', 'manager', 'employee', 'contractor']})
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.title} - {self.title}"

# Internal Finance & Bookkeeping
class FinanceRecord(models.Model):
    RECORD_TYPE = (
        ('income', 'Income'),
        ('expense', 'Expense')
    )
    title = models.CharField(max_length=200)
    record_type = models.CharField(max_length=20, choices=RECORD_TYPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()
    category = models.CharField(max_length=100, help_text="E.g., Server Costs, Client Payment, Payroll")
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='recorded_finances')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_record_type_display()} - {self.title}: ${self.amount}"

