import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.atlas.morning_briefing")
def morning_briefing():
    from django.utils import timezone
    from datetime import timedelta
    from agents.atlas.models import ExecTask, MeetingBrief
    from agents.atlas.engine import AtlasEngine
    from hub.models import BusinessInstance

    engine = AtlasEngine()
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    processed = 0

    for business in BusinessInstance.objects.filter(is_active=True):
        tasks = list(ExecTask.objects.filter(business=business, status__in=["open", "in_progress"])
                     .order_by("priority", "due_date")[:10])
        meetings = list(MeetingBrief.objects.filter(business=business,
                                                     scheduled_at__date__range=[today, tomorrow]))
        if not tasks and not meetings:
            continue
        try:
            engine.morning_briefing(tasks, meetings)
            processed += 1
        except Exception as exc:
            logger.error("atlas.morning_briefing business %s: %s", business.slug, exc)

    logger.info("atlas.morning_briefing: processed %d businesses", processed)
    return processed


@shared_task(name="agents.atlas.overdue_task_alert")
def overdue_task_alert():
    from django.utils import timezone
    from agents.atlas.models import ExecTask

    today = timezone.now().date()
    overdue = ExecTask.objects.filter(status__in=["open", "in_progress"], due_date__lt=today)
    count = overdue.count()

    for task in overdue:
        logger.warning("Atlas: overdue task [%s] — %s (business: %s)", task.priority, task.title, task.business_id)

    logger.info("atlas.overdue_task_alert: %d overdue tasks", count)
    return count


@shared_task(name="agents.atlas.weekly_summary")
def weekly_summary():
    from agents.atlas.models import ExecTask
    from django.db.models import Count

    stats = (ExecTask.objects
             .values("business_id", "status")
             .annotate(count=Count("id")))
    logger.info("atlas.weekly_summary: %d stat rows", len(stats))
    return list(stats)
