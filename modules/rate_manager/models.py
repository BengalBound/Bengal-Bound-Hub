from django.db import models
from hub.models import BusinessInstance


class Season(models.Model):
    SEASON_TYPES = [
        ('peak', 'Peak'),
        ('high', 'High'),
        ('shoulder', 'Shoulder'),
        ('low', 'Low'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='seasons')
    name = models.CharField(max_length=200)
    season_type = models.CharField(max_length=10, choices=SEASON_TYPES, default='shoulder')
    start_date = models.DateField()
    end_date = models.DateField()
    rate_multiplier = models.DecimalField(max_digits=4, decimal_places=2, default=1.00)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return self.name


class RoomRateBase(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='room_rate_bases')
    room_type_name = models.CharField(max_length=200)
    base_rate = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='USD')
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['room_type_name', '-effective_from']

    def __str__(self):
        return self.room_type_name


class YieldRule(models.Model):
    RULE_TYPES = [
        ('occupancy', 'Occupancy'),
        ('advance_days', 'Advance Days'),
        ('day_of_week', 'Day of Week'),
    ]
    ADJUSTMENT_TYPES = [
        ('percent', 'Percent'),
        ('fixed', 'Fixed'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='yield_rules')
    name = models.CharField(max_length=200)
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES)
    threshold_value = models.DecimalField(max_digits=5, decimal_places=2)
    adjustment_type = models.CharField(max_length=10, choices=ADJUSTMENT_TYPES, default='percent')
    adjustment_value = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)

    class Meta:
        ordering = ['-priority', 'name']

    def __str__(self):
        return self.name


class RateRestriction(models.Model):
    RESTRICTION_TYPES = [
        ('min_stay', 'Minimum Stay'),
        ('max_stay', 'Maximum Stay'),
        ('closed_to_arrival', 'Closed to Arrival'),
        ('closed_to_departure', 'Closed to Departure'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='rate_restrictions')
    room_type_name = models.CharField(max_length=200)
    restriction_type = models.CharField(max_length=25, choices=RESTRICTION_TYPES)
    value = models.IntegerField(default=1)
    start_date = models.DateField()
    end_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['start_date', 'restriction_type']

    def __str__(self):
        return self.restriction_type


class SpecialOffer(models.Model):
    OFFER_TYPES = [
        ('early_bird', 'Early Bird'),
        ('last_minute', 'Last Minute'),
        ('package', 'Package'),
        ('promo', 'Promo'),
    ]
    DISCOUNT_TYPES = [
        ('percent', 'Percent'),
        ('fixed', 'Fixed'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='special_offers')
    name = models.CharField(max_length=200)
    offer_type = models.CharField(max_length=15, choices=OFFER_TYPES)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    valid_from = models.DateField()
    valid_to = models.DateField()
    promo_code = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-valid_from']

    def __str__(self):
        return self.name
