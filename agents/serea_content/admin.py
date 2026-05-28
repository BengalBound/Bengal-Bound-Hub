from django.contrib import admin
from .models import ContentPiece, Campaign

@admin.register(ContentPiece)
class ContentPieceAdmin(admin.ModelAdmin):
    pass

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    pass

