def handle_event(event_type: str, payload: dict, instance):
    """Route inbound webhook — HeyGen/D-ID session state callbacks."""
    from agents.video_concierge.models import VideoSession

    if event_type == 'webhook_event':
        session_id = payload.get('session_id', '')
        resolution = payload.get('resolution_status', 'resolved')
        transcript = payload.get('transcript', '')
        duration = payload.get('duration_seconds', 0)

        if session_id:
            try:
                session = VideoSession.objects.get(session_id=session_id, organization=instance.business)
                session.resolution_status = resolution
                session.transcript = transcript
                session.duration_seconds = duration
                session.save(update_fields=['resolution_status', 'transcript', 'duration_seconds'])
            except VideoSession.DoesNotExist:
                pass
