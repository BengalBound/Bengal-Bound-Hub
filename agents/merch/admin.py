from django.contrib import admin
from .models import Store, Product

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    pass

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    pass

