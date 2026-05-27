from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class Property(models.Model):
    PROPERTY_TYPES = [
        ('house', 'House / Villa'),
        ('apartment', 'Apartment / Flat'),
        ('condo', 'Condo / Townhouse'),
        ('commercial', 'Commercial'),
        ('office', 'Office Space'),
        ('land', 'Land / Plot'),
        ('industrial', 'Industrial'),
        ('other', 'Other'),
    ]
    STATUS = [
        ('active', 'Active Listing'),
        ('under_contract', 'Under Contract'),
        ('sold', 'Sold'),
        ('rented', 'Rented'),
        ('off_market', 'Off Market'),
        ('withdrawn', 'Withdrawn'),
    ]
    LISTING_TYPES = [
        ('sale', 'For Sale'),
        ('rent', 'For Rent'),
        ('both', 'Sale or Rent'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='properties')
    title = models.CharField(max_length=200)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='house')
    listing_type = models.CharField(max_length=10, choices=LISTING_TYPES, default='sale')
    status = models.CharField(max_length=20, choices=STATUS, default='active')

    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    region = models.CharField(max_length=100, blank=True, verbose_name='State / Province / Region')
    country = models.CharField(max_length=100, blank=True)

    bedrooms = models.PositiveIntegerField(null=True, blank=True)
    bathrooms = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    area_sqft = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='Area (sqft)')
    lot_size = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    price = models.DecimalField(max_digits=16, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    rent_per_month = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    mls_number = models.CharField(max_length=50, blank=True, verbose_name='MLS / Listing Number')
    listing_url = models.URLField(blank=True, verbose_name='IDX / MLS / Portal URL')
    virtual_tour_url = models.URLField(blank=True, verbose_name='Virtual Tour / 3D Tour URL')

    description = models.TextField(blank=True)
    features = models.TextField(blank=True, help_text='Key features, comma-separated (e.g. Pool, Garage, Garden)')

    listed_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='listed_properties')
    listing_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Properties'

    def __str__(self):
        return f"{self.title} — {self.address}"

    @property
    def feature_list(self):
        return [f.strip() for f in self.features.split(',') if f.strip()]


class PropertyShowing(models.Model):
    SHOWING_STATUS = [
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='showings')
    contact_name = models.CharField(max_length=150)
    contact_phone = models.CharField(max_length=30, blank=True)
    contact_email = models.EmailField(blank=True)
    scheduled_at = models.DateTimeField()
    agent = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='property_showings')
    status = models.CharField(max_length=12, choices=SHOWING_STATUS, default='scheduled')
    notes = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f"Showing: {self.property.title} — {self.contact_name}"
