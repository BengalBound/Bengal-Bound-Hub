import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.sage.auto_review_queued_documents")
def auto_review_queued_documents():
    from agents.sage.models import LegalDocument, Clause
    from agents.sage.engine import SageEngine
    from django.utils import timezone

    engine = SageEngine()
    queued = LegalDocument.objects.filter(status="queued")
    reviewed = 0

    for document in queued:
        try:
            document.status = "reviewing"
            document.save(update_fields=["status"])

            result = engine.review_document(document)
            document.overall_risk = result.get("overall_risk", 50)
            document.risk_label = result.get("risk_label", "medium")
            document.executive_summary = result.get("executive_summary", "")
            document.status = "completed"
            document.reviewed_at = timezone.now()
            document.save(update_fields=["overall_risk", "risk_label", "executive_summary", "status", "reviewed_at"])

            for clause_data in result.get("clauses", []):
                Clause.objects.create(
                    business=document.business,
                    document=document,
                    clause_title=clause_data.get("clause_title", ""),
                    original_text=clause_data.get("original_text", ""),
                    plain_english=clause_data.get("plain_english", ""),
                    risk_level=clause_data.get("risk_level", "safe"),
                    risk_score=clause_data.get("risk_score", 0),
                    negotiation_suggestion=clause_data.get("negotiation_suggestion", ""),
                )
            reviewed += 1
        except Exception as exc:
            logger.error("sage.auto_review_queued_documents doc %s: %s", document.pk, exc)
            document.status = "failed"
            document.save(update_fields=["status"])

    logger.info("sage.auto_review_queued_documents: reviewed %d documents", reviewed)
    return reviewed


@shared_task(name="agents.sage.high_risk_document_alert")
def high_risk_document_alert():
    from agents.sage.models import LegalDocument

    critical = LegalDocument.objects.filter(risk_label__in=["high", "critical"], status="completed")
    count = critical.count()
    for doc in critical:
        logger.warning("Sage: high-risk document [%s] — risk label: %s, score: %s",
                       doc.name, doc.risk_label, doc.overall_risk)
    logger.info("sage.high_risk_document_alert: %d high-risk documents", count)
    return count
