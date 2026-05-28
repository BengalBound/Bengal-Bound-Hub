import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.nexus.overdue_enrollment_alert")
def overdue_enrollment_alert():
    from django.utils import timezone
    from agents.nexus.models import Enrollment
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='nexus')
    except AgentCatalog.DoesNotExist:
        return 0

    today = timezone.now().date()
    total_count = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        overdue = Enrollment.objects.filter(
            course__business=instance.business,
            status__in=["assigned", "in_progress"],
            due_date__lt=today,
        )
        count = overdue.update(status="overdue")
        total_count += count
        if count > 0:
            logger.warning("nexus.overdue_enrollment_alert: %d enrollments marked overdue for %s", count, instance.business.slug)

    return total_count


@shared_task(name="agents.nexus.auto_generate_course_content")
def auto_generate_course_content():
    from agents.nexus.models import Course
    from agents.nexus.engine import NexusEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='nexus')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = NexusEngine()
    generated = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        empty_courses = Course.objects.filter(business=instance.business, modules=[], ai_generated=False)
        for course in empty_courses:
            try:
                result = engine.generate_course(course, instance=instance)
                course.modules = result.get("modules", [])
                course.ai_generated = True
                course.save(update_fields=["modules", "ai_generated"])
                generated += 1
            except PermissionRequired as pr:
                if "result" in locals():
                    course.modules = result.get("modules", [])
                    course.save(update_fields=["modules"])
                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("nexus.auto_generate_course_content course %s: %s", course.pk, exc)

    logger.info("nexus.auto_generate_course_content: generated %d courses", generated)
    return generated


@shared_task(name="agents.nexus.weekly_progress_report")
def weekly_progress_report():
    from agents.nexus.models import Enrollment
    from django.db.models import Count, Avg
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='nexus')
    except AgentCatalog.DoesNotExist:
        return 0

    total_stats = []

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        stats = {
            "business": instance.business.slug,
            "by_status": dict(Enrollment.objects.filter(course__business=instance.business).values_list("status").annotate(count=Count("id"))),
            "avg_progress": Enrollment.objects.filter(course__business=instance.business).aggregate(avg=Avg("progress_pct"))["avg"] or 0,
            "completions_this_week": Enrollment.objects.filter(course__business=instance.business, status="completed").count(),
        }
        total_stats.append(stats)
        logger.info("nexus.weekly_progress_report for %s: %s", instance.business.slug, stats)
    return total_stats
