import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.nexus.overdue_enrollment_alert")
def overdue_enrollment_alert():
    from django.utils import timezone
    from agents.nexus.models import Enrollment

    today = timezone.now().date()
    overdue = Enrollment.objects.filter(
        status__in=["assigned", "in_progress"],
        due_date__lt=today,
    )
    count = overdue.update(status="overdue")
    logger.warning("nexus.overdue_enrollment_alert: %d enrollments marked overdue", count)
    return count


@shared_task(name="agents.nexus.auto_generate_course_content")
def auto_generate_course_content():
    from agents.nexus.models import Course
    from agents.nexus.engine import NexusEngine

    engine = NexusEngine()
    empty_courses = Course.objects.filter(modules=[], ai_generated=False)
    generated = 0

    for course in empty_courses:
        try:
            result = engine.generate_course(course)
            course.modules = result.get("modules", [])
            course.ai_generated = True
            course.save(update_fields=["modules", "ai_generated"])
            generated += 1
        except Exception as exc:
            logger.error("nexus.auto_generate_course_content course %s: %s", course.pk, exc)

    logger.info("nexus.auto_generate_course_content: generated %d courses", generated)
    return generated


@shared_task(name="agents.nexus.weekly_progress_report")
def weekly_progress_report():
    from agents.nexus.models import Enrollment
    from django.db.models import Count, Avg

    stats = {
        "by_status": dict(Enrollment.objects.values_list("status").annotate(count=Count("id"))),
        "avg_progress": Enrollment.objects.aggregate(avg=Avg("progress_pct"))["avg"] or 0,
        "completions_this_week": Enrollment.objects.filter(status="completed").count(),
    }
    logger.info("nexus.weekly_progress_report: %s", stats)
    return stats
