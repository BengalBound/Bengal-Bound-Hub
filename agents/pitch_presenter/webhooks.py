def handle_event(event_type: str, payload: dict, instance):
    """Route inbound webhook payload — HeyGen/D-ID rendering complete callback."""
    from agents.pitch_presenter.models import VideoPitch

    if event_type == 'webhook_event':
        pitch_id = payload.get('pitch_id') or payload.get('video_id')
        video_url = payload.get('video_url', '')
        status = payload.get('status', 'completed')

        if pitch_id:
            try:
                pitch = VideoPitch.objects.get(id=pitch_id, organization=instance.business)
                pitch.video_url = video_url
                pitch.status = status
                pitch.save(update_fields=['video_url', 'status'])
            except VideoPitch.DoesNotExist:
                pass
