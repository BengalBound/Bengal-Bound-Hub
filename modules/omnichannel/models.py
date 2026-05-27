from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class SalesChannel(models.Model):
    CHANNEL_TYPES = [
        ('pos', 'Physical POS / Store'),
        ('website', 'Own Website / E-Commerce'),
        ('shopify', 'Shopify'),
        ('woocommerce', 'WooCommerce'),
        ('amazon', 'Amazon'),
        ('ebay', 'eBay'),
        ('tiktok', 'TikTok Shop'),
        ('instagram', 'Instagram Shop'),
        ('facebook', 'Facebook Marketplace'),
        ('b2b', 'B2B Portal'),
        ('other', 'Other'),
    ]

    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='sales_channels')
    name = models.CharField(max_length=100)
    channel_type = models.CharField(max_length=20, choices=CHANNEL_TYPES, default='other')
    url = models.URLField(blank=True)
    api_key = models.CharField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ['business', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_channel_type_display()})"


class ChannelListing(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='channel_listings')
    channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE, related_name='listings')
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True, verbose_name='Internal SKU')
    channel_sku = models.CharField(max_length=100, blank=True, verbose_name='Channel SKU')
    listed_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock_qty = models.IntegerField(default=0)
    is_synced = models.BooleanField(default=False)
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['product_name']

    def __str__(self):
        return f"{self.product_name} — {self.channel.name}"


class ChannelSyncLog(models.Model):
    STATUS = [('success', 'Success'), ('partial', 'Partial'), ('failed', 'Failed')]

    channel = models.ForeignKey(SalesChannel, on_delete=models.CASCADE, related_name='sync_logs')
    synced_at = models.DateTimeField(auto_now_add=True)
    items_synced = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS, default='success')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-synced_at']
