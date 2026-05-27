from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class CommissionRule(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='commission_rules')
    name = models.CharField(max_length=150)
    agent = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='commission_rules', help_text='Leave blank for a default/global rule')
    agent_split_pct = models.DecimalField(max_digits=5, decimal_places=2, default=70, verbose_name='Agent Split %')
    broker_split_pct = models.DecimalField(max_digits=5, decimal_places=2, default=30, verbose_name='Broker Split %')
    referral_fee_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Referral Fee %')
    annual_cap = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, verbose_name='Annual Cap (agent stops splitting after this amount)')
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class CommissionEntry(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='commission_entries')
    agent = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='commission_entries')
    deal_reference = models.CharField(max_length=200, verbose_name='Deal / Property Reference')
    client_name = models.CharField(max_length=150, blank=True)
    close_date = models.DateField(null=True, blank=True)
    gross_commission = models.DecimalField(max_digits=14, decimal_places=2, verbose_name='Gross Commission Income (GCI)')
    agent_split_pct = models.DecimalField(max_digits=5, decimal_places=2, default=70)
    agent_amount = models.DecimalField(max_digits=14, decimal_places=2)
    broker_amount = models.DecimalField(max_digits=14, decimal_places=2)
    referral_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-close_date', '-created_at']

    def __str__(self):
        return f"{self.deal_reference} — {self.agent.user.get_full_name() if self.agent else 'N/A'}"

    @property
    def net_agent_amount(self):
        return self.agent_amount - self.referral_amount
