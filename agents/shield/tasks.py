import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name="agents.shield.auto_resolve_open_tickets")
def auto_resolve_open_tickets():
    from agents.shield.models import ITTicket, KnowledgeArticle
    from agents.shield.engine import ShieldEngine, PermissionRequired
    from agents.models import AgentInstance, AgentCatalog, AgentPermissionRequest

    try:
        catalog = AgentCatalog.objects.get(slug='shield')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = ShieldEngine()
    resolved = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        open_tickets = ITTicket.objects.filter(business=instance.business, status="open", priority__in=["low", "medium"])
        for ticket in open_tickets:
            try:
                kb_articles = list(KnowledgeArticle.objects.filter(
                    business=ticket.business, category=ticket.category
                ).order_by("-success_count")[:3])

                result = engine.resolve_ticket(ticket, kb_articles, instance=instance)
                ticket.ai_solution = result.get("ai_solution", "")
                ticket.ai_confidence = result.get("ai_confidence", 0.5)
                ticket.sla_hours = {"low": 48, "medium": 24, "high": 4, "urgent": 1}.get(ticket.priority, 24)

                if result.get("should_auto_resolve") and result.get("ai_confidence", 0) >= 0.8:
                    ticket.status = "resolved"
                    resolved += 1
                    kb_draft = result.get("kb_article_draft", {})
                    if kb_draft:
                        KnowledgeArticle.objects.get_or_create(
                            business=ticket.business,
                            title=kb_draft.get("title", ticket.title),
                            defaults={
                                "category": ticket.category,
                                "problem": kb_draft.get("problem", ""),
                                "solution": kb_draft.get("solution", ""),
                            },
                        )
                else:
                    ticket.status = "ai_resolving"

                ticket.save(update_fields=["ai_solution", "ai_confidence", "sla_hours", "status"])
            except PermissionRequired as pr:
                # Save partial
                if "result" in locals():
                    ticket.ai_solution = locals()['result'].get("ai_solution", "")
                    ticket.ai_confidence = locals()['result'].get("ai_confidence", 0.5)
                    ticket.sla_hours = {"low": 48, "medium": 24, "high": 4, "urgent": 1}.get(ticket.priority, 24)
                    ticket.save(update_fields=["ai_solution", "ai_confidence", "sla_hours"])

                AgentPermissionRequest.objects.create(
                    instance=instance, context=pr.context, option_a=pr.option_a, option_b=pr.option_b
                )
                instance.status = 'waiting'
                instance.save(update_fields=['status'])
            except Exception as exc:
                logger.error("shield.auto_resolve_open_tickets ticket %s: %s", ticket.pk, exc)

    logger.info("shield.auto_resolve_open_tickets: auto-resolved %d tickets", resolved)
    return resolved


@shared_task(name="agents.shield.sla_breach_monitor")
def sla_breach_monitor():
    from agents.shield.models import ITTicket
    from agents.shield.engine import ShieldEngine
    from agents.models import AgentInstance, AgentCatalog

    try:
        catalog = AgentCatalog.objects.get(slug='shield')
    except AgentCatalog.DoesNotExist:
        return 0

    engine = ShieldEngine()
    breached_count = 0

    for instance in AgentInstance.objects.filter(catalog=catalog, status='idle'):
        open_tickets = ITTicket.objects.filter(business=instance.business, status__in=["open", "ai_resolving"], sla_breached=False)
        for ticket in open_tickets:
            sla = engine.sla_assessment(ticket, instance=instance)
            if sla["breached"]:
                ticket.sla_breached = True
                ticket.save(update_fields=["sla_breached"])
                logger.warning("Shield SLA breach: ticket [%s] %s — age: %.1fh, limit: %dh",
                               ticket.priority, ticket.title, sla["age_hours"], sla["sla_limit_hours"])
                breached_count += 1

    logger.info("shield.sla_breach_monitor: %d new SLA breaches", breached_count)
    return breached_count
