import logging
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task(name="agents.scribe.process_meeting_notes")
def process_meeting_notes(meeting_id: str):
    """
    Background task triggered when Recall.ai webhook delivers the transcript.
    """
    from agents.scribe.models import Meeting
    from agents.scribe.engine import ScribeEngine
    
    try:
        meeting = Meeting.objects.get(id=meeting_id)
        meeting.status = "processing"
        meeting.save(update_fields=["status"])
        
        engine = ScribeEngine()
        engine.process_transcript(meeting)
        
    except Exception as e:
        logger.error("Error processing meeting notes %s: %s", meeting_id, e)
