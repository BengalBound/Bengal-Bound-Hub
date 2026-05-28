from django.db.models.signals import post_save
from django.dispatch import receiver
from workspace_admin.models import HiredAIEmployee
from agents.models import AgentInstance, AgentCatalog

@receiver(post_save, sender=HiredAIEmployee)
def provision_aria_instance(sender, instance, created, **kwargs):
    if not getattr(instance, 'agent_catalog', None) or instance.agent_catalog.slug != 'aria':
        return
    if instance.is_active:
        business = instance.employer.owned_businesses.first()
        if not business:
            return
            
        obj, is_new = AgentInstance.objects.get_or_create(
            business=business,  # tenant link
            catalog=instance.agent_catalog,
            defaults={'hired_employee': instance, 'status': 'idle'}
        )
        if not is_new and obj.status == 'offline':
            obj.status = 'idle'
            obj.save(update_fields=['status'])
    else:
        AgentInstance.objects.filter(hired_employee=instance).update(status='offline')
