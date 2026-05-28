import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.babel.process_queued_jobs")
def process_queued_jobs():
    from agents.babel.models import TranslationJob, TranslationOutput
    from agents.babel.engine import BabelEngine

    engine = BabelEngine()
    queued = TranslationJob.objects.filter(status="queued")
    completed = 0

    for job in queued:
        try:
            job.status = "processing"
            job.save(update_fields=["status"])

            results = engine.translate(job)
            for result in results:
                TranslationOutput.objects.update_or_create(
                    job=job,
                    target_language=result["language"],
                    defaults={
                        "translated_text": result.get("translated_text", ""),
                        "quality_score": result.get("quality_score", 0.7),
                    },
                )

            job.status = "completed"
            job.save(update_fields=["status"])
            completed += 1
        except Exception as exc:
            logger.error("babel.process_queued_jobs job %s: %s", job.pk, exc)
            job.status = "failed"
            job.save(update_fields=["status"])

    logger.info("babel.process_queued_jobs: completed %d jobs", completed)
    return completed


@shared_task(name="agents.babel.retry_failed_jobs")
def retry_failed_jobs():
    from agents.babel.models import TranslationJob

    count = TranslationJob.objects.filter(status="failed").update(status="queued")
    logger.info("babel.retry_failed_jobs: re-queued %d jobs", count)
    return count
