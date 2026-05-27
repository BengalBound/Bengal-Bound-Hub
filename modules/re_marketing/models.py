from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class ListingFlyer(models.Model):
    TEMPLATES = [
        ('standard', 'Standard'),
        ('luxury', 'Luxury'),
        ('minimal', 'Minimal'),
        ('open_house', 'Open House'),
        ('just_sold', 'Just Sold'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='listing_flyers')
    property_address = models.CharField(max_length=300)
    template = models.CharField(max_length=15, choices=TEMPLATES, default='standard')
    headline = models.CharField(max_length=200, blank=True, help_text='e.g. "Just Listed!", "Stunning Family Home"')
    tagline = models.CharField(max_length=300, blank=True, help_text='Short selling statement')
    bedrooms = models.PositiveIntegerField(null=True, blank=True)
    bathrooms = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    price = models.CharField(max_length=50, blank=True)
    open_house_date = models.CharField(max_length=100, blank=True, help_text='e.g. Sunday 2pm – 4pm')
    agent_name = models.CharField(max_length=150, blank=True)
    agent_phone = models.CharField(max_length=30, blank=True)
    agent_email = models.EmailField(blank=True)
    property_url = models.URLField(blank=True)
    virtual_tour_url = models.URLField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_flyers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_template_display()} Flyer — {self.property_address}"


class DripCampaign(models.Model):
    AUDIENCE = [
        ('buyers', 'Buyers'),
        ('sellers', 'Sellers'),
        ('renters', 'Renters'),
        ('investors', 'Investors'),
        ('past_clients', 'Past Clients'),
        ('all', 'All Contacts'),
    ]
    STATUS = [('draft', 'Draft'), ('active', 'Active'), ('paused', 'Paused'), ('ended', 'Ended')]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='drip_campaigns')
    name = models.CharField(max_length=150)
    target_audience = models.CharField(max_length=15, choices=AUDIENCE, default='all')
    status = models.CharField(max_length=8, choices=STATUS, default='draft')
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_campaigns')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def message_count(self):
        return self.messages.count()

    def __str__(self):
        return self.name


class DripMessage(models.Model):
    MSG_TYPES = [('email', 'Email'), ('sms', 'SMS / Text')]

    campaign = models.ForeignKey(DripCampaign, on_delete=models.CASCADE, related_name='messages')
    subject = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    delay_days = models.PositiveIntegerField(default=0, help_text='Days after enrolment to send')
    message_type = models.CharField(max_length=6, choices=MSG_TYPES, default='email')

    class Meta:
        ordering = ['delay_days']


class SocialPost(models.Model):
    POST_TYPES = [
        ('just_listed', 'Just Listed'),
        ('just_sold', 'Just Sold'),
        ('open_house', 'Open House'),
        ('price_drop', 'Price Reduction'),
        ('under_contract', 'Under Contract'),
        ('market_update', 'Market Update'),
        ('custom', 'Custom'),
    ]
    PLATFORMS = [('facebook', 'Facebook'), ('instagram', 'Instagram'), ('both', 'Facebook & Instagram'), ('linkedin', 'LinkedIn')]
    POST_STATUS = [('draft', 'Draft'), ('scheduled', 'Scheduled'), ('posted', 'Posted')]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='social_posts')
    post_type = models.CharField(max_length=20, choices=POST_TYPES, default='just_listed')
    property_address = models.CharField(max_length=300, blank=True)
    caption = models.TextField()
    platform = models.CharField(max_length=12, choices=PLATFORMS, default='both')
    status = models.CharField(max_length=10, choices=POST_STATUS, default='draft')
    scheduled_for = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='social_posts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_post_type_display()} — {self.property_address or 'General'}"
