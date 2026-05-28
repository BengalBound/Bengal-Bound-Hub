from django.db import models
from hub.models import BusinessInstance


class Supplier(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="supplier_set")
    name = models.CharField(max_length=300)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=30, blank=True)
    country = models.CharField(max_length=100, blank=True)
    on_time_rate = models.FloatField(null=True, blank=True)
    avg_lead_days = models.IntegerField(null=True, blank=True)
    rating = models.CharField(
        max_length=10,
        choices=[("excellent", "Excellent"), ("good", "Good"), ("average", "Average"), ("poor", "Poor")],
        blank=True,
    )
    ai_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="purchaseorder_set")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="purchase_orders")
    po_number = models.CharField(max_length=100)
    expected_date = models.DateField()
    total_value = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=10,
        choices=[
            ("draft", "Draft"),
            ("sent", "Sent"),
            ("confirmed", "Confirmed"),
            ("shipped", "Shipped"),
            ("received", "Received"),
            ("overdue", "Overdue"),
        ],
        default="draft",
    )
    items = models.JSONField(default=list)
    ai_recommendation = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"PO {self.po_number} — {self.supplier.name}"
