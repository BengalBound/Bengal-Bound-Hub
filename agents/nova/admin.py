from django.contrib import admin
from .models import DataSource, DataQuery

@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    pass

@admin.register(DataQuery)
class DataQueryAdmin(admin.ModelAdmin):
    pass

