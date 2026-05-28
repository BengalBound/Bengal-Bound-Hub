import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.aria.auto_resolve_tickets")
def auto_resolve_tickets():
    from agents.aria.models import SupportTicket, TicketResponse
    from agents.aria.engine import AriaEngine

    engine = AriaEngine()
    tickets = SupportTicket.objects.filter(status="open", priority__in=["low", "medium"])
    resolved = 0

    for ticket in tickets:
        try:
            result = engine.resolve_ticket(ticket)
            if result.get("confidence", 0) >= 0.8 and not result.get("escalate", True):
                TicketResponse.objects.create(
                    ticket=ticket,
                    content=result.get("customer_reply", ""),
                    is_ai_generated=True,
                )
                ticket.status = "resolved"
                ticket.save(update_fields=["status"])
                resolved += 1
        except Exception as exc:
            logger.error("aria.auto_resolve_tickets: ticket %s failed: %s", ticket.pk, exc)

    logger.info("aria.auto_resolve_tickets: resolved %d tickets", resolved)
    return resolved


@shared_task(name="agents.aria.sla_breach_check")
def sla_breach_check():
    from django.utils import timezone
    from datetime import timedelta
    from agents.aria.models import SupportTicket

    sla_hours = {"urgent": 1, "high": 4, "medium": 24, "low": 48}
    breached = []

    for ticket in SupportTicket.objects.filter(status__in=["open", "in_progress"]):
        limit_hours = sla_hours.get(ticket.priority, 24)
        age = (timezone.now() - ticket.created_at).total_seconds() / 3600
        if age > limit_hours:
            breached.append(str(ticket.pk))
            logger.warning("SLA breached: ticket %s (%s, %s)", ticket.pk, ticket.priority, ticket.subject)

    logger.info("aria.sla_breach_check: %d breached tickets", len(breached))
    return breached


@shared_task(name="agents.aria.daily_support_digest")
def daily_support_digest():
    from agents.aria.models import SupportTicket
    from agents.aria.engine import AriaEngine
    from django.db.models import Count

    engine = AriaEngine()
    stats = SupportTicket.objects.values("business_id", "status").annotate(count=Count("id"))
    logger.info("aria.daily_support_digest: %d stat rows processed", len(stats))
    return list(stats)
