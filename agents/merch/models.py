from django.db import models


class Store(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="store_set")
    platform = models.CharField(
        max_length=15,
        choices=[
            ("shopify", "Shopify"),
            ("woocommerce", "WooCommerce"),
            ("daraz", "Daraz"),
            ("facebook", "Facebook"),
            ("custom", "Custom"),
        ],
    )
    store_name = models.CharField(max_length=300)
    store_url = models.URLField(blank=True)
    currency = models.CharField(max_length=10, default="BDT")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["store_name"]

    def __str__(self):
        return f"{self.store_name} [{self.platform}]"


class Product(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="product_set")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name="products")
    title = models.CharField(max_length=500)
    sku = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock_quantity = models.IntegerField(default=0)
    reorder_threshold = models.IntegerField(default=10)
    is_low_stock = models.BooleanField(default=False)
    ai_description = models.TextField(blank=True)
    ai_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    units_sold_30d = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
