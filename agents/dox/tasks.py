import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.dox.scan_outdated_docs")
def scan_outdated_docs():
    from django.utils import timezone
    from agents.dox.models import DocPage
    from agents.dox.engine import DoxEngine

    engine = DoxEngine()
    pages = DocPage.objects.filter(status="published")
    flagged = 0

    for page in pages:
        if not page.project.last_generated:
            continue
        days_old = (timezone.now() - page.project.last_generated).days
        if days_old < 30:
            continue
        try:
            result = engine.scan_for_outdated(page, days_old)
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
    from agents.dox.engine import DoxEngine

    engine = DoxEngine()
    empty_pages = DocPage.objects.filter(status="draft", content="")
    generated = 0

    for page in empty_pages:
        try:
            content = engine.generate_page(page.project, page)
            page.content = content
            page.ai_generated = True
            page.word_count = len(content.split())
            page.status = "published"
            page.save(update_fields=["content", "ai_generated", "word_count", "status"])
            generated += 1
        except Exception as exc:
            logger.error("dox.auto_generate_empty_pages page %s: %s", page.pk, exc)

    logger.info("dox.auto_generate_empty_pages: generated %d pages", generated)
    return generated
