import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

@csrf_exempt
def recall_webhook(request):
    """
    Webhook receiver for Recall.ai bot events.
    Called when a meeting ends and the transcript is ready.
    """
    if request.method != "POST":
        return HttpResponse(status=405)

    try:
        data = json.loads(request.body)
        event_type = data.get("event")
        bot_id = data.get("data", {}).get("bot_id")

        if event_type == "bot.transcript_ready":
            transcript = data.get("data", {}).get("transcript", "")

            from .models import Meeting
            meeting = Meeting.objects.filter(bot_id=bot_id).first()

            if meeting:
                meeting.raw_transcript = transcript
                meeting.save(update_fields=["raw_transcript"])

                # Trigger background processing
                from .tasks import process_meeting_notes
                process_meeting_notes.delay(str(meeting.id))

        return HttpResponse("OK")
    except Exception as e:
        logger.error("Recall.ai webhook error: %s", e)
        return HttpResponse(status=400)
