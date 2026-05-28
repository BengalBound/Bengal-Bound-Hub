from django.db import models
from hub.models import BusinessInstance


class Property(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="property_set")
    title = models.CharField(max_length=500)
    property_type = models.CharField(
        max_length=15,
        choices=[
            ("apartment", "Apartment"),
            ("house", "House"),
            ("commercial", "Commercial"),
            ("land", "Land"),
            ("office", "Office"),
        ],
    )
    listing_type = models.CharField(
        max_length=5,
        choices=[("sale", "Sale"), ("rent", "Rent")],
    )
    price = models.DecimalField(max_digits=14, decimal_places=2)
    area_sqft = models.IntegerField()
    bedrooms = models.IntegerField(null=True, blank=True)
    location = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    ai_description = models.TextField(blank=True)
    status = models.CharField(
        max_length=12,
        choices=[
            ("available", "Available"),
            ("viewing", "Viewing"),
            ("under_offer", "Under Offer"),
            ("sold", "Sold"),
            ("rented", "Rented"),
        ],
        default="available",
    )
    listed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-listed_at"]

    def __str__(self):
        return self.title


class Lead(models.Model):
    business = models.ForeignKey("bredbound.BusinessInstance", on_delete=models.CASCADE, related_name="realt_lead_set")
    name = models.CharField(max_length=300)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    intent = models.CharField(max_length=5, choices=[("buy", "Buy"), ("rent", "Rent")])
    budget_max = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    preferred_areas = models.JSONField(default=list)
    bedrooms_needed = models.IntegerField(null=True, blank=True)
    ai_score = models.IntegerField(null=True, blank=True)
    ai_notes = models.TextField(blank=True)
    status = models.CharField(
        max_length=15,
        choices=[
            ("new", "New"),
            ("qualified", "Qualified"),
            ("viewing_booked", "Viewing Booked"),
            ("offer_made", "Offer Made"),
            ("converted", "Converted"),
            ("rejected", "Rejected"),
        ],
        default="new",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} [{self.intent}]"
