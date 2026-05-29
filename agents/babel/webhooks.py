from agents.babel.engine import BabelEngine
from agents.babel.models import TranslationJob
from agents.models import AgentInstance

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Babel."""
    engine = BabelEngine()

    if event_type == 'translation_requested':
        job = TranslationJob.objects.create(
            business=instance.business,
            source_language=payload.get('source_language', 'en'),
            target_languages=payload.get('target_languages', []),
            source_text=payload.get('source_text', ''),
            status='queued'
        )

        # We can let the background task handle it, or attempt immediate translation
        # Letting tasks.py pick it up might be better to avoid blocking webhook if long text.
