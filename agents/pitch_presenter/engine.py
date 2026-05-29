import logging
from agents.utils import agent_chat

logger = logging.getLogger(__name__)

class PitchPresenterEngine:
    SYSTEM_PROMPT = "You are Sylvia, BengalBound's AI Video Pitch Presenter. You write high-converting spoken pitch scripts tailored to specific audiences (investors, enterprise buyers, partners) and orchestrate HeyGen/D-ID video rendering."

    def generate_script(self, pitch_obj) -> str:
        """
        Uses Gemini to generate a high-converting spoken pitch script based on the business summary and slide talking points.
        """
        prompt = "Write a professional, spoken video pitch for the following business context:\n\n"
        prompt += f"Context: {pitch_obj.business_summary}\n"
        prompt += f"Target Audience: {pitch_obj.target_audience}\n\n"

        slides = pitch_obj.slides.all()
        if slides.exists():
            prompt += "The video will feature the following slides. Please write the script linearly, transitioning smoothly between slides:\n"
            for slide in slides:
                prompt += f"- Slide {slide.slide_number}: Cover these points: {slide.talking_points}\n"

        prompt += "\nOutput ONLY the spoken script. Do not include stage directions or formatting, just the raw words the avatar will speak."

        messages = [
            {"role": "system", "content": "You are Sylvia, an elite Executive Presentation AI. Write compelling, confident, and highly persuasive spoken video scripts."},
            {"role": "user", "content": prompt}
        ]

        try:
            script = agent_chat(messages)
            pitch_obj.ai_script = script
            pitch_obj.status = "rendering_video"
            pitch_obj.save(update_fields=["ai_script", "status"])
            return script
        except Exception as e:
            logger.error("Failed to generate pitch script: %s", e)
            pitch_obj.status = "failed"
            pitch_obj.save(update_fields=["status"])
            raise
