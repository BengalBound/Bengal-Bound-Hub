from django.db import models
from django.utils import timezone
from accounts.models import User


class AccountCategory(models.Model):
    TYPE = [('asset', 'Asset'), ('liability', 'Liability'), ('equity', 'Equity'), ('income', 'Income'), ('expense', 'Expense')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='acc_categories')
    name = models.CharField(max_length=100)
    account_type = models.CharField(max_length=20, choices=TYPE)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Account(models.Model):
    TYPE = [('asset', 'Asset'), ('liability', 'Liability'), ('equity', 'Equity'), ('income', 'Income'), ('expense', 'Expense')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='acc_accounts')
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=200)
    account_type = models.CharField(max_length=20, choices=TYPE)
    category = models.ForeignKey(AccountCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='accounts')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    opening_balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    currency = models.CharField(max_length=5, default='USD')

    class Meta:
        ordering = ['code']
        unique_together = [('business', 'code')]

    def __str__(self):
        return f"{self.code} — {self.name}"

    def get_balance(self):
        agg = self.journal_lines.aggregate(
            total_debit=models.Sum('debit'),
            total_credit=models.Sum('credit'),
        )
        debits = agg['total_debit'] or 0
        credits = agg['total_credit'] or 0
        if self.account_type in ('asset', 'expense'):
            return self.opening_balance + debits - credits
        return self.opening_balance + credits - debits


class JournalEntry(models.Model):
    STATUS = [('draft', 'Draft'), ('posted', 'Posted'), ('voided', 'Voided')]
    TYPE = [('general', 'General'), ('sales', 'Sales'), ('purchase', 'Purchase'), ('bank', 'Bank'), ('cash', 'Cash')]

    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='acc_entries')
    reference = models.CharField(max_length=50, blank=True)
    entry_type = models.CharField(max_length=20, choices=TYPE, default='general')
    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=500, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='journal_entries')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Journal Entries'

    def __str__(self):
        return f"JE-{self.pk} | {self.date} | {self.description[:50]}"

    def total_debits(self):
        return self.lines.aggregate(s=models.Sum('debit'))['s'] or 0

    def total_credits(self):
        return self.lines.aggregate(s=models.Sum('credit'))['s'] or 0

    def is_balanced(self):
        return abs(self.total_debits() - self.total_credits()) < 0.01


class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name='journal_lines')
    description = models.CharField(max_length=300, blank=True)
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ['pk']

    def __str__(self):
        return f"{self.account} | Dr:{self.debit} Cr:{self.credit}"


class TaxRate(models.Model):
    TYPE = [('percentage', 'Percentage'), ('fixed', 'Fixed Amount')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='acc_tax_rates')
    name = models.CharField(max_length=100)
    rate = models.DecimalField(max_digits=6, decimal_places=3, default=0)
    tax_type = models.CharField(max_length=20, choices=TYPE, default='percentage')
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.rate}%)"


class FiscalYear(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='acc_fiscal_years')
    name = models.CharField(max_length=50)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name
