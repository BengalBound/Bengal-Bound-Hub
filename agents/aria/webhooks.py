def handle_event(event_type: str, payload: dict, instance):
    """Route inbound webhook payload to the right engine method."""
    from agents.aria.engine import AriaEngine
    from agents.aria.models import SupportTicket

    engine = AriaEngine()
    if event_type == 'webhook_event':
        subject = payload.get('subject', 'New Ticket')
        description = payload.get('description', '')

        ticket = SupportTicket.objects.create(
            business=instance.business,
            subject=subject,
            description=description,
            channel='email',
            priority='medium',
            status='open'
        )

        try:
            from agents.aria.engine import PermissionRequired
            engine.resolve_ticket(ticket, instance=instance)
        except PermissionRequired as pr:
            from agents.models import AgentPermissionRequest
            from agents.platform.email_notify import EmailAdapter

            request = AgentPermissionRequest.objects.create(
                instance=instance,
                context=pr.context,
                option_a=pr.option_a,
                option_b=pr.option_b,
            )
            instance.status = 'waiting'
            instance.save(update_fields=['status'])

            try:
                if hasattr(instance.business, 'owner') and getattr(instance.business.owner, 'email', None):
                    emails = [instance.business.owner.email]
                elif hasattr(instance.business, 'users'):
                    emails = [u.email for u in instance.business.users.all() if u.email]
                else:
                    emails = ['admin@bengalbound.com']
            except Exception:
                emails = ['admin@bengalbound.com']
            if not emails:
                emails = ['admin@bengalbound.com']

            EmailAdapter(instance).send_permission_request(request, emails)
