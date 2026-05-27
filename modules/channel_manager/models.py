from django.db import models
from hub.models import BusinessInstance


class Channel(models.Model):
    CHANNEL_TYPES = [
        ('ota', 'OTA'),
        ('gds', 'GDS'),
        ('direct', 'Direct'),
        ('wholesaler', 'Wholesaler'),
        ('metasearch', 'Metasearch'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='channels')
    name = models.CharField(max_length=200)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES, default='ota')
    is_active = models.BooleanField(default=True)
    api_endpoint = models.CharField(max_length=500, blank=True)
    api_key = models.CharField(max_length=500, blank=True)
    commission_pct = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class RatePlan(models.Model):
    MEAL_PLANS = [
        ('ro', 'Room Only'),
        ('bb', 'Bed & Breakfast'),
        ('hb', 'Half Board'),
        ('fb', 'Full Board'),
        ('ai', 'All Inclusive'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='rate_plans')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    meal_plan = models.CharField(max_length=5, choices=MEAL_PLANS, default='ro')
    is_refundable = models.BooleanField(default=True)
    min_stay = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ChannelRate(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='channel_rates')
    rate_plan = models.ForeignKey(RatePlan, on_delete=models.CASCADE, related_name='channel_rates')
    room_type_name = models.CharField(max_length=200)
    rate_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=5, default='USD')
    valid_from = models.DateField()
    valid_to = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-valid_from']

    def __str__(self):
        return f"{self.room_type_name} — {self.channel.name} — {self.rate_plan.name}"


class AvailabilityBlock(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='availability_blocks')
    room_type_name = models.CharField(max_length=200)
    date = models.DateField()
    available_rooms = models.IntegerField(default=0)
    sold_rooms = models.IntegerField(default=0)

    class Meta:
        ordering = ['date', 'room_type_name']
        unique_together = [['business', 'room_type_name', 'date']]

    def __str__(self):
        return f"{self.room_type_name} — {self.date}"

    @property
    def occupancy_pct(self):
        total = self.available_rooms + self.sold_rooms
        if total == 0:
            return 0
        return round((self.sold_rooms / total) * 100, 1)


class ChannelSyncLog(models.Model):
    SYNC_TYPES = [
        ('rates', 'Rates'),
        ('availability', 'Availability'),
        ('reservations', 'Reservations'),
        ('full', 'Full Sync'),
    ]
    SYNC_STATUS = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='channel_sync_logs')
    channel = models.ForeignKey(Channel, on_delete=models.SET_NULL, null=True, blank=True, related_name='channel_sync_log_entries')
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES, default='full')
    status = models.CharField(max_length=10, choices=SYNC_STATUS, default='success')
    message = models.TextField(blank=True)
    synced_at = models.DateTimeField(auto_now_add=True)
    records_synced = models.IntegerField(default=0)

    class Meta:
        ordering = ['-synced_at']

    def __str__(self):
        return f"{self.get_sync_type_display()} — {self.get_status_display()} — {self.synced_at}"
