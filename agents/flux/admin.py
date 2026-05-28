from django.contrib import admin
from .models import Supplier, PurchaseOrder

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    pass

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    pass

