from django.contrib import admin
from .models import ForumCategory, ForumTopic, ForumPost

@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(ForumTopic)
class ForumTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'creator', 'is_pinned', 'is_locked', 'created_at')
    list_filter = ('category', 'is_pinned', 'is_locked')
    search_fields = ('title', 'creator__email')

@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('topic', 'author', 'created_at')
    search_fields = ('topic__title', 'author__email', 'content')
