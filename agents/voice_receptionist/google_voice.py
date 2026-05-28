"""
voice_receptionist/google_voice.py
------------------------------------
Google Cloud Text-to-Speech and Speech-to-Text wrappers.
- TTS responses are cached in diskcache to avoid re-generating identical phrases.
- STT uses synchronous recognition (Twilio sends 8kHz MULAW audio chunks).
"""

import hashlib
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cache setup (diskcache — no Redis needed)
# ---------------------------------------------------------------------------

_tts_cache = None


def _get_tts_cache():
    global _tts_cache
    if _tts_cache is None:
        import diskcache
        from pathlib import Path
        cache_dir = Path(settings.BASE_DIR) / "cache" / "tts"
        _tts_cache = diskcache.Cache(str(cache_dir), size_limit=512 * 1024 * 1024)  # 512 MB
    return _tts_cache


# ---------------------------------------------------------------------------
# Text-to-Speech
# ---------------------------------------------------------------------------

def synthesize_speech(
    text: str,
    voice_name: str = "en-US-Neural2-F",
    language_code: str = "en-US",
    speaking_rate: float = 1.0,
) -> bytes:
    """
    Convert text to MP3 audio bytes using Google Cloud TTS Neural2 voices.
    Results are cached by (text + voice_name) hash to minimize API calls.

    Returns:
        MP3 audio bytes suitable for serving via Twilio <Play> verb.
    """
    cache_key = f"tts:{hashlib.sha256(f'{text}{voice_name}'.encode()).hexdigest()}"
    cache = _get_tts_cache()

    cached = cache.get(cache_key)
    if cached:
        logger.debug("TTS cache hit for voice=%s", voice_name)
        return cached

    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=speaking_rate,
        pitch=0.0,
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config,
    )

    audio_bytes = response.audio_content
    cache.set(cache_key, audio_bytes, expire=86400 * 7)  # Cache for 7 days
    logger.info("TTS synthesized %d chars using voice %s", len(text), voice_name)
    return audio_bytes


# ---------------------------------------------------------------------------
# Speech-to-Text
# ---------------------------------------------------------------------------

def transcribe_audio(
    audio_bytes: bytes,
    sample_rate_hertz: int = 8000,
    language_code: str = "en-US",
    encoding: str = "MULAW",
) -> str:
    """
    Transcribe audio bytes using Google Cloud Speech-to-Text v2.
    Twilio sends MULAW-encoded audio at 8kHz by default.

    Returns:
        Transcription string, or empty string on failure.
    """
    from google.cloud import speech

    client = speech.SpeechClient()

    # Map string encoding to enum
    enc_map = {
        "MULAW":   speech.RecognitionConfig.AudioEncoding.MULAW,
        "LINEAR16": speech.RecognitionConfig.AudioEncoding.LINEAR16,
        "FLAC":    speech.RecognitionConfig.AudioEncoding.FLAC,
    }
    audio_encoding = enc_map.get(encoding.upper(), speech.RecognitionConfig.AudioEncoding.MULAW)

    config = speech.RecognitionConfig(
        encoding=audio_encoding,
        sample_rate_hertz=sample_rate_hertz,
        language_code=language_code,
        enable_automatic_punctuation=True,
        model="phone_call",
        use_enhanced=True,  # Enhanced phone model
    )
    audio = speech.RecognitionAudio(content=audio_bytes)

    try:
        response = client.recognize(config=config, audio=audio)
        if response.results:
            transcript = response.results[0].alternatives[0].transcript
            logger.info("STT transcript (%d chars): %s", len(transcript), transcript[:80])
            return transcript.strip()
        return ""
    except Exception as e:
        logger.error("STT error: %s", e)
        return ""


# ---------------------------------------------------------------------------
# Available Voice Options
# ---------------------------------------------------------------------------

AVAILABLE_VOICES = [
    {"id": "en-US-Neural2-F", "label": "Aria (US Female)",     "language": "en-US", "gender": "FEMALE"},
    {"id": "en-US-Neural2-D", "label": "Ryan (US Male)",       "language": "en-US", "gender": "MALE"},
    {"id": "en-US-Neural2-A", "label": "Alex (US Male Alt)",   "language": "en-US", "gender": "MALE"},
    {"id": "en-US-Neural2-C", "label": "Sophie (US Female Alt)","language": "en-US", "gender": "FEMALE"},
    {"id": "en-GB-Neural2-B", "label": "Oliver (UK Male)",     "language": "en-GB", "gender": "MALE"},
    {"id": "en-GB-Neural2-A", "label": "Emma (UK Female)",     "language": "en-GB", "gender": "FEMALE"},
]
