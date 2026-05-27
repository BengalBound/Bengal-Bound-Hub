"""
serea/signals.py
────────────────
Post-save signal on HiredAIEmployee:
  • When a new HiredAIEmployee is created (created=True), automatically
    provision a matching SereaAgent for that client.
  • When an existing HiredAIEmployee is re-activated (is_active flips to True),
    ensure a SereaAgent exists (get_or_create).
  • When deactivated, marks the SereaAgent as 'offline' without deleting it
    so history is preserved.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver

from workspace_admin.models import HiredAIEmployee
from .models import SereaAgent

logger = logging.getLogger(__name__)

# Map HiredAIEmployee tier names → SereaAgent tier choices
_TIER_MAP = {
    'intern': 'intern',
    'entry':  'entry',
    'mid':    'mid',
    'senior': 'senior',
}


@receiver(post_save, sender=HiredAIEmployee)
def provision_serea_agent(sender, instance, created, **kwargs):
    """
    Auto-create (or reactivate) a SereaAgent whenever a HiredAIEmployee is saved.
    """
    tier_name = instance.tier.name if instance.tier else 'intern'
    serea_tier = _TIER_MAP.get(tier_name, 'intern')

    if instance.is_active:
        agent, was_created = SereaAgent.objects.get_or_create(
            hired_employee=instance,
            defaults={
                'tenant':   instance.employer,
                'tier':     serea_tier,
                'status':   'idle',
            },
        )

        if was_created:
            logger.info(
                "SereaAgent #%s provisioned for HiredAIEmployee #%s (%s).",
                agent.id, instance.id, instance.employer.email,
            )
        else:
            # Employee already has an agent — make sure it's not offline
            if agent.status == 'offline':
                agent.status = 'idle'
                agent.save(update_fields=['status'])
                logger.info(
                    "SereaAgent #%s reactivated for HiredAIEmployee #%s (%s).",
                    agent.id, instance.id, instance.employer.email,
                )

            # Keep tier in sync with any tier change on the HiredAIEmployee
            if agent.tier != serea_tier:
                agent.tier = serea_tier
                agent.save(update_fields=['tier'])
                logger.info(
                    "SereaAgent #%s tier updated to '%s' for %s.",
                    agent.id, serea_tier, instance.employer.email,
                )

    else:
        # HiredAIEmployee deactivated — put the agent offline (don't delete)
        SereaAgent.objects.filter(hired_employee=instance).update(status='offline')
        logger.info(
            "SereaAgent(s) for HiredAIEmployee #%s marked offline.",
            instance.id,
        )
