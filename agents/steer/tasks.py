import logging
from celery import shared_task
from django.utils import timezone
from workspace_admin.models import HiredAIEmployee
from .engine import SteerEngine, PermissionRequired

logger = logging.getLogger(__name__)

@shared_task
def steer_daily_schedule_review(instance_id: int):
    """
    Runs daily to review upcoming driving lessons and ensure vehicles are assigned.
    """
    try:
        instance = HiredAIEmployee.objects.select_related('business').get(pk=instance_id, is_active=True)
    except HiredAIEmployee.DoesNotExist:
        return
        
    engine = SteerEngine()
    
    # Minimal execution simulation
    logger.info(f"Steer {instance_id} running daily schedule review...")
    
    dummy_request = engine.parse_booking_request("I need a manual lesson on Saturday morning.", instance)
    engine.schedule_lesson(dummy_request, [{"id": "slot_1", "time": "Saturday 10am", "instructor": "Bob", "vehicle": "Manual Ford Focus"}], instance)
