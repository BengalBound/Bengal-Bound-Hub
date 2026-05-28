from django.contrib import admin
from .models import Vendor, RFQ

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    pass

@admin.register(RFQ)
class RFQAdmin(admin.ModelAdmin):
    pass

