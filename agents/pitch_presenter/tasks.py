import logging
from celery import shared_task

logger = logging.getLogger(__name__)

@shared_task(name="agents.pitch_presenter.generate_video_pitch")
def generate_video_pitch(pitch_id: str):
    """
    Background pipeline to generate the script via Gemini, then dispatch to the HeyGen/D-ID API for rendering.
    """
    from agents.pitch_presenter.models import VideoPitch
    from agents.pitch_presenter.engine import PitchPresenterEngine

    try:
        pitch = VideoPitch.objects.get(id=pitch_id)
        pitch.status = "generating_script"
        pitch.save(update_fields=["status"])

        # 1. Generate Script
        engine = PitchPresenterEngine()
        script = engine.generate_script(pitch)

        # 2. Trigger HeyGen API (Stubbed for now)
        logger.info("Pitch %s script generated. Ready to trigger Video API rendering.", pitch_id)

        # TODO: Implement REST API call to HeyGen to submit the task.
        # webhook_url = settings.BACKEND_URL + f"/api/v1/pitch/webhook/heygen/"
        # requests.post("https://api.heygen.com/v1/video.generate", ...)

    except Exception as e:
        logger.error("Error generating video pitch %s: %s", pitch_id, e)
