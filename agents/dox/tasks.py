import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.dox.scan_outdated_docs")
def scan_outdated_docs():
    from django.utils import timezone
    from agents.dox.models import DocPage
    from agents.dox.engine import DoxEngine
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='dox')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = DoxEngine()
    flagged = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        pages = DocPage.objects.filter(project__business=instance.business, status="published")
        for page in pages:
            if not page.project.last_generated:
                continue
            days_old = (timezone.now() - page.project.last_generated).days
            if days_old < 30:
                continue
            try:
                result = engine.scan_for_outdated(page, days_old, instance=instance)
                if result.get("likely_outdated") and result.get("update_priority") in ["medium", "high"]:
                    page.status = "outdated"
                    page.save(update_fields=["status"])
                    flagged += 1
                    logger.info("Dox: flagged outdated page [%s] (%d days old)", page.title, days_old)
            except Exception as exc:
                logger.error("dox.scan_outdated_docs page %s: %s", page.pk, exc)

    logger.info("dox.scan_outdated_docs: flagged %d pages as outdated", flagged)
    return flagged


@shared_task(name="agents.dox.auto_generate_empty_pages")
def auto_generate_empty_pages():
    from agents.dox.models import DocPage
    from agents.dox.engine import DoxEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='dox')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = DoxEngine()
    generated = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        empty_pages = DocPage.objects.filter(project__business=instance.business, status="draft", content="")
        for page in empty_pages:
            try:
                content = engine.generate_page(page.project, page, instance=instance)
                page.content = content
                page.ai_generated = True
                page.word_count = len(content.split())
                page.status = "published"
                page.save(update_fields=["content", "ai_generated", "word_count", "status"])
                generated += 1
            except PermissionRequired as pr:
                # Save drafted content anyway but mark waiting
                if "content" in locals():
                    page.content = content
                    page.save(update_fields=["content"])

                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("dox.auto_generate_empty_pages page %s: %s", page.pk, exc)

    logger.info("dox.auto_generate_empty_pages: generated %d pages", generated)
    return generated
