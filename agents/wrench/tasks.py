import logging
from celery import shared_task
from django.utils import timezone
from workspace_admin.models import HiredAIEmployee
from .engine import WrenchEngine, PermissionRequired

logger = logging.getLogger(__name__)

@shared_task
def wrench_daily_dispatch_review(instance_id: int):
    """
    Runs daily to review upcoming jobs and ensure techs and parts are assigned.
    """
    try:
        instance = HiredAIEmployee.objects.select_related('business').get(pk=instance_id, is_active=True)
    except HiredAIEmployee.DoesNotExist:
        return
        
    engine = WrenchEngine()
    
    # In a real scenario, this would fetch jobs from the `pos` or `crm` modules
    # and call engine.dispatch_technician
    
    # Example minimal execution
    logger.info(f"Wrench {instance_id} running daily dispatch review...")
    
    # Simulate a dummy classification
    dummy_job = engine.classify_job("Kitchen sink is leaking rapidly, water everywhere", instance)
    
    if dummy_job.get('urgency') == 'emergency':
        try:
            # Simulate a dispatch that triggers a permission request
            engine.dispatch_technician(dummy_job, [{"id": "tech_1", "name": "Mario"}], instance)
        except PermissionRequired as e:
            from agents.models import AgentPermissionRequest
            AgentPermissionRequest.objects.create(
                instance=instance,
                context_summary=e.context,
                option_a=e.option_a,
                option_b=e.option_b
            )
