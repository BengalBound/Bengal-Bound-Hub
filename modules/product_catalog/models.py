import secrets
from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class ProductCatalog(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='product_catalogs')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    share_token = models.CharField(max_length=64, blank=True)
    created_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_catalogs')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def generate_share_token(self):
        self.share_token = secrets.token_urlsafe(32)
        self.is_public = True
        self.save(update_fields=['share_token', 'is_public'])

    @property
    def item_count(self):
        return self.items.count()

    def __str__(self):
        return self.title


class CatalogCategory(models.Model):
    catalog = models.ForeignKey(ProductCatalog, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.catalog.title} — {self.name}"


class CatalogItem(models.Model):
    catalog = models.ForeignKey(ProductCatalog, on_delete=models.CASCADE, related_name='items')
    category = models.ForeignKey(CatalogCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=5, default='USD')
    unit = models.CharField(max_length=30, blank=True, help_text='e.g. per kg, per box, each')
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    in_stock = models.BooleanField(default=True)

    class Meta:
        ordering = ['-is_featured', 'display_order', 'name']

    def __str__(self):
        return self.name
