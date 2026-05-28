from django.contrib import admin
from .models import LegalDocument, Clause

@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    pass

@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    pass

