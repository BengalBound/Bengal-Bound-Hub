from django.contrib import admin
from .models import DocumentationProject, DocPage

@admin.register(DocumentationProject)
class DocumentationProjectAdmin(admin.ModelAdmin):
    pass

@admin.register(DocPage)
class DocPageAdmin(admin.ModelAdmin):
    pass

