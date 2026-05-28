from django.contrib import admin
from .models import Employee, PayrollRun

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    pass

@admin.register(PayrollRun)
class PayrollRunAdmin(admin.ModelAdmin):
    pass

