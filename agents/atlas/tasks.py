import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.atlas.morning_briefing")
def morning_briefing():
    from django.utils import timezone
    from datetime import timedelta
    from agents.atlas.models import ExecTask, MeetingBrief
    from agents.atlas.engine import AtlasEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='atlas')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = AtlasEngine()
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    processed = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        tasks = list(ExecTask.objects.filter(business=instance.business, status__in=["open", "in_progress"])
                     .order_by("priority", "due_date")[:10])
        meetings = list(MeetingBrief.objects.filter(business=instance.business,
                                                     scheduled_at__date__range=[today, tomorrow]))
        if not tasks and not meetings:
            continue
        try:
            engine.morning_briefing(tasks, meetings, instance=instance)
            processed += 1
        except PermissionRequired as pr:
            AgentPermissionRequest.objects.create(
                instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])
        except Exception as exc:
            logger.error("atlas.morning_briefing instance %s: %s", instance.pk, exc)

    logger.info("atlas.morning_briefing: processed %d instances", processed)
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
