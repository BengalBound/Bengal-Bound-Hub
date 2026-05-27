from django.db import models
from django.utils import timezone
from accounts.models import User


class LoyaltyProgram(models.Model):
    REWARD_TYPE = [('points', 'Points'), ('cashback', 'Cashback'), ('tiers', 'Tier-Based')]
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='loyalty_programs')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    reward_type = models.CharField(max_length=10, choices=REWARD_TYPE, default='points')
    points_per_currency = models.DecimalField(max_digits=8, decimal_places=2, default=1, help_text='Points earned per currency unit spent')
    currency_per_point = models.DecimalField(max_digits=8, decimal_places=4, default=0.01, help_text='Currency value per point when redeeming')
    min_redemption_points = models.IntegerField(default=100)
    is_active = models.BooleanField(default=True)
    expiry_days = models.IntegerField(default=0, help_text='0 = no expiry')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class LoyaltyTier(models.Model):
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='tiers')
    name = models.CharField(max_length=100)
    min_points = models.IntegerField(default=0)
    point_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.0)
    color = models.CharField(max_length=7, default='#f59e0b')
    benefits = models.TextField(blank=True)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['position', 'min_points']

    def __str__(self):
        return f"{self.name} ({self.program.name})"


class LoyaltyMember(models.Model):
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='loyalty_memberships')
    card_number = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    tier = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True)
    total_points = models.IntegerField(default=0)
    lifetime_points = models.IntegerField(default=0)
    total_spend = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-total_points']

    def __str__(self):
        return f"{self.name} ({self.card_number})"


class PointTransaction(models.Model):
    TYPE = [('earn', 'Earned'), ('redeem', 'Redeemed'), ('expire', 'Expired'), ('adjust', 'Adjustment'), ('bonus', 'Bonus')]
    member = models.ForeignKey(LoyaltyMember, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=10, choices=TYPE)
    points = models.IntegerField()
    description = models.CharField(max_length=300, blank=True)
    reference = models.CharField(max_length=100, blank=True)
    expires_at = models.DateField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_transaction_type_display()}: {self.points} pts — {self.member}"
