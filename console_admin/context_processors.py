def console_modules_processor(request):
    """
    Injects into every console template:
    - active_modules: list of ConsoleModuleActivation module_ids
    - console_biz: the user's primary BusinessInstance (or None)
    - console_modules: [{tm, url}, ...] of active TenantModules for the sidebar
    """
    ctx = {'active_modules': [], 'console_biz': None, 'console_modules': []}
    if not request.user.is_authenticated:
        return ctx

    from console_admin.models import ConsoleModuleActivation
    active_records = ConsoleModuleActivation.objects.filter(
        client=request.user, is_active=True
    )
    ctx['active_modules'] = [m.module_id for m in active_records]

    try:
        from hub.models import BusinessInstance, TenantModule
        from hub.context_processors import _resolve_module_url

        biz = BusinessInstance.objects.filter(
            owner=request.user, is_active=True
        ).select_related().first()
        if biz:
            ctx['console_biz'] = biz
            active_qs = TenantModule.objects.filter(
                business=biz, is_active=True
            ).select_related('module').order_by('module__display_order')
            ctx['console_modules'] = [
                {'tm': tm, 'url': _resolve_module_url(tm.module.url_namespace, biz.slug)}
                for tm in active_qs
            ]
    except Exception:
        pass

    # Unread notification count for the bell icon
    try:
        from workspace_admin.models import UserNotification
        ctx['unread_notification_count'] = UserNotification.objects.filter(
            user=request.user, is_read=False
        ).count()
    except Exception:
        ctx['unread_notification_count'] = 0

    # Agent instances for this business + pending approval count
    try:
        from agents.models import AgentInstance, AgentPermissionRequest
        biz = ctx.get('console_biz')
        if biz:
            ctx['agent_instances'] = (
                AgentInstance.objects
                .filter(business=biz)
                .select_related('catalog')
                .order_by('catalog__category', 'catalog__name')
            )
            ctx['pending_agent_approvals'] = AgentPermissionRequest.objects.filter(
                instance__business=biz, decision__isnull=True
            ).count()
        else:
            ctx['agent_instances'] = []
            ctx['pending_agent_approvals'] = 0
    except Exception:
        ctx['agent_instances'] = []
        ctx['pending_agent_approvals'] = 0

    return ctx
