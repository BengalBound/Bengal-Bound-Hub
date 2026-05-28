import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.content_architect.auto_generate_planned_entries")
def auto_generate_planned_entries():
    from django.utils import timezone
    from datetime import timedelta
    from agents.content_architect.models import CalendarEntry
    from agents.content_architect.engine import ContentArchitectEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='content_architect')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = ContentArchitectEngine()
    generated = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        upcoming = CalendarEntry.objects.filter(
            calendar__business=instance.business,
            status="planned",
            publish_date__lte=(timezone.now().date() + timedelta(days=3)),
        )

        for entry in upcoming:
            if entry.generated_content:
                continue
            try:
                content = engine.generate_content(entry, instance=instance)
                entry.generated_content = content
                entry.status = "generated"
                entry.save(update_fields=["generated_content", "status"])
                generated += 1
            except PermissionRequired as pr:
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("content_architect.auto_generate entry %s: %s", entry.pk, exc)

    logger.info("content_architect.auto_generate_planned_entries: generated %d entries", generated)
    return generated


@shared_task(name="agents.content_architect.publishing_reminders")
def publishing_reminders():
    from django.utils import timezone
    from agents.content_architect.models import CalendarEntry

    today = timezone.now().date()
    due_today = CalendarEntry.objects.filter(publish_date=today, status__in=["generated", "approved"])
    count = due_today.count()
    for entry in due_today:
        logger.info("Content due today: [%s] %s (calendar: %s)", entry.channel, entry.title, entry.calendar_id)
    logger.info("content_architect.publishing_reminders: %d entries due today", count)
    return count
