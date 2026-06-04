from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from .decorators import console_user_required
from .models import (
    WorkspaceProject, AITask, SupportTicket,
    AIChatInteraction, AICredential, AITrainingDocument, AITaskLimit
)
from workspace_admin.models import HiredAIEmployee

# ─── My AI Employee ────────────────────────────────────────────────────────────

@console_user_required(login_url='/accounts/login/')
def my_ai(request):
    """
    The 'My AI Employee' page — shows the user's Serea agent as a profile card.
    Tabbed interface: Overview | Chat | Moderation Logs | Content Queue | Reports
    """
    from serea.models import ConversationMessage, ModerationLog, ContentQueue, SereaReport, SereaTask

    hired_ai = HiredAIEmployee.objects.filter(employer=request.user, is_active=True).select_related('tier').first()
    serea_agent = None
    recent_messages = []
    moderation_logs = []
    content_queue = []
    reports = []
    tasks = []
    pending_approvals = 0

    if hired_ai:
        try:
            serea_agent = hired_ai.serea_agent
        except Exception:
            serea_agent = None

    if serea_agent:
        recent_messages = ConversationMessage.objects.filter(
            agent=serea_agent
        ).order_by('created_at')

        mod_logs_qs = ModerationLog.objects.filter(agent=serea_agent).order_by('-created_at')
        mod_paginator = Paginator(mod_logs_qs, 25)
        moderation_logs = mod_paginator.get_page(request.GET.get('mod_page'))

        cq_qs = ContentQueue.objects.filter(agent=serea_agent).order_by('post_date')
        cq_paginator = Paginator(cq_qs, 20)
        content_queue = cq_paginator.get_page(request.GET.get('cq_page'))

        reports = SereaReport.objects.filter(
            agent=serea_agent
        ).order_by('-created_at')[:10]

        tasks = SereaTask.objects.filter(
            agent=serea_agent
        ).exclude(status='cancelled').order_by('-updated_at')[:30]

        pending_approvals = ConversationMessage.objects.filter(
            agent=serea_agent,
            is_permission_request=True,
            permission_granted__isnull=True
        ).count()

    # Handle new chat message POST
    if request.method == 'POST' and serea_agent:
        msg_text = request.POST.get('message', '').strip()
        if msg_text:
            from serea.models import ConversationMessage as SereaMsg
            from serea.logic import SereaBrain, TokenLimitExceeded
            SereaMsg.objects.create(agent=serea_agent, sender=request.user.email, message_text=msg_text)
            try:
                brain = SereaBrain(agent_id=serea_agent.id)
                reply = brain.chat(msg_text)
            except TokenLimitExceeded as exc:
                reply = str(exc)
            except Exception as exc:
                reply = f"Something went wrong on my end. Try again? ({exc})"
            SereaMsg.objects.create(agent=serea_agent, sender='serea', message_text=reply)
        return redirect('/my-ai/')

    return render(request, 'console_admin/my_ai.html', {
        'hired_ai': hired_ai,
        'serea_agent': serea_agent,
        'recent_messages': recent_messages,
        'moderation_logs': moderation_logs,
        'content_queue': content_queue,
        'reports': reports,
        'tasks': tasks,
        'pending_approvals': pending_approvals,
        'mod_count': moderation_logs.count() if hasattr(moderation_logs, 'query') else len(moderation_logs),
        'content_count': ContentQueue.objects.filter(agent=serea_agent, status='posted').count() if serea_agent else 0,
        'report_count': reports.count() if hasattr(reports, 'query') else len(reports),
        'task_count': tasks.count() if hasattr(tasks, 'query') else len(tasks),
    })


@console_user_required(login_url='/accounts/login/')
def hire_ai(request):
    """Marketplace directory for the client to view available AI Tiers."""
    from workspace_admin.models import AIEmployeeTier
    tiers = AIEmployeeTier.objects.all().order_by('?')
    return render(request, 'console_admin/hire_ai.html', {'tiers': tiers})

# ─── AI Workforce Hub ──────────────────────────────────────────────────────────

@console_user_required(login_url='/accounts/login/')
def ai_chat(request, ai_id=None):
    """
    DM Interface — Chat with a hired AI employee.
    When the AI has a linked SereaAgent, messages are stored in ConversationMessage
    and responses are powered by SereaBrain (LangChain + Groq/OpenAI).
    Falls back to the legacy AIChatInteraction for non-Serea AIs.
    """
    hired_ais = HiredAIEmployee.objects.filter(employer=request.user, is_active=True)
    active_ai = None
    chat_messages = []
    serea_agent = None

    if ai_id:
        active_ai = get_object_or_404(HiredAIEmployee, id=ai_id, employer=request.user)

        # ── Check whether this AI has a live Serea agent ──────────────────────
        try:
            serea_agent = active_ai.serea_agent  # OneToOneField reverse accessor
            if serea_agent.status == 'offline':
                serea_agent = None  # Treat offline agents as unavailable
        except Exception:
            serea_agent = None

        if serea_agent:
            from serea.models import ConversationMessage as SereaMsg
            chat_messages = SereaMsg.objects.filter(agent=serea_agent).order_by('created_at')

            # ── Auto-welcome: send Serea's first onboarding message if no chat yet ──
            if not chat_messages.exists():
                from serea.models import SocialMediaAccount as _SMA, ClientContentFile as _CCF
                has_platforms = _SMA.objects.filter(agent=serea_agent, is_active=True).exists()
                has_content   = _CCF.objects.filter(agent=serea_agent, is_active=True).exists()

                if not has_platforms and not has_content:
                    welcome = (
                        "Hey — I'm Serea, just started. Good to meet you.\n\n"
                        "Before I can do anything useful, I need two things from you:\n\n"
                        "**Platforms** — I need access to your Facebook, Instagram, and/or LinkedIn accounts "
                        "so I can actually get in there and work. Add them at [Platform Connections](/platforms/).\n\n"
                        "**Business info** — the more you tell me about your business, the better I can represent you. "
                        "Drop products, FAQs, brand voice notes, response templates — whatever you've got — "
                        "in the [Workspace](/workspace/). Even a rough doc is a good start.\n\n"
                        "Once both are in, just message me and we'll get going."
                    )
                elif not has_platforms:
                    welcome = (
                        "Hey — I can see you've already uploaded some business content, which is great.\n\n"
                        "One thing I'm still missing: access to your social media accounts. "
                        "Head to [Platform Connections](/platforms/) and connect whichever platforms you want me to handle "
                        "— Facebook, Instagram, LinkedIn, or all three.\n\n"
                        "Once that's done, I'm ready."
                    )
                elif not has_content:
                    welcome = (
                        "Hey — platforms are connected, so I'm ready on that front.\n\n"
                        "The one thing that'd really help me is knowing more about your business. "
                        "If you can drop something in the [Workspace](/workspace/) — product info, FAQs, "
                        "how you want people to sound when they represent you — I can use that to write "
                        "proper posts and reply to customers the right way.\n\n"
                        "Or if it's easier, just tell me about the business here and I'll work from that."
                    )
                else:
                    welcome = (
                        "Hey — looks like everything's already set up. Let's get into it.\n\n"
                        "I've got access to your platforms and I've gone through your business content. "
                        "I can handle moderation, write and schedule posts, reply to DMs, manage campaigns, "
                        "and send you a daily briefing on how things are going.\n\n"
                        "If anything comes up that I'm not sure about, I'll check in with you before doing anything — "
                        "I'll always give you my take on the situation and a recommendation, not just a question.\n\n"
                        "What would you like me to start with?"
                    )

                SereaMsg.objects.create(
                    agent=serea_agent,
                    sender='serea',
                    message_text=welcome,
                )
                chat_messages = SereaMsg.objects.filter(agent=serea_agent).order_by('created_at')
        else:
            chat_messages = AIChatInteraction.objects.filter(
                client=request.user, ai_employee=active_ai
            ).order_by('timestamp')

    if request.method == 'POST' and active_ai:
        msg_content = request.POST.get('message', '').strip()
        if msg_content:
            if serea_agent:
                from serea.models import ConversationMessage as SereaMsg
                from serea.logic import SereaBrain, TokenLimitExceeded

                # Store the client's message
                SereaMsg.objects.create(
                    agent=serea_agent,
                    sender=request.user.email,
                    message_text=msg_content,
                )

                # Get Serea's reply synchronously
                # (Use process_chat_message_task.delay() for async in production)
                try:
                    brain = SereaBrain(agent_id=serea_agent.id)
                    reply = brain.chat(msg_content)
                except TokenLimitExceeded as exc:
                    reply = str(exc)
                except Exception as exc:
                    reply = f"I encountered an issue responding. Please try again. ({exc})"

                SereaMsg.objects.create(
                    agent=serea_agent,
                    sender='serea',
                    message_text=reply,
                )
            else:
                AIChatInteraction.objects.create(
                    client=request.user,
                    ai_employee=active_ai,
                    message_content=msg_content,
                    is_from_ai=False,
                )
                AIChatInteraction.objects.create(
                    client=request.user,
                    ai_employee=active_ai,
                    message_content="[AI engine connection pending]",
                    is_from_ai=True,
                )

        return redirect(f'/ai-chat/{active_ai.id}/')

    return render(request, 'console_admin/ai_chat.html', {
        'hired_ais': hired_ais,
        'active_ai': active_ai,
        'chat_messages': chat_messages,
        'serea_agent': serea_agent,
    })

@console_user_required(login_url='/accounts/login/')
def task_management(request):
    """Task overview — all tasks assigned to the client's AI employees."""
    all_tasks = AITask.objects.filter(project__client=request.user).order_by('-created_at')
    hired_ais = HiredAIEmployee.objects.filter(employer=request.user, is_active=True)
    # Grab or create limits for each AI
    ai_limits = {limit.ai_employee_id: limit for limit in AITaskLimit.objects.filter(client=request.user)}
    return render(request, 'console_admin/task_management.html', {
        'all_tasks': all_tasks,
        'hired_ais': hired_ais,
        'ai_limits': ai_limits,
    })

@console_user_required(login_url='/accounts/login/')
def task_create(request):
    """Assign a new task to a hired AI employee."""
    hired_ais = HiredAIEmployee.objects.filter(employer=request.user, is_active=True)
    projects = WorkspaceProject.objects.filter(client=request.user)

    if request.method == 'POST':
        title = request.POST.get('title')
        instructions = request.POST.get('instructions')
        ai_id = request.POST.get('ai_employee')
        project_id = request.POST.get('project')

        ai = get_object_or_404(HiredAIEmployee, id=ai_id, employer=request.user)
        project = get_object_or_404(WorkspaceProject, id=project_id, client=request.user)

        AITask.objects.create(
            project=project, assigned_ai=ai,
            title=title, instructions=instructions
        )
        messages.success(request, f'Task "{title}" assigned to {ai.ai_name}!')
        return redirect('console_admin:task_management')

    return render(request, 'console_admin/task_create.html', {
        'hired_ais': hired_ais,
        'projects': projects,
    })

@console_user_required(login_url='/accounts/login/')
def ai_training(request):
    """
    Training section — upload documents/instructions to train Serea.
    Active documents are injected as context into n8n workflows.
    """
    hired_ais = HiredAIEmployee.objects.filter(employer=request.user, is_active=True)
    training_docs = AITrainingDocument.objects.filter(client=request.user).order_by('-created_at')

    if request.method == 'POST':
        title = request.POST.get('title')
        ai_id = request.POST.get('ai_employee')
        doc_type = request.POST.get('document_type', 'instruction')
        content = request.POST.get('content')

        ai = get_object_or_404(HiredAIEmployee, id=ai_id, employer=request.user)
        AITrainingDocument.objects.create(
            client=request.user, ai_employee=ai,
            title=title, document_type=doc_type, content=content
        )
        messages.success(request, f'Training document "{title}" saved and added to {ai.ai_name}\'s knowledge.')
        return redirect('console_admin:ai_training')

    return render(request, 'console_admin/ai_training.html', {
        'hired_ais': hired_ais,
        'training_docs': training_docs,
        'doc_type_choices': AITrainingDocument.DOCUMENT_TYPES,
    })

# ─── Operations ────────────────────────────────────────────────────────────────

@console_user_required(login_url='/accounts/login/')
def tickets(request):
    """Support ticket system — create and track tickets."""
    all_tickets = SupportTicket.objects.filter(client=request.user).order_by('-created_at')

    if request.method == 'POST':
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        SupportTicket.objects.create(
            client=request.user, subject=subject, description=description
        )
        messages.success(request, 'Support ticket submitted successfully.')
        return redirect('console_admin:tickets')

    return render(request, 'console_admin/tickets.html', {'all_tickets': all_tickets})

@console_user_required(login_url='/accounts/login/')
def tools(request):
    """
    Tools & Integrations — manage API credentials for AI employees,
    and view affiliate status if the user is an affiliate.
    """
    hired_ais = HiredAIEmployee.objects.filter(employer=request.user, is_active=True)
    credentials = AICredential.objects.filter(client=request.user).order_by('-created_at')
    affiliate_profile = getattr(request.user, 'affiliate_profile', None)

    if request.method == 'POST':
        ai_id = request.POST.get('ai_employee')
        service_name = request.POST.get('service_name')
        api_key = request.POST.get('api_key_or_token')
        ai = get_object_or_404(HiredAIEmployee, id=ai_id, employer=request.user)
        AICredential.objects.create(
            client=request.user, ai_employee=ai,
            service_name=service_name, api_key_or_token=api_key
        )
        messages.success(request, f'Credential for "{service_name}" saved.')
        return redirect('console_admin:tools')

    return render(request, 'console_admin/tools.html', {
        'hired_ais': hired_ais,
        'credentials': credentials,
        'affiliate_profile': affiliate_profile,
    })

@console_user_required(login_url='/accounts/login/')
def dashboard(request):
    """
    Unified console dashboard — business overview + AI employee panel in one place.
    """
    # 1. Veritas KYB Gate
    try:
        from modules.veritas.models import ClientApplication
        kyb_app = ClientApplication.objects.filter(user=request.user).first()
        if not kyb_app or kyb_app.status != 'approved':
            if not kyb_app:
                return redirect('console_admin:veritas_user:kyb_apply')
            return redirect('console_admin:veritas_user:kyb_pending')
    except ImportError:
        pass

    from hub.models import BusinessInstance
    from .models import ConsoleModuleActivation
    from serea.models import ConversationMessage, ModerationLog, ContentQueue, SereaReport, SereaTask

    biz = BusinessInstance.objects.filter(owner=request.user, is_active=True).first()
    
    if not biz:
        return redirect('console_admin:hybrid_onboarding')

    from hub.models import DashboardConfig
    dashboard_config, _ = DashboardConfig.objects.get_or_create(business=biz)
    if not dashboard_config.is_configured:
        return redirect('console_admin:hybrid_onboarding')

    active_module_records = ConsoleModuleActivation.objects.filter(client=request.user, is_active=True)
    active_modules = [m.module_id for m in active_module_records]

    hired_ai = HiredAIEmployee.objects.filter(employer=request.user, is_active=True).select_related('tier').first()
    open_tickets = SupportTicket.objects.filter(client=request.user).exclude(status='resolved')

    serea_agent = None
    recent_messages = []
    moderation_logs = []
    content_queue = []
    reports = []
    tasks = []
    pending_approvals = 0

    if hired_ai:
        try:
            serea_agent = hired_ai.serea_agent
        except Exception:
            serea_agent = None

    if serea_agent:
        recent_messages = ConversationMessage.objects.filter(
            agent=serea_agent
        ).order_by('created_at')
        moderation_logs = ModerationLog.objects.filter(
            agent=serea_agent
        ).order_by('-created_at')[:50]
        content_queue = ContentQueue.objects.filter(
            agent=serea_agent
        ).order_by('post_date')[:20]
        reports = SereaReport.objects.filter(
            agent=serea_agent
        ).order_by('-created_at')[:10]
        tasks = SereaTask.objects.filter(
            agent=serea_agent
        ).exclude(status='cancelled').order_by('-updated_at')[:30]
        pending_approvals = ConversationMessage.objects.filter(
            agent=serea_agent,
            is_permission_request=True,
            permission_granted__isnull=True,
        ).count()

    if request.method == 'POST' and serea_agent:
        msg_text = request.POST.get('message', '').strip()
        if msg_text:
            from serea.logic import SereaBrain, TokenLimitExceeded
            ConversationMessage.objects.create(
                agent=serea_agent, sender=request.user.email, message_text=msg_text
            )
            try:
                brain = SereaBrain(agent_id=serea_agent.id)
                reply = brain.chat(msg_text)
            except TokenLimitExceeded as exc:
                reply = str(exc)
            except Exception as exc:
                reply = f"Something went wrong on my end. Try again? ({exc})"
            ConversationMessage.objects.create(
                agent=serea_agent, sender='serea', message_text=reply
            )
        return redirect('console_admin:dashboard')

    # Fetch active business modules for the modules grid
    tenant_modules = []
    employee_count = 0
    biz_sub = None
    if biz:
        from hub.models import TenantModule, BusinessEmployee, BusinessSubscription
        from hub.context_processors import _resolve_module_url
        active_qs = TenantModule.objects.filter(
            business=biz, is_active=True
        ).select_related('module').order_by('module__display_order')
        tenant_modules = [
            {'tm': tm, 'url': _resolve_module_url(tm.module.url_namespace, biz.slug)}
            for tm in active_qs
        ]
        employee_count = BusinessEmployee.objects.filter(business=biz, is_active=True).count()
        biz_sub = BusinessSubscription.objects.filter(business=biz).order_by('-started_at').first()

    marketplace_catalog = [
        {
            'id': 'ai_workforce',
            'name': 'AI Employees (Serea / Aelin / Kael)',
            'icon': 'bi-robot',
            'desc': 'Hire dedicated AI receptionists and digital workers to manage your tasks, chat, and support.',
            'category': 'Automation',
        },
    ]

    widgets = sorted(dashboard_config.layout.get('widgets', []), key=lambda x: x.get('order', 99))

    return render(request, 'console_admin/dashboard.html', {
        'biz': biz,
        'biz_sub': biz_sub,
        'tenant_modules': tenant_modules,
        'employee_count': employee_count,
        'active_modules': active_modules,
        'hired_ai': hired_ai,
        'open_tickets': open_tickets,
        'serea_agent': serea_agent,
        'recent_messages': recent_messages,
        'moderation_logs': moderation_logs,
        'content_queue': content_queue,
        'reports': reports,
        'tasks': tasks,
        'pending_approvals': pending_approvals,
        'mod_count': moderation_logs.count() if hasattr(moderation_logs, 'query') else len(moderation_logs),
        'content_count': ContentQueue.objects.filter(agent=serea_agent, status='posted').count() if serea_agent else 0,
        'report_count': reports.count() if hasattr(reports, 'query') else len(reports),
        'task_count': tasks.count() if hasattr(tasks, 'query') else len(tasks),
        'marketplace_catalog': marketplace_catalog,
        'dashboard_config': dashboard_config,
        'widgets': widgets,
    })

@console_user_required(login_url='/accounts/login/')
def activate_module(request):
    if request.method == 'POST':
        module_id = request.POST.get('module_id')
        if module_id:
            from .models import ConsoleModuleActivation
            # Instantly unlock the free tier (if applicable) or access panel
            ConsoleModuleActivation.objects.get_or_create(
                client=request.user,
                module_id=module_id,
                defaults={'tier': 'free', 'is_active': True}
            )
            messages.success(request, f"Module '{module_id}' added to your console space.")
    return redirect('console_admin:dashboard')

@console_user_required(login_url='/accounts/login/')
def hire_ai(request):
    """
    Marketplace directory for the client to view available AI Tiers and "hire" them.
    Handles tier selection, duration, and NowPayments invoice generation.
    Supports hiring a specific AI Agent catalog item via the 'agent' parameter.
    """
    from workspace_admin.models import AIEmployeeTier, Subscription
    from agents.models import AgentCatalog
    from django.urls import reverse

    tiers = list(AIEmployeeTier.objects.all().order_by('monthly_price_usd'))

    agent_slug = request.GET.get('agent', '').strip()
    agent_catalog = None
    if agent_slug:
        agent_catalog = get_object_or_404(AgentCatalog, slug=agent_slug, is_active=True)
        # Check if already hired
        if HiredAIEmployee.objects.filter(
            employer=request.user,
            agent_catalog=agent_catalog,
            is_active=True
        ).exists():
            messages.info(request, f"You already have an active {agent_catalog.name} employee.")
            return redirect('console_admin:agents_overview')

    # Annotate tiers with a disabled flag if they don't meet the agent's requirements
    tier_ranks = {'intern': 0, 'entry': 1, 'mid': 2, 'senior': 3}
    for t in tiers:
        t.is_disabled = False
        if agent_catalog:
            req_rank = tier_ranks.get(agent_catalog.tier_required, 1)
            current_rank = tier_ranks.get(t.name, 0)
            if current_rank < req_rank:
                t.is_disabled = True

    if request.method == 'POST':
        tier_id = request.POST.get('tier_id')
        duration_months = int(request.POST.get('duration_months', 1))
        post_agent_slug = request.POST.get('agent_slug', '').strip()

        tier = get_object_or_404(AIEmployeeTier, id=tier_id)

        # Enforce tier requirement on POST as well
        post_agent_catalog = None
        if post_agent_slug:
            post_agent_catalog = get_object_or_404(AgentCatalog, slug=post_agent_slug, is_active=True)
            if HiredAIEmployee.objects.filter(
                employer=request.user,
                agent_catalog=post_agent_catalog,
                is_active=True
            ).exists():
                messages.warning(request, f"You already have an active {post_agent_catalog.name} employee.")
                return redirect('console_admin:agents_overview')

            req_rank = tier_ranks.get(post_agent_catalog.tier_required, 1)
            current_rank = tier_ranks.get(tier.name, 0)
            if current_rank < req_rank:
                messages.error(request, f"Hiring {post_agent_catalog.name} requires at least the {post_agent_catalog.tier_required|title} tier.")
                return redirect(f"{reverse('console_admin:hire_ai')}?agent={post_agent_slug}")

        # Instead of bypassing payment, redirect to Stripe Checkout
        from billing.services import create_ai_checkout_session
        base_url = request.build_absolute_uri('/')[:-1]
        try:
            checkout_url = create_ai_checkout_session(request.user, tier, duration_months, base_url, post_agent_slug)
            return redirect(checkout_url)
        except Exception as e:
            messages.error(request, f"Failed to initialize checkout: {e}")
            if post_agent_slug:
                return redirect(f"{reverse('console_admin:hire_ai')}?agent={post_agent_slug}")
            return redirect('console_admin:hire_ai')

    return render(request, 'console_admin/hire_ai.html', {
        'tiers': tiers,
        'agent_catalog': agent_catalog,
    })


# ─── Facebook OAuth helpers ────────────────────────────────────────────────────

def _get_fb_redirect_uri(request):
    from django.conf import settings as _s
    return _s.FACEBOOK_OAUTH_REDIRECT_URI or request.build_absolute_uri('/platforms/facebook/callback/')


def _subscribe_page_webhooks(page_id, page_token, ig_id=None):
    """
    Silently subscribe the app to this page's real-time webhook events.
    Called automatically after OAuth — clients never need to touch the Dev Console.
    """
    import requests as _r
    try:
        _r.post(
            f'https://graph.facebook.com/v18.0/{page_id}/subscribed_apps',
            params={
                'access_token': page_token,
                'subscribed_fields': (
                    'messages,messaging_postbacks,messaging_optins,'
                    'feed,mention,comments,message_reactions'
                ),
            },
            timeout=10,
        )
    except Exception:
        pass  # Non-fatal — Serea can still work via polling if this fails

    if ig_id:
        try:
            _r.post(
                f'https://graph.facebook.com/v18.0/{ig_id}/subscribed_apps',
                params={
                    'access_token': page_token,
                    'subscribed_fields': 'messages,comments,mentions',
                },
                timeout=10,
            )
        except Exception:
            pass


from django.db import transaction as _db_transaction

@_db_transaction.atomic
def _save_fb_page(serea_agent, page):
    """
    Persist a Facebook Page connection, auto-detect linked Instagram Business account,
    auto-subscribe real-time webhooks, and update managed_platforms.
    Returns (fb_account, ig_account_or_None).
    All DB writes are atomic — if any step fails the whole connection is rolled back.
    """
    import requests as _r
    from serea.models import SocialMediaAccount, ConversationMessage

    # ── Facebook ──────────────────────────────────────────────────────────────
    SocialMediaAccount.objects.filter(agent=serea_agent, platform='facebook').delete()
    fb_account = SocialMediaAccount.objects.create(
        agent=serea_agent,
        platform='facebook',
        account_name=page['name'],
        account_id=page['id'],
        access_token=page['access_token'],
        status='connected',
        is_active=True,
    )

    # ── Instagram (auto-detect linked IG Business account) ────────────────────
    ig_account = None
    ig_id = None
    try:
        ig_resp = _r.get(
            f'https://graph.facebook.com/v18.0/{page["id"]}',
            params={'fields': 'instagram_business_account', 'access_token': page['access_token']},
            timeout=10,
        )
        ig_data = ig_resp.json().get('instagram_business_account') if ig_resp.ok else None
        if ig_data:
            ig_id = ig_data['id']
            detail_resp = _r.get(
                f'https://graph.facebook.com/v18.0/{ig_id}',
                params={'fields': 'username,name', 'access_token': page['access_token']},
                timeout=10,
            )
            ig_detail = detail_resp.json() if detail_resp.ok else {}
            ig_name = ig_detail.get('username') or ig_detail.get('name') or 'Instagram'
            SocialMediaAccount.objects.filter(agent=serea_agent, platform='instagram').delete()
            ig_account = SocialMediaAccount.objects.create(
                agent=serea_agent,
                platform='instagram',
                account_name=ig_name,
                account_id=ig_id,
                access_token=page['access_token'],
                status='connected',
                is_active=True,
            )
    except Exception:
        pass

    # ── Auto-subscribe webhooks (clients never have to do this themselves) ────
    _subscribe_page_webhooks(page['id'], page['access_token'], ig_id=ig_id)

    # ── Auto-update managed_platforms on the agent ────────────────────────────
    managed = list(serea_agent.managed_platforms or [])
    if 'facebook' not in managed:
        managed.append('facebook')
    if ig_account and 'instagram' not in managed:
        managed.append('instagram')
    serea_agent.managed_platforms = managed
    serea_agent.save(update_fields=['managed_platforms'])

    # ── Notify Serea ──────────────────────────────────────────────────────────
    ig_note = f" Instagram (@{ig_account.account_name}) was also connected automatically." if ig_account else ''
    ConversationMessage.objects.create(
        agent=serea_agent,
        sender='system',
        message_text=(
            f"Facebook Page '{page['name']}' connected.{ig_note} "
            "Real-time webhooks are active. I'm ready to start working."
        ),
    )
    return fb_account, ig_account


@console_user_required(login_url='/accounts/login/')
def serea_fb_connect(request):
    """Kick off the Facebook OAuth flow for Serea platform connection."""
    import secrets
    from urllib.parse import urlencode
    from django.conf import settings as dj_settings

    hired_ai = HiredAIEmployee.objects.filter(employer=request.user, is_active=True).first()
    serea_agent = None
    if hired_ai:
        try:
            serea_agent = hired_ai.serea_agent
        except Exception:
            pass

    if not serea_agent:
        messages.warning(request, "Hire a Serea AI employee first before connecting platforms.")
        return redirect('console_admin:hire_ai')

    app_id = dj_settings.FACEBOOK_APP_ID
    if not app_id:
        messages.error(request, "Facebook App ID is not configured. Set FACEBOOK_CLIENT_ID in your environment.")
        return redirect('console_admin:serea_platforms')

    state = secrets.token_urlsafe(32)
    request.session['fb_oauth_state'] = state
    request.session['fb_oauth_agent_id'] = serea_agent.id

    params = urlencode({
        'client_id': app_id,
        'redirect_uri': _get_fb_redirect_uri(request),
        'scope': ','.join([
            'pages_show_list',
            'pages_read_engagement',
            'pages_manage_posts',
            'pages_manage_engagement',
            'pages_messaging',
            'instagram_basic',
            'instagram_manage_comments',
            'instagram_content_publish',
            'instagram_manage_messages',
        ]),
        'state': state,
        'response_type': 'code',
    })
    return redirect(f'https://www.facebook.com/v18.0/dialog/oauth?{params}')


@console_user_required(login_url='/accounts/login/')
def serea_fb_callback(request):
    """Handle the OAuth redirect back from Facebook — exchange code and save pages."""
    import requests as _r
    from django.conf import settings as dj_settings
    from serea.models import SereaAgent

    # ── State check (CSRF guard) ──────────────────────────────────────────────
    if request.GET.get('state', '') != request.session.get('fb_oauth_state', '___'):
        messages.error(request, "OAuth state mismatch — please try connecting again.")
        return redirect('console_admin:serea_platforms')

    error = request.GET.get('error')
    if error:
        messages.error(request, f"Facebook declined access: {request.GET.get('error_description', error)}")
        return redirect('console_admin:serea_platforms')

    code = request.GET.get('code')
    if not code:
        messages.error(request, "No authorization code returned from Facebook.")
        return redirect('console_admin:serea_platforms')

    agent_id = request.session.get('fb_oauth_agent_id')
    try:
        serea_agent = SereaAgent.objects.get(id=agent_id, tenant=request.user)
    except SereaAgent.DoesNotExist:
        messages.error(request, "Session expired — please try connecting again.")
        return redirect('console_admin:serea_platforms')

    # ── Exchange code for user access token ───────────────────────────────────
    token_resp = _r.get(
        'https://graph.facebook.com/v18.0/oauth/access_token',
        params={
            'client_id': dj_settings.FACEBOOK_APP_ID,
            'client_secret': dj_settings.FACEBOOK_APP_SECRET,
            'redirect_uri': _get_fb_redirect_uri(request),
            'code': code,
        },
        timeout=15,
    )
    user_token = token_resp.json().get('access_token') if token_resp.ok else None
    if not user_token:
        messages.error(request, "Could not get access token from Facebook. Please try again.")
        return redirect('console_admin:serea_platforms')

    # ── Get the pages this user manages ───────────────────────────────────────
    pages_resp = _r.get(
        'https://graph.facebook.com/v18.0/me/accounts',
        params={'access_token': user_token, 'fields': 'id,name,access_token,category'},
        timeout=15,
    )
    pages = pages_resp.json().get('data', []) if pages_resp.ok else []

    if not pages:
        messages.warning(
            request,
            "No Facebook Pages found on your account. "
            "Make sure you admin at least one Facebook Page, then try again."
        )
        return redirect('console_admin:serea_platforms')

    if len(pages) == 1:
        fb_account, ig_account = _save_fb_page(serea_agent, pages[0])
        msg = f"'{pages[0]['name']}' connected."
        if ig_account:
            msg += f" Instagram (@{ig_account.account_name}) was detected and connected automatically."
        messages.success(request, msg)
        _clear_fb_session(request)
        return redirect('console_admin:serea_platforms')

    # Multiple pages — store ONLY id/name in session; keep user_token to re-fetch
    # page tokens on selection (never store page access_tokens in the session).
    request.session['fb_pages_pending'] = [{'id': p['id'], 'name': p['name']} for p in pages]
    request.session['fb_user_token'] = user_token
    page_display = [{'id': p['id'], 'name': p['name']} for p in pages]
    return render(request, 'console_admin/fb_page_select.html', {
        'pages': page_display,
        'serea_agent': serea_agent,
    })


@console_user_required(login_url='/accounts/login/')
def serea_fb_page_select(request):
    """POST handler for the page-picker screen (shown when the user manages multiple Pages)."""
    from serea.models import SereaAgent

    if request.method != 'POST':
        return redirect('console_admin:serea_platforms')

    page_id = request.POST.get('page_id', '')
    pending_pages = request.session.get('fb_pages_pending', [])
    page_meta = next((p for p in pending_pages if p['id'] == page_id), None)
    if not page_meta:
        messages.error(request, "Invalid page selection.")
        return redirect('console_admin:serea_platforms')

    agent_id = request.session.get('fb_oauth_agent_id')
    try:
        serea_agent = SereaAgent.objects.get(id=agent_id, tenant=request.user)
    except SereaAgent.DoesNotExist:
        messages.error(request, "Session expired — please try connecting again.")
        return redirect('console_admin:serea_platforms')

    # Re-fetch the page access token using the stored user token (never stored in session).
    import requests as _r
    user_token = request.session.get('fb_user_token', '')
    page = dict(page_meta)  # {'id': ..., 'name': ...}
    if user_token:
        pages_resp = _r.get(
            'https://graph.facebook.com/v18.0/me/accounts',
            params={'access_token': user_token, 'fields': 'id,name,access_token,category'},
            timeout=15,
        )
        full_pages = pages_resp.json().get('data', []) if pages_resp.ok else []
        matched = next((p for p in full_pages if p['id'] == page_id), None)
        if matched:
            page = matched

    fb_account, ig_account = _save_fb_page(serea_agent, page)
    msg = f"'{page['name']}' connected."
    if ig_account:
        msg += f" Instagram (@{ig_account.account_name}) was detected and connected automatically."
    messages.success(request, msg)
    _clear_fb_session(request)
    return redirect('console_admin:serea_platforms')


def _clear_fb_session(request):
    for key in ('fb_oauth_state', 'fb_oauth_agent_id', 'fb_pages_pending', 'fb_user_token'):
        request.session.pop(key, None)


# ─── Serea Onboarding Wizard ───────────────────────────────────────────────────

@console_user_required(login_url='/accounts/login/')
def serea_onboarding(request):
    """
    3-step onboarding wizard run once after hiring Serea.
    Step 1: Welcome / intro
    Step 2: Connect Facebook (OAuth)
    Step 3: Business info — manager name, working hours, tone/description
    On finish: marks onboarding_complete=True, sends Serea's first message.
    """
    from serea.models import SocialMediaAccount, ConversationMessage

    hired_ai = HiredAIEmployee.objects.filter(employer=request.user, is_active=True).first()
    serea_agent = None
    if hired_ai:
        try:
            serea_agent = hired_ai.serea_agent
        except Exception:
            serea_agent = None

    if not serea_agent:
        return redirect('console_admin:hire_ai')

    # Already done — skip to my_ai
    if serea_agent.onboarding_complete:
        return redirect('console_admin:my_ai')

    step = int(request.GET.get('step', 1))

    if request.method == 'POST':
        posted_step = int(request.POST.get('step', 1))

        if posted_step == 3:
            # Save business info and complete onboarding
            manager_name = request.POST.get('manager_name', '').strip()
            description = request.POST.get('description', '').strip()
            tone = request.POST.get('tone', '').strip()

            if manager_name:
                serea_agent.manager_name = manager_name

            hours_start = request.POST.get('working_hours_start', '').strip()
            hours_end   = request.POST.get('working_hours_end', '').strip()
            if hours_start:
                try:
                    from datetime import time as _time
                    h, m = hours_start.split(':')
                    serea_agent.working_hours_start = _time(int(h), int(m))
                except Exception:
                    pass
            if hours_end:
                try:
                    from datetime import time as _time
                    h, m = hours_end.split(':')
                    serea_agent.working_hours_end = _time(int(h), int(m))
                except Exception:
                    pass

            serea_agent.onboarding_complete = True
            serea_agent.save(update_fields=['manager_name', 'working_hours_start', 'working_hours_end', 'onboarding_complete'])

            # Save business description as a content file if provided
            if description or tone:
                from serea.models import ClientContentFile
                combined = ''
                if tone:
                    combined += f"**Tone & Voice:**\n{tone}\n\n"
                if description:
                    combined += f"**Business Description:**\n{description}"
                ClientContentFile.objects.create(
                    agent=serea_agent,
                    uploaded_by=request.user,
                    title='Business Overview (from onboarding)',
                    content_type='brand_guidelines',
                    source_type='manual_text',
                    manual_text=combined,
                    parsed_content=combined,
                    is_active=True,
                )

            # Serea's first message after onboarding
            manager_greeting = f", {manager_name}" if manager_name else ''
            has_fb = SocialMediaAccount.objects.filter(agent=serea_agent, platform='facebook', is_active=True).exists()
            if has_fb:
                first_msg = (
                    f"Hey{manager_greeting} — all set. I'm online and I've got access to your pages.\n\n"
                    "I'll keep an eye on comments and DMs, flag anything that needs your call, "
                    "and start drafting post ideas when you're ready. "
                    "Just message me here whenever you need anything — I work like a real team member, "
                    "not a chatbot.\n\nWhat would you like me to start with?"
                )
            else:
                first_msg = (
                    f"Hey{manager_greeting} — I'm set up and ready.\n\n"
                    "I still need access to your social media accounts before I can start working. "
                    "You can connect them any time from [Platform Connections](/platforms/).\n\n"
                    "Once that's done, I'll handle moderation, content, DMs, and daily briefings — "
                    "just like a regular employee. Message me any time."
                )
            ConversationMessage.objects.create(
                agent=serea_agent, sender='serea', message_text=first_msg
            )

            messages.success(request, f"Welcome to the team! {serea_agent.hired_employee.ai_name if serea_agent.hired_employee else 'Serea'} is ready.")
            return redirect('console_admin:my_ai')

        # Steps 1 and 2 just advance
        from django.urls import reverse
        return redirect(f"{reverse('console_admin:serea_onboarding')}?step={posted_step + 1}")

    has_fb = SocialMediaAccount.objects.filter(agent=serea_agent, platform='facebook', is_active=True).exists()
    return render(request, 'console_admin/serea_onboarding.html', {
        'step': step,
        'serea_agent': serea_agent,
        'hired_ai': hired_ai,
        'has_fb': has_fb,
    })


# ─── Serea Platform Connections ────────────────────────────────────────────────

@console_user_required(login_url='/accounts/login/')
def serea_platforms(request):
    """
    Platform Connections — the client connects Facebook, Instagram, and LinkedIn here.
    Serea uses these credentials to moderate, post, and handle DMs on all three platforms.
    """
    from serea.models import SocialMediaAccount, ConversationMessage

    hired_ai = HiredAIEmployee.objects.filter(employer=request.user, is_active=True).first()
    serea_agent = None
    if hired_ai:
        try:
            serea_agent = hired_ai.serea_agent
        except Exception:
            serea_agent = None

    if not serea_agent:
        messages.warning(request, "You need to hire a Serea AI employee before connecting platforms.")
        return redirect('console_admin:hire_ai')

    connected_accounts = SocialMediaAccount.objects.filter(agent=serea_agent, is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Connect a platform account (manual form fallback) ─────────────────
        if action == 'connect':
            platform = request.POST.get('platform')
            account_name = request.POST.get('account_name', '').strip()
            account_id = request.POST.get('account_id', '').strip()
            access_token = request.POST.get('access_token', '').strip()

            if not all([platform, account_name, account_id, access_token]):
                messages.error(request, "Fill in all required fields before connecting.")
                return redirect('console_admin:serea_platforms')

            extra_creds = {}

            existing_count = SocialMediaAccount.objects.filter(agent=serea_agent, platform=platform).count()
            SocialMediaAccount.objects.filter(agent=serea_agent, platform=platform).delete()
            obj = SocialMediaAccount.objects.create(
                agent=serea_agent,
                platform=platform,
                account_name=account_name,
                account_id=account_id,
                access_token=access_token,
                status='connected',
                is_active=True,
            )
            verb = 'updated' if existing_count else 'connected'
            messages.success(
                request,
                f"{obj.get_platform_display()} ({account_name}) {verb}. Serea now has access."
            )
            ConversationMessage.objects.create(
                agent=serea_agent,
                sender='system',
                message_text=(
                    f"Your {obj.get_platform_display()} account '{account_name}' "
                    f"(ID: {account_id}) has been connected."
                ),
            )
            return redirect('console_admin:serea_platforms')

        # ── Disconnect a platform ─────────────────────────────────────────────
        elif action == 'disconnect':
            platform = request.POST.get('platform')
            acc = SocialMediaAccount.objects.filter(agent=serea_agent, platform=platform).first()
            label = acc.get_platform_display() if acc else platform
            SocialMediaAccount.objects.filter(agent=serea_agent, platform=platform).update(is_active=False)
            messages.success(request, f"{label} disconnected.")
            return redirect('console_admin:serea_platforms')


    accounts_by_platform = {a.platform: a for a in connected_accounts}
    return render(request, 'console_admin/serea_platforms.html', {
        'serea_agent': serea_agent,
        'facebook_account': accounts_by_platform.get('facebook'),
        'instagram_account': accounts_by_platform.get('instagram'),
        'tiktok_account': accounts_by_platform.get('tiktok'),
        # LinkedIn removed from active posting — shown as view-only if previously connected
        'linkedin_account': accounts_by_platform.get('linkedin'),
        'linkedin_deprecated': True,
    })


# ─── Serea Workspace (Content Knowledge Base) ──────────────────────────────────

@console_user_required(login_url='/accounts/login/')
def serea_workspace(request):
    """
    Workspace — the client feeds Serea business knowledge here.
    Serea reads this content to write on-brand posts, reply to comments/DMs,
    and understand what kinds of comments to flag or delete.

    Supports three input methods:
      1. CSV file upload  (parsed into plaintext)
      2. Manual text entry
      3. Google Drive link (Serea accesses it via her Drive tool)
    """
    import csv
    import io
    from serea.models import ClientContentFile

    hired_ai = HiredAIEmployee.objects.filter(employer=request.user, is_active=True).first()
    serea_agent = None
    if hired_ai:
        try:
            serea_agent = hired_ai.serea_agent
        except Exception:
            serea_agent = None

    if not serea_agent:
        messages.warning(request, "You need to hire a Serea AI employee before uploading content.")
        return redirect('console_admin:hire_ai')

    content_files = ClientContentFile.objects.filter(agent=serea_agent).order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action', 'add')

        if action == 'add':
            title = request.POST.get('title', '').strip()
            content_type = request.POST.get('content_type', 'other')
            description = request.POST.get('description', '').strip()
            source_type = request.POST.get('source_type', 'manual_text')

            if not title:
                messages.error(request, "Please provide a title for this content.")
                return redirect('console_admin:serea_workspace')

            cf = ClientContentFile(
                agent=serea_agent,
                uploaded_by=request.user,
                title=title,
                content_type=content_type,
                description=description,
                source_type=source_type,
            )

            if source_type == 'csv_upload':
                uploaded_file = request.FILES.get('file')
                if not uploaded_file:
                    messages.error(request, "Please select a CSV file to upload.")
                    return redirect('console_admin:serea_workspace')
                cf.file = uploaded_file

                # Parse CSV into plaintext for Serea's context
                try:
                    decoded = uploaded_file.read().decode('utf-8', errors='ignore')
                    reader = csv.DictReader(io.StringIO(decoded))
                    rows = list(reader)
                    if rows:
                        lines = []
                        for row in rows[:200]:   # cap at 200 rows
                            lines.append('  |  '.join(f"{k}: {v}" for k, v in row.items() if v))
                        cf.parsed_content = '\n'.join(lines)
                    else:
                        cf.parsed_content = decoded[:5000]
                except Exception as exc:
                    messages.warning(request, f"CSV parsed with issues: {exc}. Content saved as-is.")
                    cf.parsed_content = ''

            elif source_type == 'manual_text':
                manual_text = request.POST.get('manual_text', '').strip()
                if not manual_text:
                    messages.error(request, "Please enter some content in the text area.")
                    return redirect('console_admin:serea_workspace')
                cf.manual_text = manual_text

            elif source_type == 'google_drive':
                drive_url = request.POST.get('drive_url', '').strip()
                if not drive_url:
                    messages.error(request, "Please enter a Google Drive URL.")
                    return redirect('console_admin:serea_workspace')
                cf.drive_url = drive_url

            cf.save()
            messages.success(
                request,
                f'"{title}" added to Serea\'s knowledge base. '
                'She will use this when writing posts and responding to comments.'
            )

            # Post a notification in the Serea chat
            from serea.models import ConversationMessage
            ConversationMessage.objects.create(
                agent=serea_agent,
                sender='system',
                message_text=(
                    f"[Knowledge update] New content added: "
                    f"[{cf.get_content_type_display()}] \"{title}\". "
                    "I'll use this going forward."
                ),
            )
            return redirect('console_admin:serea_workspace')

        elif action == 'toggle':
            file_id = request.POST.get('file_id')
            cf = get_object_or_404(ClientContentFile, id=file_id, agent=serea_agent)
            cf.is_active = not cf.is_active
            cf.save(update_fields=['is_active'])
            state = 'enabled' if cf.is_active else 'disabled'
            messages.success(request, f'"{cf.title}" {state}.')
            return redirect('console_admin:serea_workspace')

        elif action == 'delete':
            file_id = request.POST.get('file_id')
            cf = get_object_or_404(ClientContentFile, id=file_id, agent=serea_agent)
            title = cf.title
            cf.delete()
            messages.success(request, f'"{title}" removed from the knowledge base.')
            return redirect('console_admin:serea_workspace')

    return render(request, 'console_admin/serea_workspace.html', {
        'serea_agent': serea_agent,
        'content_files': content_files,
        'content_type_choices': ClientContentFile.CONTENT_TYPE_CHOICES,
        'source_type_choices': ClientContentFile.SOURCE_CHOICES,
        'active_count': content_files.filter(is_active=True).count(),
    })


# ─── Manage / Fire AI Employee ─────────────────────────────────────────────────

@console_user_required(login_url='/accounts/login/')
def manage_ai(request, ai_id):
    """Settings page for a single hired AI employee: rename, change model, pause/resume."""
    from serea.models import SereaAgent

    hired_ai = get_object_or_404(HiredAIEmployee, id=ai_id, employer=request.user)

    try:
        serea_agent = hired_ai.serea_agent
    except Exception:
        serea_agent = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'rename':
            new_name = request.POST.get('ai_name', '').strip()
            if new_name:
                hired_ai.ai_name = new_name
                hired_ai.save(update_fields=['ai_name'])
                messages.success(request, f'Renamed to "{new_name}".')
            return redirect('console_admin:manage_ai', ai_id=ai_id)

        elif action == 'update_employee_settings' and serea_agent:
            manager_name = request.POST.get('manager_name', '').strip()
            serea_agent.manager_name = manager_name

            hours_start = request.POST.get('working_hours_start', '').strip()
            hours_end   = request.POST.get('working_hours_end', '').strip()
            if hours_start:
                try:
                    from datetime import time as _time
                    h, m = hours_start.split(':')
                    serea_agent.working_hours_start = _time(int(h), int(m))
                except Exception:
                    pass
            else:
                serea_agent.working_hours_start = None
            if hours_end:
                try:
                    from datetime import time as _time
                    h, m = hours_end.split(':')
                    serea_agent.working_hours_end = _time(int(h), int(m))
                except Exception:
                    pass
            else:
                serea_agent.working_hours_end = None

            serea_agent.save(update_fields=['manager_name', 'working_hours_start', 'working_hours_end'])
            messages.success(request, 'Employee settings saved.')
            return redirect('console_admin:manage_ai', ai_id=ai_id)

        elif action == 'pause' and hired_ai.is_active:
            hired_ai.is_active = False
            hired_ai.save(update_fields=['is_active'])
            messages.success(request, f'{hired_ai.ai_name} has been paused.')
            return redirect('console_admin:manage_ai', ai_id=ai_id)

        elif action == 'resume' and not hired_ai.is_active:
            hired_ai.is_active = True
            hired_ai.save(update_fields=['is_active'])
            messages.success(request, f'{hired_ai.ai_name} is back online.')
            return redirect('console_admin:manage_ai', ai_id=ai_id)

        return redirect('console_admin:manage_ai', ai_id=ai_id)

    # Group model choices for optgroups
    def _grouped(choices):
        groups = [
            ('NeuroLinkIt (Home Server)', []),
            ('Groq (Cloud)', []),
            ('OpenRouter FREE', []),
            ('OpenRouter (Paid)', []),
            ('OpenAI', []),
        ]
        for val, label in choices:
            if val.startswith('neurolinkit/'):
                groups[0][1].append((val, label))
            elif '/' not in val:
                groups[1][1].append((val, label))
            elif ':free' in val:
                groups[2][1].append((val, label))
            elif val.startswith('gpt-'):
                groups[4][1].append((val, label))
            else:
                groups[3][1].append((val, label))
        return [(g, items) for g, items in groups if items]

    token_limit = hired_ai.tier.token_limit if hired_ai.tier else 0
    token_pct = 0
    if token_limit > 0:
        token_pct = min(100, round((hired_ai.tokens_used_this_month / token_limit) * 100))

    return render(request, 'console_admin/manage_ai.html', {
        'hired_ai': hired_ai,
        'serea_agent': serea_agent,
        'model_choices_grouped': _grouped(SereaAgent.AI_MODEL_CHOICES),
        'token_pct': token_pct,
        'token_limit': token_limit,
    })


@console_user_required(login_url='/accounts/login/')
def fire_ai(request, ai_id):
    """Permanently deactivate an AI employee (with confirmation step)."""
    hired_ai = get_object_or_404(HiredAIEmployee, id=ai_id, employer=request.user)

    if request.method == 'POST':
        if request.POST.get('confirm') == 'yes':
            name = hired_ai.ai_name
            hired_ai.is_active = False
            hired_ai.save(update_fields=['is_active'])
            messages.success(
                request,
                f'{name} has been deactivated. All history is preserved — '
                'you can hire a new AI employee from the marketplace.'
            )
            return redirect('console_admin:hire_ai')
        return redirect('console_admin:manage_ai', ai_id=ai_id)

    return render(request, 'console_admin/fire_ai.html', {'hired_ai': hired_ai})


# ─── Daily Reports ─────────────────────────────────────────────────────────────

import logging as _logging
_report_log = _logging.getLogger(__name__)

@console_user_required(login_url='/accounts/login/')
def daily_reports(request):
    """List all daily reports for the client's Serea agent."""
    from serea.models import DailyReport

    hired_ai = HiredAIEmployee.objects.filter(employer=request.user, is_active=True).first()
    serea_agent = None
    reports = []

    if hired_ai:
        try:
            serea_agent = hired_ai.serea_agent
        except Exception:
            pass

    if serea_agent:
        reports = DailyReport.objects.filter(agent=serea_agent).prefetch_related('items')

    return render(request, 'console_admin/daily_reports.html', {
        'serea_agent': serea_agent,
        'reports': reports,
        'pending_count': sum(1 for r in reports if r.status == 'pending'),
    })


@console_user_required(login_url='/accounts/login/')
def daily_report_detail(request, report_id):
    """
    View a single daily report.
    Clients can flag individual items, choose an action (reassign/fix manually),
    add overall feedback, and send it all back to Serea in one click.
    """
    from serea.models import DailyReport, DailyReportItem, ConversationMessage
    from django.utils import timezone

    hired_ai = HiredAIEmployee.objects.filter(employer=request.user, is_active=True).first()
    if not hired_ai:
        return redirect('/my-ai/')
    try:
        serea_agent = hired_ai.serea_agent
    except Exception:
        return redirect('/my-ai/')

    report = get_object_or_404(DailyReport, id=report_id, agent=serea_agent)

    if request.method == 'POST':
        action = request.POST.get('action')

        # ── Flag / unflag a single item ───────────────────────────────────────
        if action == 'flag_item':
            item_id = request.POST.get('item_id')
            flag_reason = request.POST.get('flag_reason', '').strip()
            client_action = request.POST.get('client_action', 'none')
            try:
                item = DailyReportItem.objects.get(id=item_id, report=report)
                item.is_flagged = True
                item.flag_reason = flag_reason
                item.client_action = client_action
                item.save(update_fields=['is_flagged', 'flag_reason', 'client_action'])

                # Immediately act on the linked task if one exists
                if item.linked_task:
                    if client_action == 'reassign':
                        item.linked_task.status = 'todo'
                        item.linked_task.progress_notes = (
                            f"Reassigned by client on {timezone.now().date()}"
                            + (f": {flag_reason}" if flag_reason else "")
                        )
                        item.linked_task.save(update_fields=['status', 'progress_notes'])
                    elif client_action == 'fixed_manually':
                        item.linked_task.status = 'done'
                        item.linked_task.result = (
                            f"Fixed manually by client on {timezone.now().date()}"
                            + (f": {flag_reason}" if flag_reason else "")
                        )
                        item.linked_task.completed_at = timezone.now()
                        item.linked_task.save(update_fields=['status', 'result', 'completed_at'])

            except DailyReportItem.DoesNotExist:
                pass
            return redirect(f'/reports/{report_id}/')

        elif action == 'unflag_item':
            item_id = request.POST.get('item_id')
            try:
                item = DailyReportItem.objects.get(id=item_id, report=report)
                item.is_flagged = False
                item.flag_reason = ''
                item.client_action = 'none'
                item.save(update_fields=['is_flagged', 'flag_reason', 'client_action'])
            except DailyReportItem.DoesNotExist:
                pass
            return redirect(f'/reports/{report_id}/')

        # ── Send all flagged items + feedback to Serea ────────────────────────
        elif action == 'send_feedback':
            feedback = request.POST.get('client_feedback', '').strip()
            flagged_items = list(report.items.filter(is_flagged=True).select_related('linked_task'))

            if not flagged_items and not feedback:
                messages.warning(request, "Flag at least one item or add feedback before sending.")
                return redirect(f'/reports/{report_id}/')

            # Build a natural-language message Serea can act on
            lines = ["Hey, I went through today's report and flagged a few things for you:"]
            for item in flagged_items:
                lines.append(f"\n• **{item.title}**")
                if item.flag_reason:
                    lines.append(f"  Issue: {item.flag_reason}")
                action_label = {
                    'reassign': "Please redo / handle this",
                    'fixed_manually': "I fixed it myself — just a heads-up",
                    'none': "Take a look at this",
                }.get(item.client_action, '')
                if action_label:
                    lines.append(f"  Action needed: {action_label}")

            if feedback:
                lines.append(f"\nOverall notes: {feedback}")

            msg_text = '\n'.join(lines)

            # Post message from client side
            ConversationMessage.objects.create(
                agent=serea_agent,
                sender=request.user.email,
                message_text=msg_text,
            )

            # Trigger Serea's reply
            try:
                from serea.logic import SereaBrain
                brain = SereaBrain(agent_id=serea_agent.id)
                reply = brain.chat(msg_text)
                ConversationMessage.objects.create(
                    agent=serea_agent,
                    sender='serea',
                    message_text=reply,
                )
            except Exception as exc:
                _report_log.warning("daily_report send_feedback: SereaBrain error: %s", exc)

            # Update report status
            report.client_feedback = feedback
            report.status = 'has_issues'
            report.reviewed_at = timezone.now()
            report.reviewed_by = request.user
            report.feedback_sent_at = timezone.now()
            report.save(update_fields=[
                'client_feedback', 'status', 'reviewed_at', 'reviewed_by', 'feedback_sent_at'
            ])

            messages.success(request, "Feedback sent to Serea — she'll get on it.")
            return redirect(f'/reports/{report_id}/')

        # ── Approve the report ────────────────────────────────────────────────
        elif action == 'approve':
            report.status = 'approved'
            report.reviewed_at = timezone.now()
            report.reviewed_by = request.user
            report.save(update_fields=['status', 'reviewed_at', 'reviewed_by'])
            messages.success(request, "Report approved.")
            return redirect('/reports/')

    items = report.items.select_related('linked_task').all()
    return render(request, 'console_admin/daily_report_detail.html', {
        'report': report,
        'items': items,
        'serea_agent': serea_agent,
        'flagged_count': report.flagged_count,
    })


# ─── Notification Center ───────────────────────────────────────────────────────

@console_user_required(login_url='/accounts/login/')
def notifications_list(request):
    """List all in-app notifications for the current user, newest first."""
    from workspace_admin.models import UserNotification
    from django.core.paginator import Paginator

    notifs_qs = UserNotification.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(notifs_qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Auto-mark all as read when the list is opened
    notifs_qs.filter(is_read=False).update(is_read=True)

    return render(request, 'console_admin/notifications_list.html', {
        'page_obj': page_obj,
    })


@console_user_required(login_url='/accounts/login/')
def notifications_mark_read(request):
    """AJAX/POST: mark a single notification or all notifications as read."""
    from workspace_admin.models import UserNotification
    if request.method == 'POST':
        notif_id = request.POST.get('id')
        if notif_id:
            UserNotification.objects.filter(id=notif_id, user=request.user).update(is_read=True)
        else:
            UserNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'console_admin:notifications_list'))


# ─── Data Exports ──────────────────────────────────────────────────────────────

@console_user_required(login_url='/accounts/login/')
def export_moderation_logs_csv(request):
    """Export Serea moderation logs for the current user's agent as CSV."""
    from serea.models import ModerationLog
    from core.exports import serea_moderation_csv
    hired_ai = HiredAIEmployee.objects.filter(employer=request.user, is_active=True).first()
    logs = []
    if hired_ai:
        try:
            serea_agent = hired_ai.serea_agent
            logs = ModerationLog.objects.filter(agent=serea_agent).order_by('-created_at')[:500]
        except Exception:
            pass
    return serea_moderation_csv(logs)

# ─── Hybrid Onboarding ────────────────────────────────────────────────────────

@console_user_required(login_url='/accounts/login/')
def hybrid_onboarding(request):
    """
    The Hybrid Onboarding interface. 
    Shows a 6-question AI onboarding interview to configure the workspace automatically.
    """
    # 1. Veritas KYB Gate
    try:
        from modules.veritas.models import ClientApplication
        kyb_app = ClientApplication.objects.filter(user=request.user).first()
        if not kyb_app or kyb_app.status != 'approved':
            if not kyb_app:
                return redirect('console_admin:veritas_user:kyb_apply')
            return redirect('console_admin:veritas_user:kyb_pending')
    except ImportError:
        pass

    from hub.models import ModuleCatalog, BUSINESS_TYPES, BASIC_MODULE_IDS, INDUSTRY_MODULE_PRIORITY
    from workspace_admin.models import AIEmployeeTier
    from agents.models import AgentCatalog
    from public_site.views import EXCHANGE_RATES, CURRENCY_SYMBOLS
    import json

    modules = ModuleCatalog.objects.filter(is_available=True)
    ai_tiers = AIEmployeeTier.objects.all().order_by('monthly_price_usd')
    agents = AgentCatalog.objects.filter(is_active=True)

    negotiated_package = request.session.pop('negotiated_package', None)

    return render(request, 'console_admin/hybrid_onboarding.html', {
        'modules': modules,
        'ai_tiers': ai_tiers,
        'agents': agents,
        'business_types': BUSINESS_TYPES,
        'basic_module_ids': json.dumps(BASIC_MODULE_IDS),
        'industry_module_priority': json.dumps(INDUSTRY_MODULE_PRIORITY),
        'exchange_rates': json.dumps(EXCHANGE_RATES),
        'currency_symbols': json.dumps(CURRENCY_SYMBOLS),
        'negotiated_package': json.dumps(negotiated_package) if negotiated_package else 'null',
    })

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json

@csrf_exempt
@console_user_required(login_url='/accounts/login/')
def api_onboarding_chat(request):
    """
    AJAX endpoint for the onboarding AI assistant.
    Expects JSON: {"messages": [{"role": "user", "content": "..."}]}
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            messages = data.get('messages', [])
            
            from agents.onboarding_agent import get_onboarding_chat_response
            response_data = get_onboarding_chat_response(messages)
            
            return JsonResponse(response_data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)

@console_user_required(login_url='/accounts/login/')
def process_onboarding_checkout(request):
    """
    Processes the onboarding interview answers and customised package, then provisions the workspace.
    """
    if request.method == 'POST':
        business_name = request.POST.get('business_name', 'My Business').strip()
        business_type = request.POST.get('business_type', 'business').strip()
        main_challenge = request.POST.get('main_challenge', 'getting_leads').strip()
        team_size = request.POST.get('team_size', 'Just me').strip()
        platforms = request.POST.getlist('platforms')
        language = request.POST.get('language', 'English').strip()
        payment_preference = request.POST.get('payment_preference', 'Stripe').strip()

        answers = {
            'business_type': business_type,
            'main_challenge': main_challenge,
            'team_size': team_size,
            'platforms': platforms,
            'language': language,
            'payment_preference': payment_preference,
        }

        from hub.models import BusinessInstance, TenantModule, ModuleCatalog
        from workspace_admin.models import HiredAIEmployee, Subscription, AIEmployeeTier
        from django.utils import timezone
        from datetime import timedelta
        from hub.views import _unique_slug
        from hub.dashboard_configurator import DashboardConfigurator
        from agents.models import AgentCatalog
        
        # 1. Create Business
        slug = _unique_slug(business_name)
        business, created = BusinessInstance.objects.get_or_create(
            owner=request.user,
            defaults={
                'name': business_name,
                'slug': slug,
                'business_type': business_type
            }
        )
        
        # 2. Provision custom modules if specified, else basic modules plus priority business modules
        custom_modules = request.POST.getlist('custom_modules')
        custom_agents = request.POST.getlist('custom_agents')
        
        agent_tiers = {}
        for key, val in request.POST.items():
            if key.startswith('agent_tier_'):
                agent_slug = key[len('agent_tier_'):]
                agent_tiers[agent_slug] = val

        if not custom_modules:
            from hub.models import BASIC_MODULE_IDS, INDUSTRY_MODULE_PRIORITY
            priority_modules = INDUSTRY_MODULE_PRIORITY.get(business_type, [])
            custom_modules = BASIC_MODULE_IDS + priority_modules

        for mod_id in custom_modules:
            try:
                module = ModuleCatalog.objects.get(module_id=mod_id)
                TenantModule.objects.get_or_create(
                    business=business,
                    module=module,
                    defaults={'tier': 'free', 'is_active': True}
                )
            except ModuleCatalog.DoesNotExist:
                continue

        # Create a BusinessEmployee for the owner as CEO
        from hub.models import BusinessEmployee
        from django.core.exceptions import ObjectDoesNotExist
        try:
            BusinessEmployee.objects.get_or_create(
                business=business,
                user=request.user,
                defaults={
                    'name': request.user.get_full_name() or request.user.email,
                    'email': request.user.email,
                    'role': 'ceo',
                }
            )
        except Exception:
            pass
            
        # 3. Trigger AI dashboard configuration
        configurator = DashboardConfigurator()
        configurator.configure(business, answers,
                               custom_agents=custom_agents if custom_agents else None,
                               agent_tiers=agent_tiers)
            
        from django.contrib import messages
        messages.success(request, f"Welcome! Your workspace '{business.name}' is ready.")
        return redirect('console_admin:dashboard')
        
    return redirect('console_admin:hybrid_onboarding')


@csrf_exempt
@console_user_required(login_url='/accounts/login/')
def skip_onboarding_book(request):
    """
    Endpoint for client to skip onboarding wizard and book a demo.
    Registers a booking_calendar.models.Appointment and provisions a basic freemium workspace.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    import json
    from django.http import JsonResponse
    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    booking_date = data.get('date')
    booking_time = data.get('time')
    booking_notes = data.get('notes', '').strip()

    if not booking_date or not booking_time:
        return JsonResponse({'success': False, 'error': 'Preferred date and time are required.'}, status=400)

    from booking_calendar.models import Appointment
    from hub.models import BusinessInstance, DashboardConfig
    from hub.views import _unique_slug
    from hub.dashboard_configurator import DashboardConfigurator
    from django.contrib import messages

    # 1. Create Appointment
    appointment = Appointment.objects.create(
        client_name=request.user.get_full_name() or request.user.email,
        client_email=request.user.email,
        service_type='bengalbound_demo',
        date=booking_date,
        time=booking_time,
        notes=booking_notes,
    )

    # 2. Provision default BusinessInstance
    business_name = f"{request.user.email.split('@')[0]}'s Workspace"
    slug = _unique_slug(business_name)
    
    business, created = BusinessInstance.objects.get_or_create(
        owner=request.user,
        defaults={
            'name': business_name,
            'slug': slug,
            'business_type': 'business'
        }
    )

    # 3. Create CEO employee profile if missing
    from hub.models import BusinessEmployee
    try:
        BusinessEmployee.objects.get_or_create(
            business=business,
            user=request.user,
            defaults={
                'name': request.user.get_full_name() or request.user.email,
                'email': request.user.email,
                'role': 'ceo',
            }
        )
    except Exception:
        pass

    # 4. Trigger configuration
    answers = {
        'business_type': 'business',
        'main_challenge': 'getting_leads',
        'team_size': 'Just me',
        'platforms': [],
        'language': 'English',
        'payment_preference': 'Stripe',
    }
    
    configurator = DashboardConfigurator()
    configurator.configure(business, answers)

    # Ensure DashboardConfig is marked as configured to prevent further redirect loops
    db_config = DashboardConfig.objects.filter(business=business).first()
    if db_config:
        db_config.is_configured = True
        db_config.save()

    messages.success(request, f"Onboarding skipped. Your demo is booked for {booking_date} at {booking_time}!")
    
    from django.urls import reverse
    return JsonResponse({
        'success': True,
        'redirect_url': reverse('console_admin:dashboard')
    })


@csrf_exempt
@console_user_required(login_url='/accounts/login/')
def modify_dashboard_layout(request):
    """
    AJAX endpoint to modify dashboard layout/theme via natural language.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            request_text = data.get('request', '').strip()
            if not request_text:
                return JsonResponse({"success": False, "message": "Request text cannot be empty."})
            
            from hub.models import BusinessInstance
            business = BusinessInstance.objects.filter(owner=request.user, is_active=True).first()
            if not business:
                return JsonResponse({"success": False, "message": "Business not found."})

            from hub.dashboard_configurator import DashboardAIModifier
            modifier = DashboardAIModifier()
            result = modifier.modify(business, request_text)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)
    return JsonResponse({"success": False, "message": "Invalid method"}, status=400)
