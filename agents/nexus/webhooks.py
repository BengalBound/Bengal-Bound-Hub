from agents.nexus.engine import NexusEngine, PermissionRequired
from agents.nexus.models import Course
from agents.models import AgentInstance, AgentPermissionRequest

def handle_event(event_type: str, payload: dict, instance: AgentInstance):
    """Route inbound webhook payload to the right engine method for Nexus."""
    engine = NexusEngine()

    if event_type == 'course_requested':
        course = Course.objects.create(
            business=instance.business,
            title=payload.get('title', 'New Course'),
            course_type=payload.get('course_type', 'technical'),
            description=payload.get('description', ''),
            duration_hours=payload.get('duration_hours', 1.0),
            is_mandatory=payload.get('is_mandatory', False),
            modules=[],
            ai_generated=False
        )

        try:
            result = engine.generate_course(course, instance=instance)
            course.modules = result.get("modules", [])
            course.ai_generated = True
            course.save(update_fields=["modules", "ai_generated"])
        except PermissionRequired as pr:
            if "result" in locals():
                course.modules = result.get("modules", [])
                course.save(update_fields=["modules"])
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
