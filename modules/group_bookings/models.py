from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class GroupRFP(models.Model):
    EVENT_TYPE_CHOICES = [
        ('conference', 'Conference'),
        ('wedding', 'Wedding'),
        ('corporate', 'Corporate'),
        ('leisure', 'Leisure'),
        ('sports', 'Sports'),
        ('other', 'Other'),
    ]
    STATUS_CHOICES = [
        ('inquiry', 'Inquiry'),
        ('quoted', 'Quoted'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('declined', 'Declined'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='group_rfps')
    rfp_number = models.CharField(max_length=20, blank=True)
    group_name = models.CharField(max_length=200)
    contact_name = models.CharField(max_length=150)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30, blank=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='conference')
    arrival_date = models.DateField()
    departure_date = models.DateField()
    rooms_required = models.IntegerField()
    adults = models.IntegerField()
    children = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inquiry')
    special_requirements = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_to = models.ForeignKey(
        BusinessEmployee, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_rfps'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.rfp_number

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.rfp_number:
            self.rfp_number = f'GRP-{self.pk:05d}'
            GroupRFP.objects.filter(pk=self.pk).update(rfp_number=self.rfp_number)

    @property
    def nights(self):
        return (self.departure_date - self.arrival_date).days


class GroupBlock(models.Model):
    rfp = models.ForeignKey(GroupRFP, on_delete=models.CASCADE, related_name='blocks')
    room_type_name = models.CharField(max_length=150)
    rooms_blocked = models.IntegerField()
    rate_per_night = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='USD')
    release_date = models.DateField(null=True, blank=True)
    is_confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ['room_type_name']

    def __str__(self):
        return self.room_type_name


class RoomingListEntry(models.Model):
    rfp = models.ForeignKey(GroupRFP, on_delete=models.CASCADE, related_name='rooming_list')
    guest_name = models.CharField(max_length=200)
    room_type_name = models.CharField(max_length=150, blank=True)
    check_in = models.DateField()
    check_out = models.DateField()
    special_requests = models.TextField(blank=True)
    is_assigned = models.BooleanField(default=False)
    room_number = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['guest_name']

    def __str__(self):
        return self.guest_name


class GroupContract(models.Model):
    rfp = models.OneToOneField(GroupRFP, on_delete=models.CASCADE, related_name='contract')
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    deposit_due_date = models.DateField(null=True, blank=True)
    deposit_paid = models.BooleanField(default=False)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='USD')
    cancellation_policy = models.TextField(blank=True)
    attrition_pct = models.IntegerField(default=20)
    signed = models.BooleanField(default=False)
    signed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return str(self.rfp)
