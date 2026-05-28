from django.db import models
from core.models import BaseModel
from django.db.models import CharField, IntegerField, JSONField, DateTimeField, BooleanField, TextField, ForeignKey as FK, CASCADE, PROTECT, SET_NULL, OneToOneField
from django.contrib.auth import get_user_model
from workspace_admin.models import HiredAIEmployee
from simple_history.models import HistoricalRecords
from .encryption import EncryptedTextField, EncryptedJSONField

User = get_user_model()

class AgentCatalog(BaseModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    role = models.CharField(max_length=200)
    description = models.TextField()
    system_prompt = models.TextField()
    category = models.CharField(max_length=100)
    tier_required = models.CharField(max_length=20, default='entry')
    is_active = models.BooleanField(default=True)
    icon = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.role})"


class AgentInstance(BaseModel):
    business       = FK('bredbound.BusinessInstance', related_name='agent_instances', on_delete=CASCADE)
    hired_employee = OneToOneField(HiredAIEmployee, null=True, blank=True, on_delete=SET_NULL)
    catalog        = FK(AgentCatalog, on_delete=PROTECT)
    status         = CharField(choices=[('idle','Idle'),('working','Working'),
                                        ('waiting','Waiting Approval'),('offline','Offline')], max_length=20)
    config         = JSONField(default=dict)   # thresholds, model overrides, notification prefs
    tokens_used_this_month = IntegerField(default=0)
    token_limit_override   = IntegerField(null=True, blank=True)
    last_run_at    = DateTimeField(null=True, blank=True)
    history        = HistoricalRecords()        # django-simple-history

    class Meta:
        unique_together = ('business', 'catalog')


class AgentLog(BaseModel):
    instance   = FK(AgentInstance, related_name='logs', on_delete=CASCADE)
    action     = CharField(max_length=200)          # e.g. "auto_resolve_ticket #47"
    outcome    = CharField(choices=[('success','Success'),('failed','Failed'),
                                    ('escalated','Escalated'),('pending','Pending')], max_length=20)
    detail     = TextField(blank=True)              # full LLM output or error
    model_used = CharField(max_length=100, blank=True)
    tokens     = IntegerField(default=0)
    duration_ms = IntegerField(default=0)


class AgentPermissionRequest(BaseModel):
    instance    = FK(AgentInstance, related_name='permission_requests', on_delete=CASCADE)
    log         = OneToOneField(AgentLog, null=True, blank=True, on_delete=SET_NULL)
    context     = TextField()                  # what the agent wants to do + why
    option_a    = TextField()                  # suggested action A
    option_b    = TextField(blank=True)        # suggested action B (optional)
    decision    = CharField(null=True, blank=True, max_length=20,
                            choices=[('approved','Approved'),('denied','Denied')])
    decided_by  = FK(User, null=True, blank=True, on_delete=SET_NULL)
    decided_at  = DateTimeField(null=True, blank=True)
    executed    = BooleanField(default=False)


class AgentMemory(BaseModel):
    instance     = FK(AgentInstance, related_name='memories', on_delete=CASCADE)
    subject      = CharField(max_length=300)    # e.g. "client:acme-corp", "uk-gdpr-rules"
    memory_type  = CharField(choices=[('entity','Entity'),('instruction','Instruction'),
                                      ('context','Context'),('outcome','Outcome')], max_length=20)
    content      = TextField()
    importance   = CharField(choices=[('low','Low'),('medium','Medium'),
                                      ('high','High'),('critical','Critical')], default='medium', max_length=20)
    expires_at   = DateTimeField(null=True, blank=True)   # None = permanent
    is_active    = BooleanField(default=True)

    class Meta:
        ordering = ['-importance', '-updated_at']


class AgentIntegration(BaseModel):
    instance  = FK(AgentInstance, related_name='integrations', on_delete=CASCADE)
    platform  = CharField(max_length=100)     # 'slack','email','github','shopify', etc.
    label     = CharField(max_length=200)     # human readable: "Acme Corp Slack"
    credential = EncryptedTextField()         # API key / OAuth token (Fernet encrypted)
    config    = JSONField(default=dict)       # platform-specific: channel, repo, store URL
    status    = CharField(choices=[('connected','Connected'),('error','Error'),
                                   ('expired','Expired')], default='connected', max_length=20)
    last_used_at = DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('instance', 'platform', 'label')


class AgentWebhookEndpoint(BaseModel):
    instance   = FK(AgentInstance, related_name='webhook_endpoints', on_delete=CASCADE)
    source     = CharField(max_length=100)     # 'github', 'shopify', 'stripe', etc.
    url_token  = CharField(max_length=64, unique=True)  # /agents/webhook/<token>/
    secret     = CharField(max_length=256, blank=True)  # HMAC verification key
    is_active  = BooleanField(default=True)
    last_triggered_at = DateTimeField(null=True, blank=True)
    event_count = IntegerField(default=0)
