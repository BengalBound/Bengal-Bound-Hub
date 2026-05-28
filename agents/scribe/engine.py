import json
import logging
from agents.utils import agent_chat

logger = logging.getLogger(__name__)

class ScribeEngine:
    def process_transcript(self, meeting) -> bool:
        """
        Uses Gemini to extract executive summary and action items from the raw meeting transcript.
        """
        if not meeting.raw_transcript:
            return False
            
        prompt = f"Analyze the following meeting transcript. Provide an executive summary, identify the overall sentiment, and extract all action items.\n\n"
        prompt += f"Transcript:\n{meeting.raw_transcript}\n\n"
        prompt += """Output ONLY valid JSON in this exact format:
{
  "executive_summary": "A 2-paragraph summary of the meeting.",
  "sentiment": "positive|neutral|negative",
  "action_items": [
    {"assignee_name": "Name", "task_description": "Task details"}
  ]
}"""

        messages = [
            {"role": "system", "content": "You are Scribe, an elite Executive Assistant and Meeting Notetaker. You are highly accurate and concise."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            raw = agent_chat(messages)
            data = json.loads(raw.strip())
            
            meeting.executive_summary = data.get("executive_summary", "")
            meeting.sentiment = data.get("sentiment", "neutral")
            meeting.status = "completed"
            meeting.save(update_fields=["executive_summary", "sentiment", "status"])
            
            # Create Action Items
            from .models import ActionItem
            items = data.get("action_items", [])
            for item in items:
                ActionItem.objects.create(
                    meeting=meeting,
                    assignee_name=item.get("assignee_name", "Unknown"),
                    task_description=item.get("task_description", "")
                )
            
            return True
        except Exception as e:
            logger.error("Failed to process meeting %s: %s", meeting.id, e)
            meeting.status = "failed"
            meeting.save(update_fields=["status"])
            return False
