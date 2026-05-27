from django.contrib import admin
from .models import Board, BoardList, Card, Label, CardLabel, Checklist, ChecklistItem, CardComment, CardActivity


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ['name', 'business', 'color', 'is_archived', 'created_at']
    list_filter = ['is_archived', 'color']
    search_fields = ['name', 'business__name']


@admin.register(BoardList)
class BoardListAdmin(admin.ModelAdmin):
    list_display = ['name', 'board', 'position', 'task_limit', 'is_archived']
    list_filter = ['is_archived']


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['title', 'board_list', 'color', 'due_date', 'is_archived', 'created_at']
    list_filter = ['is_archived', 'color']
    search_fields = ['title']
    filter_horizontal = ['assignees']


admin.site.register(Label)
admin.site.register(CardLabel)
admin.site.register(Checklist)
admin.site.register(ChecklistItem)
admin.site.register(CardComment)
admin.site.register(CardActivity)
