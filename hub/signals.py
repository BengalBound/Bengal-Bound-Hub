"""
Storage quota enforcement.

Pre-save signal fires before any model save. When a FileField or ImageField
is about to receive a new file, we estimate the size and raise ValidationError
if it would push the business over its storage limit.
"""
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import BusinessInstance


@receiver(pre_save, sender=BusinessInstance)
def enforce_logo_quota(sender, instance, **kwargs):
    """Block logo uploads that would exceed the business storage quota."""
    if not instance.logo:
        return
    # Only check when a new file object is being assigned (not an existing path string)
    if not hasattr(instance.logo, 'file'):
        return
    try:
        file_size_mb = instance.logo.size / (1024 * 1024)
    except (AttributeError, ValueError):
        return

    # Load previous storage_used_mb from the DB (avoids using the in-memory value)
    try:
        existing = BusinessInstance.objects.get(pk=instance.pk)
        current_used = existing.storage_used_mb
    except BusinessInstance.DoesNotExist:
        current_used = 0.0

    if current_used + file_size_mb > instance.storage_limit_mb:
        raise ValidationError(
            f"Storage quota exceeded. "
            f"Used: {current_used:.1f} MB / {instance.storage_limit_mb:.0f} MB. "
            f"This file is {file_size_mb:.1f} MB. "
            "Request a storage increase or upgrade your plan."
        )

    # Update tracked usage
    instance.storage_used_mb = current_used + file_size_mb
