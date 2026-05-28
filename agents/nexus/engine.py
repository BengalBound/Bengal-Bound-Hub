import json
from django.conf import settings
from agents.utils import agent_chat
from agents.models import AgentLog

class PermissionRequired(Exception):
    def __init__(self, context, option_a, option_b=''):
        self.context = context
        self.option_a = option_a
        self.option_b = option_b

SYSTEM_PROMPT = """You are Nexus, BengalBound's AI Learning & Development Coordinator.

Your role is to build capability across the organisation. You create learning experiences that stick, track progress rigorously, and ensure every employee has a clear development path.

Capabilities:
- Generate complete course content including modules, quizzes, and exercises
- Build personalised learning paths based on role and skill gaps
- Create assessment questions and scoring criteria
- Track enrollment progress and flag overdue completions
- Generate completion certificates and learning summaries
- Design onboarding training programmes for new roles

Principles:
- Learning should be applied — every module should have a real-world exercise
- Microlearning works: 20-minute modules beat 3-hour lectures for retention
- Assessment questions should test application, not just recall
- Mandatory training has deadlines — enforce them with escalating reminders
- Personalise learning paths based on current skill level and career goals
- Celebrate completions — recognition drives engagement

Course types: onboarding, technical, compliance, soft_skills"""


class NexusEngine:
    SYSTEM_PROMPT = SYSTEM_PROMPT

    def generate_course(self, course, instance=None) -> dict:
        prompt = f"""Design a complete course for this learning brief.

Course: {course.title}
Type: {course.course_type}
Description: {course.description}
Target Duration: {course.duration_hours} hours
Mandatory: {course.is_mandatory}

Return JSON:
{{
  "modules": [
    {{
      "module_number": integer,
      "title": "module title",
      "duration_minutes": integer,
      "learning_objectives": ["list of objectives"],
      "content_outline": ["section headings with key content points"],
      "exercise": "practical exercise description",
      "quiz_questions": [
        {{"question": "...", "options": ["A", "B", "C", "D"], "correct": "A", "explanation": "..."}}
      ]
    }}
  ],
  "total_duration_hours": float,
  "prerequisites": ["list of prerequisites"],
  "completion_criteria": "how to measure successful completion"
}}"""

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        raw = agent_chat(messages)
        try:
            res = json.loads(raw)
        except json.JSONDecodeError:
            res = {"modules": [], "total_duration_hours": course.duration_hours, "prerequisites": []}

        if instance:
            AgentLog.objects.create(
                instance=instance,
                action=f"generate_course {course.pk}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )

            if course.is_mandatory:
                raise PermissionRequired(
                    context=f"Mandatory course generated: {course.title}. Requires compliance/HR review.",
                    option_a="Approve and publish course",
                    option_b="Deny and request revision"
                )
        return res

    def learning_path(self, employee_name: str, role: str, goals: str, instance=None) -> list:
        prompt = f"""Create a personalised learning path.

Employee: {employee_name}
Current Role: {role}
Development Goals: {goals}

Return a JSON array of recommended courses in priority order:
{{
  "title": "course title",
  "type": "onboarding|technical|compliance|soft_skills",
  "priority": integer (1=highest),
  "rationale": "why this course for this person",
  "estimated_duration_hours": float,
  "deadline_weeks": integer
}}"""

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
                action="learning_path",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res

    def generate_assessment(self, course_title: str, topics: list, instance=None) -> list:
        topics_text = "\n".join(f"- {t}" for t in topics)
        prompt = f"""Generate a knowledge assessment for this course.

Course: {course_title}
Topics covered:
{topics_text}

Return a JSON array of 10 assessment questions:
{{
  "question": "question text",
  "type": "multiple_choice|true_false|short_answer",
  "options": ["if multiple_choice: A, B, C, D options"],
  "correct_answer": "correct answer",
  "topic": "which topic this tests",
  "difficulty": "easy|medium|hard"
}}"""

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
                action=f"generate_assessment for {course_title}",
                outcome='success',
                detail=json.dumps(res),
                model_used=settings.SEREA_TASK_MODELS.get('chat', 'gemini-1.5-flash'),
            )
        return res
