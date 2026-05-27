from django.contrib import admin
from .models import Channel, ChannelMember, Message, MessageReaction, DirectMessage


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'channel_type', 'is_archived', 'created_at']
    list_filter = ['channel_type', 'is_archived']
    search_fields = ['name', 'business__name']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['author', 'channel', 'content', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'is_edited']
    search_fields = ['content', 'author__email']


admin.site.register(ChannelMember)
admin.site.register(MessageReaction)
admin.site.register(DirectMessage)
