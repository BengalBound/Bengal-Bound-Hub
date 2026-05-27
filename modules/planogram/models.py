from django.db import models
from hub.models import BusinessInstance, BusinessEmployee


class StoreLayout(models.Model):
    business = models.ForeignKey(BusinessInstance, on_delete=models.CASCADE, related_name='store_layouts')
    name = models.CharField(max_length=100)
    store_location = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(BusinessEmployee, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_layouts')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    @property
    def section_count(self):
        return self.sections.count()

    @property
    def slot_count(self):
        return PlanogramSlot.objects.filter(section__layout=self).count()

    def __str__(self):
        return self.name


class PlanogramSection(models.Model):
    layout = models.ForeignKey(StoreLayout, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=100)
    display_order = models.PositiveIntegerField(default=0)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.layout.name} — {self.name}"


class PlanogramSlot(models.Model):
    section = models.ForeignKey(PlanogramSection, on_delete=models.CASCADE, related_name='slots')
    product_name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, blank=True)
    shelf_number = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=20, blank=True, help_text='e.g. Left, Centre, Right or slot number')
    facings = models.PositiveIntegerField(default=1)
    min_stock = models.IntegerField(null=True, blank=True)
    current_stock = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['shelf_number', 'position']

    @property
    def needs_reorder(self):
        if self.min_stock is not None and self.current_stock is not None:
            return self.current_stock <= self.min_stock
        return False

    def __str__(self):
        return f"{self.product_name} — {self.section}"
