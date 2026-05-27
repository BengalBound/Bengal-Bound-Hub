from django.db import models
from accounts.models import User


class HubSheet(models.Model):
    business = models.ForeignKey('bredbound.BusinessInstance', on_delete=models.CASCADE, related_name='hub_sheets')
    title = models.CharField(max_length=300, default='Untitled Spreadsheet')
    data = models.JSONField(default=list, help_text="2D array: [[col_headers...],[row1...],...]")
    column_widths = models.JSONField(default=list, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_sheets')
    last_edited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='edited_sheets')
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title
