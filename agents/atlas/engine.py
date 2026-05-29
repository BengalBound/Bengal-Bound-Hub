import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Atlas, BengalBound's AI Executive Assistant.

Your role is to keep executives organised, prepared, and ahead of their schedule. You think two steps ahead so the executive never has to scramble.

Capabilities:
- Generate sharp, concise meeting briefings from agendas and attendee context
- Extract action items from meeting notes, emails, and transcripts
- Prioritise tasks by urgency and strategic importance
- Draft executive summaries, follow-up emails, and status updates
- Prepare daily briefing documents with schedule + top priorities

Principles:
- Brevity over completeness — executives want the signal, not the noise
- Prioritise ruthlessly: urgent+important → important → urgent → other
- Always surface risks and blockers proactively
- Meeting briefs should answer: What is this meeting about? What decisions need to be made? What do I need to know beforehand?
- Action items must be specific: Who does What by When

Tone: Concise, professional, strategic. Like a Chief of Staff."""


class AtlasEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_briefing(self, meeting, instance=None) -> dict:
        prompt = f"""Generate an executive briefing for this upcoming meeting.

Meeting: {meeting.meeting_title}
Scheduled: {meeting.scheduled_at}
Attendees: {', '.join(meeting.attendees) if meeting.attendees else 'Not specified'}
Agenda: {meeting.agenda}

Return JSON with:
- "talking_points": list of 3-5 key talking points (strings)
- "ai_briefing": 2-3 paragraph executive brief (what to know, what to decide, what to watch out for)
- "pre_meeting_prep": list of things the executive should do before the meeting
- "risks": list of potential issues or blockers to flag"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"talking_points": [], "ai_briefing": raw, "pre_meeting_prep": [], "risks": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_briefing for {meeting.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if res.get("risks") and len(res.get("risks")) > 0:
                raise PermissionRequired(
                    context=f"Risks identified in meeting briefing: {', '.join(res.get('risks', []))}",
                    option_a="Acknowledge risks and prepare",
                    option_b="Reschedule meeting to address risks first"
                )
        return res

    def extract_tasks(self, text: str, source: str = "meeting", instance=None) -> list:
        prompt = f"""Extract all action items from this {source} text.

Text:
{text}

Return a JSON array of objects, each with:
- "title": specific action item (verb + what + measurable outcome)
- "priority": low/medium/high/urgent
- "suggested_due_days": integer (how many days from today)
- "owner_hint": who should own this (name or role if mentioned)"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = []

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="extract_tasks",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def prioritize_tasks(self, tasks: list, instance=None) -> str:
        task_list = "\n".join(f"- {t.get('title', str(t))} [{t.get('priority', 'medium')}]" for t in tasks[:20])
        prompt = f"""The executive has these open tasks. Prioritise and create an action plan.

Tasks:
{task_list}

Provide:
1. Top 3 tasks to tackle today
2. Tasks to delegate
3. Tasks to defer
4. Any tasks that can be dropped

Be specific and decisive."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="prioritize_tasks",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def morning_briefing(self, tasks: list, meetings: list, instance=None) -> str:
        task_summary = "\n".join(f"- {t.title} [{t.priority}] due {t.due_date}" for t in tasks[:10])
        meeting_summary = "\n".join(f"- {m.meeting_title} at {m.scheduled_at}" for m in meetings[:5])

        prompt = f"""Generate a crisp morning briefing for the executive.

Today's Meetings:
{meeting_summary or 'No meetings scheduled'}

Open Tasks (top 10):
{task_summary or 'No open tasks'}

Write a 3-paragraph morning briefing: (1) today's schedule, (2) top priorities to move, (3) any flags or risks."""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        res = agent_chat(messages)
        if instance:
            AgentLog.objects.create(
                instance=instance,
                action="morning_briefing",
                outcome='success',
                detail=res,
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
