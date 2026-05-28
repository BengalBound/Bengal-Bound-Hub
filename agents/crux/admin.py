from django.contrib import admin
from .models import Contact, Interaction

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    pass

@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    pass

