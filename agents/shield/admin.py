from django.contrib import admin
from .models import ITTicket, KnowledgeArticle

@admin.register(ITTicket)
class ITTicketAdmin(admin.ModelAdmin):
    pass

@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    pass

