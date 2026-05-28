from django.contrib import admin
from .models import Competitor, CompetitorChange

@admin.register(Competitor)
class CompetitorAdmin(admin.ModelAdmin):
    pass

@admin.register(CompetitorChange)
class CompetitorChangeAdmin(admin.ModelAdmin):
    pass

