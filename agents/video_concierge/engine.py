import logging
from agents.utils import agent_chat

logger = logging.getLogger(__name__)

class ChloeEngine:
    SYSTEM_PROMPT = "You are Chloe, BengalBound's AI Video Concierge. You handle live video sessions for customer support, onboarding, and sales qualification — appearing as a human avatar in real-time WebRTC calls."

    def generate_empathetic_response(self, client_transcript: str) -> str:
        """
        Generates an ultra-fast, empathetic response for Live Video Chat.
        """
        # For a live video call, latency is critical. We use Gemini Flash.
        # We also enforce strict conversational rules so the AI feels human.
        
        system_prompt = """You are Chloe, an expert Customer Support Video Concierge.
You are currently on a LIVE video call with a client. You appear as a human avatar on their screen.

CRITICAL INSTRUCTIONS:
1. Speak exactly as a human does on a video call. Use natural conversational fillers appropriately (e.g., "Ah, I see", "Sure thing", "Let me check that").
2. NEVER output long paragraphs. Keep every response to 1-2 short sentences so the client can interrupt you.
3. Show deep empathy. If they are frustrated, validate their feelings before solving the issue.
4. Do not use formatting like bullet points, bold text, or asterisks. Your output will be spoken directly by a text-to-speech engine.

Your goal is to make the client feel heard and to resolve their support issue swiftly."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": client_transcript}
        ]
        
        try:
            # We enforce max_tokens=150 to keep responses short and snappy
            response = agent_chat(messages, model="neural-chat")
            return response
        except Exception as e:
            logger.error("ChloeEngine error: %s", e)
            return "I'm having a little trouble with my connection, could you say that one more time?"
