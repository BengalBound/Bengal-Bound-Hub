import hashlib
import json
from django.db import models
from django.utils import timezone


class ComplianceRule(models.Model):
    CATEGORIES = [
        ('legal', 'Legal'),
        ('ethics', 'Ethics & Discrimination'),
        ('cybersecurity', 'Cybersecurity'),
        ('privacy', 'Data Privacy'),
        ('scope', 'Scope Authorization'),
        ('harm', 'Harm Prevention'),
        ('ai_ethics', 'AI Ethics'),
    ]
    name              = models.CharField(max_length=300)
    category          = models.CharField(max_length=20, choices=CATEGORIES)
    standard_ref      = models.CharField(max_length=200)  # e.g. 'GDPR Art.6', 'NIST CSF 2.0 GV.1'
    jurisdiction      = models.CharField(max_length=200)  # 'BD', 'US', 'EU', 'Global', 'AU'
    applies_to_agents = models.JSONField(default=list)    # ['all'] or ['hera', 'medibook']
    rule_description  = models.TextField()
    is_active         = models.BooleanField(default=True)
    effective_date    = models.DateField()
    review_date       = models.DateField()

    def __str__(self):
        return f"[{self.standard_ref}] {self.name}"


class ComplianceCheck(models.Model):
    """Append-only log — no UPDATE or DELETE ever."""
    DECISIONS = [
        ('approved', 'Approved'),
        ('blocked', 'Blocked'),
        ('escalated', 'Escalated to Human'),
        ('auto_rejected', 'Auto-Rejected'),
    ]
    # Business context — uses bredbound.BusinessInstance
    business         = models.ForeignKey(
        'bredbound.BusinessInstance',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='compliance_checks',
    )
    agent_name        = models.CharField(max_length=50)
    client_country    = models.CharField(max_length=10)   # ISO country code
    end_user_country  = models.CharField(max_length=10, blank=True)
    action_type       = models.CharField(max_length=100)
    action_payload    = models.JSONField()
    decision          = models.CharField(max_length=20, choices=DECISIONS)
    failed_check      = models.CharField(max_length=50, blank=True)
    failed_standard   = models.CharField(max_length=200, blank=True)
    ai_reasoning      = models.TextField()  # LiteLLM-generated reasoning
    confidence        = models.FloatField()
    rules_applied     = models.ManyToManyField(ComplianceRule)
    log_hash          = models.CharField(max_length=64, blank=True)   # SHA-256 of this record
    prev_hash         = models.CharField(max_length=64, blank=True)   # Chained integrity
    checked_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        permissions = [('cannot_delete_log', 'Cannot delete compliance log')]

    def __str__(self):
        return f"{self.agent_name} → {self.decision} ({self.checked_at})"

    def save(self, *args, **kwargs):
        # Immutable check
        if self.pk:
            raise PermissionError("ComplianceCheck records are immutable and cannot be updated.")
        
        # Chained integrity
        last_check = ComplianceCheck.objects.order_by('-checked_at', '-id').first()
        if last_check:
            self.prev_hash = last_check.log_hash
        else:
            self.prev_hash = '0' * 64

        # Compute SHA-256 hash before saving
        if not self.checked_at:
            self.checked_at = timezone.now()

        payload_str = json.dumps(self.action_payload, sort_keys=True)
        hash_input = (
            f"{self.business_id or ''}|{self.agent_name}|{self.client_country}|"
            f"{self.end_user_country}|{self.action_type}|{payload_str}|"
            f"{self.decision}|{self.failed_check}|{self.failed_standard}|"
            f"{self.ai_reasoning}|{self.confidence}|{self.prev_hash}|"
            f"{self.checked_at.isoformat()}"
        )
        self.log_hash = hashlib.sha256(hash_input.encode('utf-8')).hexdigest()
        
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("ComplianceCheck records are immutable and cannot be deleted.")


class SecurityIncident(models.Model):
    SEVERITY = [('low','Low'),('medium','Medium'),('high','High'),('critical','Critical')]
    STATUS   = [('open','Open'),('contained','Contained'),('notifying','Notifying Regulators'),
                ('resolved','Resolved'),('post_incident_review','Post-Incident Review')]
    compliance_check      = models.OneToOneField(ComplianceCheck, on_delete=models.PROTECT, related_name='incident')
    severity              = models.CharField(max_length=10, choices=SEVERITY)
    status                = models.CharField(max_length=30, choices=STATUS, default='open')
    affected_records      = models.IntegerField(null=True, blank=True)
    regulatory_breach     = models.BooleanField(default=False)
    regulations_triggered = models.JSONField(default=list)   # ['GDPR', 'AU_NDB']
    notification_draft    = models.TextField(blank=True)
    notification_sent     = models.BooleanField(default=False)
    notification_sent_at  = models.DateTimeField(null=True, blank=True)
    root_cause            = models.TextField(blank=True)
    resolution_notes      = models.TextField(blank=True)
    resolved_at           = models.DateTimeField(null=True, blank=True)
    created_at            = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Incident ({self.severity}) — Check {self.check_id} — {self.status}"
