from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from .decorators import workspace_admin_required
from .models import HiredAIEmployee, WaaSSite, TrafficLog, Order, Coupon, UserNotification, Subscription
from serea.models import SereaAgent
from public_site.models import ContactInquiry, ConsultationBooking, BlogPost, BlogComment
from console_admin.models import WorkspaceProject, SupportTicket
from community_forum.models import ForumTopic, ForumPost

User = get_user_model()

# ─── Dashboard ────────────────────────────────────────────────────────────────

@workspace_admin_required
def dashboard(request):
    """Command-center overview for Workspace Admins."""
    context = {
        'active_agents': HiredAIEmployee.objects.filter(is_active=True).count(),
        'active_sites': WaaSSite.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'pending_inquiries': ContactInquiry.objects.filter(is_resolved=False).count(),
        'open_tickets': SupportTicket.objects.filter(status='open').count(),
        'recent_orders': Order.objects.all().order_by('-created_at')[:5],
        'traffic_logs': TrafficLog.objects.all().order_by('-timestamp')[:5],
    }
    return render(request, 'workspace_admin/dashboard.html', context)

# ─── AI Oversight ─────────────────────────────────────────────────────────────

@workspace_admin_required
def ai_oversight(request):
    """Monitor all Serea agents across all clients; activate/deactivate."""
    if request.method == 'POST':
        ai_id = request.POST.get('ai_id')
        action = request.POST.get('action')
        ai = get_object_or_404(HiredAIEmployee, id=ai_id)
        ai.is_active = (action == 'activate')
        ai.save()
        messages.success(request, f"{ai.ai_name} {'activated' if ai.is_active else 'deactivated'}.")
        return redirect('workspace_admin:ai_oversight')

    all_agents_qs = HiredAIEmployee.objects.select_related('employer', 'tier').order_by('-hired_at')

    serea_map = {sa.hired_employee_id: sa for sa in SereaAgent.objects.select_related('tenant').all()}
    for ai in all_agents_qs:
        ai.serea = serea_map.get(ai.id)

    paginator = Paginator(all_agents_qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    serea_agents_total = SereaAgent.objects.count()
    serea_active = SereaAgent.objects.filter(status__in=['idle', 'working']).count()

    return render(request, 'workspace_admin/ai_oversight.html', {
        'all_agents': page_obj,
        'page_obj': page_obj,
        'serea_agents_total': serea_agents_total,
        'serea_active': serea_active,
    })

# ─── Project Control ──────────────────────────────────────────────────────────

@workspace_admin_required
def project_control(request):
    """View and update all client custom build projects."""
    if request.method == 'POST':
        project_id = request.POST.get('project_id')
        new_status = request.POST.get('status')
        milestone = request.POST.get('milestone_note', '')
        project = get_object_or_404(WorkspaceProject, id=project_id)
        project.status = new_status
        if milestone:
            project.description = f"{project.description}\n\n[Milestone — {new_status}]: {milestone}"
        project.save()
        messages.success(request, f"Project '{project.name}' updated to {project.get_status_display()}.")
        return redirect('project_control')

    all_projects_qs = WorkspaceProject.objects.select_related('client').order_by('-created_at')
    paginator = Paginator(all_projects_qs, 25)
    page_obj = paginator.get_page(request.GET.get('page'))

    status_choices = WorkspaceProject.STATUS_CHOICES
    return render(request, 'workspace_admin/project_control.html', {
        'all_projects': page_obj,
        'page_obj': page_obj,
        'status_choices': status_choices,
    })

# ─── CRM & Support ────────────────────────────────────────────────────────────

@workspace_admin_required
def crm_support(request):
    """Manage all inquiries, support tickets, and consultation calendar."""
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'reply_ticket':
            ticket_id = request.POST.get('ticket_id')
            new_status = request.POST.get('status')
            ticket = get_object_or_404(SupportTicket, id=ticket_id)
            ticket.status = new_status
            ticket.save()
            # Notify the client
            UserNotification.objects.create(
                user=ticket.client,
                title=f"Ticket #{ticket.id} Updated",
                message=f"Your support ticket '{ticket.subject}' has been updated to: {ticket.get_status_display()}."
            )
            messages.success(request, f"Ticket #{ticket_id} updated.")
        elif action == 'resolve_inquiry':
            inquiry_id = request.POST.get('inquiry_id')
            ContactInquiry.objects.filter(id=inquiry_id).update(is_resolved=True)
            messages.success(request, "Inquiry marked as resolved.")
        elif action == 'confirm_consult':
            consult_id = request.POST.get('consult_id')
            ConsultationBooking.objects.filter(id=consult_id).update(is_confirmed=True)
            messages.success(request, "Consultation confirmed.")
        return redirect('crm_support')

    tickets_qs = SupportTicket.objects.select_related('client').order_by('-created_at')
    paginator = Paginator(tickets_qs, 20)
    tickets_page = paginator.get_page(request.GET.get('page'))

    inquiries = ContactInquiry.objects.order_by('-created_at')[:50]
    consultations = ConsultationBooking.objects.order_by('preferred_date')[:50]

    return render(request, 'workspace_admin/crm_support.html', {
        'tickets': tickets_page,
        'page_obj': tickets_page,
        'inquiries': inquiries,
        'consultations': consultations,
    })

# ─── Data & Traffic ───────────────────────────────────────────────────────────

@workspace_admin_required
def data_traffic(request):
    """Monitor site traffic, IP/user-agent logs, consent data, and all orders."""
    traffic_logs = TrafficLog.objects.order_by('-timestamp')[:200]
    all_orders = Order.objects.select_related('client').order_by('-created_at')
    subscriptions = Subscription.objects.select_related('client', 'tier').order_by('-started_at')
    all_users = User.objects.order_by('-date_joined')
    return render(request, 'workspace_admin/data_traffic.html', {
        'traffic_logs': traffic_logs,
        'all_orders': all_orders,
        'subscriptions': subscriptions,
        'all_users': all_users,
    })

@workspace_admin_required
def manage_user(request):
    """Handle user account creation, deactivation, or deletion across the workspace."""
    # Determine what roles the current user can create
    user_role = request.user.role
    allowed_roles = []
    if user_role == 'super_admin' or request.user.is_superuser:
        allowed_roles = ['manager', 'employee', 'contractor', 'auditor']
    elif user_role == 'manager':
        allowed_roles = ['employee', 'contractor', 'auditor']

    # List of all users in the workspace (exclude clients unless super_admin?)
    # Let's show all staff members.
    staff_users = User.objects.filter(role__in=['super_admin', 'manager', 'employee', 'contractor', 'auditor']).order_by('-date_joined')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_staff':
            if not allowed_roles:
                messages.error(request, "You do not have permission to create staff accounts.")
                return redirect('workspace_admin:manage_user')

            email = request.POST.get('email')
            password = request.POST.get('password')
            first_name = request.POST.get('first_name', '')
            last_name = request.POST.get('last_name', '')
            role = request.POST.get('role')

            if role not in allowed_roles:
                messages.error(request, "You do not have permission to create this role.")
                return redirect('workspace_admin:manage_user')

            if User.objects.filter(email=email).exists():
                messages.error(request, "A user with this email already exists.")
            else:
                new_user = User.objects.create_user(
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=role,
                    is_staff=True # They are staff since they get into the workspace
                )
                messages.success(request, f"Staff account {email} created with role {new_user.get_role_display()}.")

            return redirect('workspace_admin:manage_user')

        # Action: Deactivate/Delete
        user_id = request.POST.get('user_id')
        if user_id:
            if str(user_id) == str(request.user.id):
                messages.error(request, "You cannot modify your own account from this view.")
                return redirect('workspace_admin:manage_user')

            target_user = get_object_or_404(User, id=user_id)

            # Basic permission check: managers shouldn't delete super_admins
            if target_user.role == 'super_admin' and user_role != 'super_admin':
                messages.error(request, "You cannot modify a Super Admin.")
                return redirect('workspace_admin:manage_user')

            if action == 'toggle_active':
                target_user.is_active = not target_user.is_active
                target_user.save()
                status_str = "activated" if target_user.is_active else "deactivated"
                messages.success(request, f"User {target_user.email} has been {status_str}.")
            elif action == 'delete':
                target_user.delete()
                messages.success(request, "User account successfully deleted.")

        return redirect('workspace_admin:manage_user')

    return render(request, 'workspace_admin/manage_user.html', {
        'staff_users': staff_users,
        'allowed_roles': allowed_roles,
        'all_roles_dict': dict(User.ROLE_CHOICES)
    })

# ─── Marketing Management ─────────────────────────────────────────────────────

@workspace_admin_required
def marketing(request):
    """Manage blogs, comments, coupons, and site-wide notifications."""
    blogs = BlogPost.objects.select_related('author').order_by('-created_at')
    pending_comments = BlogComment.objects.filter(is_approved=False).order_by('-created_at')
    coupons = Coupon.objects.order_by('-valid_from')
    notifications = UserNotification.objects.order_by('-created_at')[:20]

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve_comment':
            BlogComment.objects.filter(id=request.POST.get('comment_id')).update(is_approved=True)
            messages.success(request, "Comment approved.")
        elif action == 'publish_blog':
            BlogPost.objects.filter(id=request.POST.get('blog_id')).update(is_published=True)
            messages.success(request, "Blog post published.")
        elif action == 'create_coupon':
            Coupon.objects.create(
                code=request.POST.get('code'),
                discount_percentage=request.POST.get('discount'),
                valid_from=request.POST.get('valid_from'),
                valid_until=request.POST.get('valid_until'),
            )
            messages.success(request, "Coupon created.")
        elif action == 'send_notification':
            user_ids = request.POST.getlist('user_ids')
            title = request.POST.get('notif_title')
            msg = request.POST.get('notif_message')
            target_users = User.objects.filter(id__in=user_ids) if user_ids else User.objects.all()
            UserNotification.objects.bulk_create([
                UserNotification(user=u, title=title, message=msg) for u in target_users
            ])
            messages.success(request, f"Notification sent to {target_users.count()} users.")
        return redirect('marketing')

    return render(request, 'workspace_admin/marketing.html', {
        'blogs': blogs,
        'pending_comments': pending_comments,
        'coupons': coupons,
        'notifications': notifications,
        'all_users': User.objects.all(),
    })

# ─── Project Monitoring Dashboard ─────────────────────────────────────────────

@workspace_admin_required
def project_monitoring(request):
    """
    Admin enters client Domain + API Key (from WaaSSite record).
    Fetches and displays live analytics from their custom application.
    """
    import requests as req
    waas_sites = WaaSSite.objects.select_related('client').filter(is_active=True)
    live_data = None
    selected_site = None
    fetch_error = None

    if request.method == 'POST':
        site_id = request.POST.get('site_id')
        selected_site = get_object_or_404(WaaSSite, id=site_id)
        try:
            resp = req.get(
                f"https://{selected_site.domain}/api/bengalbound/analytics/",
                headers={'X-BengalBound-Key': selected_site.api_key},
                timeout=10
            )
            if resp.status_code == 200:
                live_data = resp.json()
            else:
                fetch_error = f"API returned status {resp.status_code}"
        except Exception as e:
            fetch_error = str(e)

    return render(request, 'workspace_admin/project_monitoring.html', {
        'waas_sites': waas_sites,
        'selected_site': selected_site,
        'live_data': live_data,
        'fetch_error': fetch_error,
    })


# ─── Serea AI Config ──────────────────────────────────────────────────────────

@workspace_admin_required
def serea_agent_config(request):
    """
    Workspace Admin panel for managing Serea agent configurations.
    Allows admins to:
      - Change the AI model used by each agent
      - Set Groq / OpenAI / OpenRouter API keys per agent
      - Set or override the monthly token limit
      - Reset the monthly token counter
      - Change agent status (idle / working / offline)
      - Manually create a SereaAgent for any HiredAIEmployee
    """
    agents = SereaAgent.objects.select_related(
        'tenant', 'hired_employee__tier'
    ).order_by('tenant__email')

    # HiredAIEmployees that don't yet have a SereaAgent
    linked_ids = agents.values_list('hired_employee_id', flat=True)
    unlinked_employees = HiredAIEmployee.objects.filter(
        is_active=True
    ).exclude(id__in=linked_ids).select_related('employer', 'tier')

    if request.method == 'POST':
        action    = request.POST.get('action')

        # ── Create new SereaAgent manually ────────────────────────────────────
        if action == 'create_agent':
            hired_id = request.POST.get('hired_employee_id')
            hired = get_object_or_404(HiredAIEmployee, id=hired_id)
            if not SereaAgent.objects.filter(hired_employee=hired).exists():
                SereaAgent.objects.create(
                    tenant=hired.employer,
                    hired_employee=hired,
                    tier=hired.tier.name if hired.tier else 'intern',
                )
                messages.success(request, f"Serea agent created for {hired.employer.email}.")
            else:
                messages.warning(request, "That employee already has a Serea agent.")
            return redirect('workspace_admin:serea_config')

        # ── Existing agent actions ─────────────────────────────────────────────
        agent_id  = request.POST.get('agent_id')
        agent     = get_object_or_404(SereaAgent, id=agent_id)

        if action == 'update_config':
            ai_model            = request.POST.get('ai_model', '').strip()
            groq_api_key        = request.POST.get('groq_api_key', '').strip()
            openai_api_key      = request.POST.get('openai_api_key', '').strip()
            openrouter_api_key  = request.POST.get('openrouter_api_key', '').strip()
            new_status          = request.POST.get('agent_status', '').strip()
            token_limit_raw     = request.POST.get('token_limit_override', '').strip()

            if ai_model:
                agent.ai_model = ai_model
            if groq_api_key:
                agent.groq_api_key = groq_api_key
            if openai_api_key:
                agent.openai_api_key = openai_api_key
            if openrouter_api_key:
                agent.openrouter_api_key = openrouter_api_key
            if new_status in dict(SereaAgent.STATUS_CHOICES):
                agent.status = new_status

            if token_limit_raw != '':
                try:
                    agent.token_limit_override = int(token_limit_raw)
                except ValueError:
                    messages.error(request, "Token limit must be a whole number.")
                    return redirect('workspace_admin:serea_config')
            else:
                agent.token_limit_override = None

            agent.save()
            messages.success(
                request,
                f"Config updated for {agent.tenant.email} — model: {agent.get_ai_model_display()}."
            )

        elif action == 'reset_tokens':
            agent.tokens_used_this_month = 0
            agent.save(update_fields=['tokens_used_this_month'])
            messages.success(request, f"Token counter reset to 0 for {agent.tenant.email}.")

        return redirect('workspace_admin:serea_config')

    # Annotate each agent with effective token limit for template display
    for agent in agents:
        if agent.token_limit_override is not None:
            agent.effective_token_limit = agent.token_limit_override
        elif agent.hired_employee and agent.hired_employee.tier:
            agent.effective_token_limit = agent.hired_employee.tier.token_limit
        else:
            agent.effective_token_limit = None

    return render(request, 'workspace_admin/serea_agent_config.html', {
        'agents': agents,
        'ai_model_choices': SereaAgent.AI_MODEL_CHOICES,
        'status_choices': SereaAgent.STATUS_CHOICES,
        'unlinked_employees': unlinked_employees,
    })


# ─── AI Tiers Management ────────────────────────────────────────────────────────

@workspace_admin_required
def ai_tiers(request):
    """Manage global AI Employee tier rate limits, pricing, and settings."""
    from .models import AIEmployeeTier
    if request.method == 'POST':
        tier_id = request.POST.get('tier_id')
        try:
            tier = AIEmployeeTier.objects.get(id=tier_id)
            token_limit = request.POST.get('token_limit')
            monthly_price = request.POST.get('monthly_price_usd')

            if token_limit is not None and token_limit.isdigit():
                tier.token_limit = int(token_limit)
            if monthly_price is not None:
                tier.monthly_price_usd = float(monthly_price)

            tier.save()
            messages.success(request, f"{tier.get_name_display()} tier config updated successfully.")
        except AIEmployeeTier.DoesNotExist:
            messages.error(request, "Tier not found.")
        except ValueError:
            messages.error(request, "Invalid input values. Please check token limits and pricing.")

        return redirect('ai_tiers')

    tiers = AIEmployeeTier.objects.all().order_by('monthly_price_usd')
    return render(request, 'workspace_admin/ai_tiers.html', {'tiers': tiers})

# ─── CMS & Content Control ────────────────────────────────────────────────────

@workspace_admin_required
def cms_control(request):
    """
    An index portal that bridges the Workspace Admin with the native Django Admin 
    for easy management of public site models (Services, Products, Team, FAQs, etc.).
    """
    return render(request, 'workspace_admin/cms_control.html')

# ─── Dynamic CMS CRUD Engine ──────────────────────────────────────────────────

from django.forms import modelform_factory
from django.db import models
import public_site.models as psm

# Map friendly URL names to their actual imported Model classes
CMS_MODELS = {
    'service': psm.Service,
    'product': psm.Product,
    'teammember': psm.TeamMember,
    'faq': psm.FAQ,
    'partner': psm.Partner,
    'homepagecontent': psm.HomepageContent,
    'blogpost': psm.BlogPost,
    'blogcategory': psm.BlogCategory,
    'navbaritem': psm.NavbarItem,
    'footerlink': psm.FooterLink,
    'videorepresentation': psm.VideoRepresentation,
    'videoreview': psm.VideoReview,
    'corevalue': psm.CoreValue,
    'platformfeature': psm.PlatformFeature,
    'workprocessstep': psm.WorkProcessStep,
    'testimonial': psm.Testimonial,
    'documentation': psm.Documentation,
    'documentationcategory': psm.DocumentationCategory,
    'companydetails': psm.CompanyDetails,
}

@workspace_admin_required
def cms_list(request, model_name):
    """Dynamically list instances of the requested CMS model."""
    if model_name not in CMS_MODELS:
        messages.error(request, "CMS Module not found.")
        return redirect('cms_control')

    model_class = CMS_MODELS[model_name]
    object_list = model_class.objects.all().order_by('-id') if hasattr(model_class, 'id') else model_class.objects.all()

    # Get readable names for table headers (ignoring large text fields or relations if possible)
    fields_meta = [f for f in model_class._meta.fields if f.name not in ('id', 'description', 'content', 'answer', 'bio')]
    table_headers = [f.verbose_name.title() for f in fields_meta]

    # Pre-calculate attribute values because Django templates don't support getattr()
    table_rows = []
    for obj in object_list:
        row_fields = []
        for f in fields_meta:
            val = getattr(obj, f.name, None)
            # Try to grab display value for choices if it exists
            get_display_method = getattr(obj, f'get_{f.name}_display', None)
            if get_display_method is not None:
                val = get_display_method()

            row_fields.append({
                'name': f.name,
                'value': val,
                'is_boolean': isinstance(f, models.BooleanField)
            })
        table_rows.append({'pk': obj.pk, 'fields': row_fields})

    return render(request, 'workspace_admin/cms_list.html', {
        'model_name': model_name,
        'model_verbose_name': model_class._meta.verbose_name.title(),
        'table_headers': table_headers,
        'table_rows': table_rows,
    })

@workspace_admin_required
def cms_form(request, model_name, pk=None):
    """Dynamically handle Create/Update forms for the requested CMS model."""
    if model_name not in CMS_MODELS:
        return redirect('cms_control')

    model_class = CMS_MODELS[model_name]
    instance = get_object_or_404(model_class, pk=pk) if pk else None

    # Generate a generic ModelForm excluding automatically set fields
    DynamicForm = modelform_factory(model_class, exclude=['created_at', 'updated_at'])

    if request.method == 'POST':
        form = DynamicForm(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"{model_class._meta.verbose_name.title()} saved securely.")
            return redirect('workspace_admin:cms_list', model_name=model_name)
    else:
        form = DynamicForm(instance=instance)

    # Attach premium styling class to all form inputs
    for visible in form.visible_fields():
        if getattr(visible.field.widget, 'input_type', None) not in ['checkbox', 'radio']:
            visible.field.widget.attrs['class'] = 'form-control form-control-premium mb-3'

    return render(request, 'workspace_admin/cms_form.html', {
        'form': form,
        'model_name': model_name,
        'model_verbose_name': model_class._meta.verbose_name.title(),
        'is_edit': pk is not None,
    })

@workspace_admin_required
def cms_delete(request, model_name, pk):
    """Dynamically handle Deletion for the requested CMS model."""
    if model_name in CMS_MODELS:
        model_class = CMS_MODELS[model_name]
        instance = get_object_or_404(model_class, pk=pk)
        instance.delete()
        messages.success(request, "Item deleted successfully.")
    return redirect('workspace_admin:cms_list', model_name=model_name)

# ─── Community Forum Management ───────────────────────────────────────────────

@workspace_admin_required
def forum_management(request):
    """View and manage all community forum topics."""
    topics = ForumTopic.objects.select_related('creator', 'category').order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete_topic':
            topic_id = request.POST.get('topic_id')
            topic = get_object_or_404(ForumTopic, id=topic_id)
            topic.delete()
            messages.success(request, "Topic deleted successfully.")
            return redirect('forum_management')

    return render(request, 'workspace_admin/forum_management.html', {
        'topics': topics,
    })

@workspace_admin_required
def forum_topic_detail(request, pk):
    """View a specific topic and its replies, with ability to reply and delete."""
    topic = get_object_or_404(ForumTopic, pk=pk)
    posts = topic.posts.select_related('author').order_by('created_at')

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'delete_post':
            post_id = request.POST.get('post_id')
            post = get_object_or_404(ForumPost, id=post_id)
            post.delete()
            messages.success(request, "Reply deleted successfully.")
            return redirect('workspace_admin:forum_topic_detail', pk=topic.pk)

        elif action == 'reply':
            content = request.POST.get('content', '').strip()
            if content:
                parent_id = request.POST.get('parent_id')
                parent_post = None
                if parent_id:
                    parent_post = get_object_or_404(ForumPost, id=parent_id)

                ForumPost.objects.create(
                    topic=topic,
                    parent=parent_post,
                    author=request.user, # The admin user
                    content=content
                )
                topic.save() # Update timestamp
                messages.success(request, "Reply posted successfully.")
            return redirect('workspace_admin:forum_topic_detail', pk=topic.pk)

    return render(request, 'workspace_admin/forum_topic_detail.html', {
        'topic': topic,
        'posts': posts,
    })


# ─── Internal Office Management ───────────────────────────────────────────────

@workspace_admin_required
def office_projects(request):
    """Manage internal company projects."""
    from workspace_admin.models import Project
    projects = Project.objects.select_related('client', 'manager').order_by('-created_at')

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        client_id = request.POST.get('client_id')
        manager_id = request.POST.get('manager_id')

        Project.objects.create(
            title=title,
            description=description,
            client_id=client_id if client_id else None,
            manager_id=manager_id if manager_id else None
        )
        messages.success(request, "Office Project created successfully.")
        return redirect('workspace_admin:office_projects')

    users = User.objects.all()
    return render(request, 'workspace_admin/office_projects.html', {
        'projects': projects,
        'users': users,
        'status_choices': Project._meta.get_field('status').choices,
    })


@workspace_admin_required
def office_tasks(request):
    """Manage internal company tasks (kanban style list)."""
    from workspace_admin.models import Task, Project
    tasks = Task.objects.select_related('project', 'assigned_to').order_by('-created_at')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_task':
            project_id = request.POST.get('project_id')
            title = request.POST.get('title')
            assigned_to_id = request.POST.get('assigned_to_id')
            priority = request.POST.get('priority')

            project = get_object_or_404(Project, id=project_id)
            Task.objects.create(
                project=project,
                title=title,
                assigned_to_id=assigned_to_id if assigned_to_id else None,
                priority=priority,
            )
            messages.success(request, "Task created successfully.")
        elif action == 'update_status':
            task_id = request.POST.get('task_id')
            new_status = request.POST.get('status')
            Task.objects.filter(id=task_id).update(status=new_status)
            messages.success(request, "Task status updated.")

        return redirect('workspace_admin:office_tasks')

    projects = Project.objects.all()
    staff_users = User.objects.filter(role__in=['super_admin', 'manager', 'employee', 'contractor'])

    return render(request, 'workspace_admin/office_tasks.html', {
        'tasks': tasks,
        'projects': projects,
        'staff_users': staff_users,
        'status_choices': Task._meta.get_field('status').choices,
        'priority_choices': Task._meta.get_field('priority').choices,
    })


@workspace_admin_required
def office_finance(request):
    """Manage internal company bookkeeping and finance."""
    from workspace_admin.models import FinanceRecord
    records = FinanceRecord.objects.select_related('recorded_by').order_by('-date', '-created_at')

    if request.method == 'POST':
        title = request.POST.get('title')
        record_type = request.POST.get('record_type')
        amount = request.POST.get('amount')
        date = request.POST.get('date')
        category = request.POST.get('category')

        FinanceRecord.objects.create(
            title=title,
            record_type=record_type,
            amount=amount,
            date=date,
            category=category,
            recorded_by=request.user
        )
        messages.success(request, "Finance record added successfully.")
        return redirect('workspace_admin:office_finance')

    return render(request, 'workspace_admin/office_finance.html', {
        'records': records,
        'record_types': FinanceRecord.RECORD_TYPE,
    })


# ── Hub Subscription Plan Management ─────────────────────────────────────────

@workspace_admin_required
def hub_plans(request):
    """Manage the four subscription tiers: prices, storage, entitlements."""
    from hub.models import HubPlanConfig
    plans = HubPlanConfig.objects.all().order_by('monthly_price_usd')

    if request.method == 'POST':
        plan_type = request.POST.get('plan_type')
        plan, _ = HubPlanConfig.objects.get_or_create(
            plan_type=plan_type,
            defaults={'display_name': plan_type.title()}
        )
        plan.display_name = request.POST.get('display_name', plan.display_name).strip()
        plan.tagline = request.POST.get('tagline', '').strip()
        plan.monthly_price_usd = request.POST.get('monthly_price_usd', plan.monthly_price_usd)
        plan.annual_price_usd = request.POST.get('annual_price_usd', plan.annual_price_usd)
        plan.storage_gb = request.POST.get('storage_gb', plan.storage_gb)
        plan.allows_cloud = request.POST.get('allows_cloud') == '1'
        plan.allows_ip_locked = request.POST.get('allows_ip_locked') == '1'
        plan.allows_self_hosted = request.POST.get('allows_self_hosted') == '1'
        plan.includes_basic_modules = request.POST.get('includes_basic_modules') == '1'
        plan.includes_full_industry_set = request.POST.get('includes_full_industry_set') == '1'
        plan.is_fully_customizable = request.POST.get('is_fully_customizable') == '1'
        plan.ip_locked_addon_usd = request.POST.get('ip_locked_addon_usd', plan.ip_locked_addon_usd)
        plan.self_hosted_addon_usd = request.POST.get('self_hosted_addon_usd', plan.self_hosted_addon_usd)
        plan.extra_storage_price_per_gb = request.POST.get('extra_storage_price_per_gb', plan.extra_storage_price_per_gb)
        plan.advance_discount_percent = request.POST.get('advance_discount_percent', plan.advance_discount_percent)
        plan.is_visible = request.POST.get('is_visible') == '1'
        plan.save()
        messages.success(request, f'{plan.display_name} plan updated.')
        return redirect('workspace_admin:hub_plans')

    return render(request, 'workspace_admin/hub_plans.html', {
        'plans': plans,
        'plan_types': [('freemium', 'Freemium'), ('standard', 'Standard'), ('premium', 'Premium'), ('advance', 'Advance')],
    })


@workspace_admin_required
def module_pricing(request):
    """Manage per-module pricing for the module store."""
    from hub.models import ModuleCatalog
    from .models import ModulePricingConfig

    all_modules = ModuleCatalog.objects.filter(is_available=True).order_by('name')
    pricing_map = {p.module_id: p for p in ModulePricingConfig.objects.all()}

    if request.method == 'POST':
        module_id = request.POST.get('module_id')
        mod = get_object_or_404(ModuleCatalog, module_id=module_id)
        cfg, _ = ModulePricingConfig.objects.get_or_create(
            module_id=module_id,
            defaults={'module_name': mod.name}
        )
        cfg.module_name = mod.name
        cfg.monthly_price_usd = request.POST.get('monthly_price_usd', cfg.monthly_price_usd)
        cfg.annual_price_usd = request.POST.get('annual_price_usd', cfg.annual_price_usd)
        cfg.save()
        # Also update ModuleCatalog price
        mod.monthly_price_usd = cfg.monthly_price_usd
        mod.save(update_fields=['monthly_price_usd'])
        messages.success(request, f'Pricing for {mod.name} updated.')
        return redirect('workspace_admin:module_pricing')

    modules_with_pricing = []
    for mod in all_modules:
        modules_with_pricing.append({
            'mod': mod,
            'pricing': pricing_map.get(mod.module_id),
        })

    return render(request, 'workspace_admin/module_pricing.html', {
        'modules_with_pricing': modules_with_pricing,
    })


@workspace_admin_required
def hub_subscriptions(request):
    """View and manage all business subscriptions across clients."""
    from hub.models import BusinessSubscription
    subs = BusinessSubscription.objects.select_related('business', 'business__owner').order_by('-started_at')

    plan_filter = request.GET.get('plan', '')
    if plan_filter:
        subs = subs.filter(plan_type=plan_filter)

    if request.method == 'POST':
        sub_id = request.POST.get('sub_id')
        sub = get_object_or_404(BusinessSubscription, pk=sub_id)
        action = request.POST.get('action')
        if action == 'change_plan':
            sub.plan_type = request.POST.get('plan_type', sub.plan_type)
            sub.status = 'active'
            sub.save()
            messages.success(request, f'Plan changed to {sub.plan_type} for {sub.business.name}.')
        elif action == 'add_storage':
            sub.extra_storage_gb += float(request.POST.get('extra_gb', 0))
            sub.save(update_fields=['extra_storage_gb'])
            messages.success(request, f'Storage increased for {sub.business.name}.')
        return redirect('workspace_admin:hub_subscriptions')

    return render(request, 'workspace_admin/hub_subscriptions.html', {
        'subs': subs,
        'plan_filter': plan_filter,
        'plan_types': BusinessSubscription.PLAN_TYPES,
    })


@workspace_admin_required
def storage_requests(request):
    """Review and approve/reject storage increase requests."""
    from hub.models import StorageIncreaseRequest, BusinessSubscription
    requests_qs = StorageIncreaseRequest.objects.select_related(
        'business', 'requested_by'
    ).order_by('-created_at')

    status_filter = request.GET.get('status', 'pending')
    if status_filter:
        requests_qs = requests_qs.filter(status=status_filter)

    if request.method == 'POST':
        from django.utils import timezone
        req_id = request.POST.get('request_id')
        req = get_object_or_404(StorageIncreaseRequest, pk=req_id)
        action = request.POST.get('action')
        admin_notes = request.POST.get('admin_notes', '').strip()

        if action == 'approve':
            approved_gb = float(request.POST.get('approved_gb', req.requested_gb))
            price = request.POST.get('price_usd', '')
            req.status = 'approved'
            req.approved_gb = approved_gb
            req.price_usd = float(price) if price else None
            req.admin_notes = admin_notes
            req.resolved_at = timezone.now()
            req.save()
            # Apply to subscription
            sub, _ = BusinessSubscription.objects.get_or_create(
                business=req.business, defaults={'plan_type': 'freemium'}
            )
            sub.extra_storage_gb += approved_gb
            sub.save(update_fields=['extra_storage_gb'])
            messages.success(request, f'+{approved_gb}GB approved for {req.business.name}.')
        elif action == 'reject':
            req.status = 'rejected'
            req.admin_notes = admin_notes
            req.resolved_at = timezone.now()
            req.save()
            messages.warning(request, f'Request from {req.business.name} rejected.')
        return redirect('workspace_admin:storage_requests')

    return render(request, 'workspace_admin/storage_requests.html', {
        'requests': requests_qs,
        'status_filter': status_filter,
    })


@workspace_admin_required
def advance_quotes(request):
    """Review and price Advance plan custom quotes."""
    from .models import AdvancePlanQuote

    quotes = AdvancePlanQuote.objects.select_related('business', 'requested_by').order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        quotes = quotes.filter(status=status_filter)

    if request.method == 'POST':
        quote_id = request.POST.get('quote_id')
        quote = get_object_or_404(AdvancePlanQuote, pk=quote_id)
        action = request.POST.get('action')

        if action == 'price':
            discount = float(request.POST.get('discount_percent', quote.discount_percent))
            base = float(request.POST.get('base_price_usd', quote.base_price_usd))
            final = base * (1 - discount / 100)
            quote.base_price_usd = base
            quote.discount_percent = discount
            quote.final_price_usd = round(final, 2)
            quote.admin_notes = request.POST.get('admin_notes', '').strip()
            quote.status = 'sent'
            quote.save()
            messages.success(request, f'Quote sent to {quote.business.name}.')
        elif action == 'accept':
            from hub.models import BusinessSubscription
            quote.status = 'accepted'
            quote.save()
            # Apply Advance plan
            sub, _ = BusinessSubscription.objects.get_or_create(
                business=quote.business, defaults={'plan_type': 'freemium'}
            )
            sub.plan_type = 'advance'
            sub.status = 'active'
            sub.advance_selected_modules = quote.selected_modules
            sub.advance_storage_gb = quote.requested_storage_gb
            sub.advance_installation_types = quote.installation_types
            sub.advance_discount_applied = quote.discount_percent
            sub.advance_monthly_price = quote.final_price_usd
            sub.save()
            messages.success(request, f'Advance plan activated for {quote.business.name}.')
        elif action == 'reject':
            quote.status = 'rejected'
            quote.admin_notes = request.POST.get('admin_notes', '').strip()
            quote.save()
            messages.warning(request, 'Quote rejected.')
        return redirect('workspace_admin:advance_quotes')

    return render(request, 'workspace_admin/advance_quotes.html', {
        'quotes': quotes,
        'status_filter': status_filter,
    })


@workspace_admin_required
def assign_package(request):
    """
    IT Officer panel to pre-assign a complete package of modules and agents to a client user.
    Once assigned, the client bypasses onboarding and lands straight on the KYB page / dashboard.
    """
    from hub.models import ModuleCatalog, BusinessInstance, DashboardConfig, BUSINESS_TYPES
    from workspace_admin.models import AIEmployeeTier
    from agents.models import AgentCatalog
    
    users = User.objects.filter(is_active=True).exclude(is_superuser=True, is_staff=True).order_by('email')
    modules = ModuleCatalog.objects.filter(is_available=True).order_by('name')
    agents = AgentCatalog.objects.filter(is_active=True).order_by('name')
    tiers = AIEmployeeTier.objects.all().order_by('monthly_price_usd')
    
    if request.method == 'POST':
        user_id = request.POST.get('client_user_id')
        business_name = request.POST.get('business_name', '').strip()
        business_type = request.POST.get('business_type', 'business').strip()
        selected_modules = request.POST.getlist('custom_modules')
        selected_agents = request.POST.getlist('custom_agents')
        
        agent_tiers = {}
        for key, val in request.POST.items():
            if key.startswith('agent_tier_'):
                agent_slug = key[len('agent_tier_'):]
                agent_tiers[agent_slug] = val
                
        client_user = get_object_or_404(User, id=user_id)
        
        from hub.views import _unique_slug
        from hub.dashboard_configurator import DashboardConfigurator
        
        # 1. Create Business
        slug = _unique_slug(business_name or f"{client_user.email.split('@')[0]}-business")
        business, _ = BusinessInstance.objects.get_or_create(
            owner=client_user,
            defaults={
                'name': business_name or f"{client_user.email.split('@')[0]}'s Workspace",
                'slug': slug,
                'business_type': business_type
            }
        )
        
        # 2. Provision selected modules
        from hub.models import TenantModule
        for mod_id in selected_modules:
            try:
                module = ModuleCatalog.objects.get(module_id=mod_id)
                TenantModule.objects.get_or_create(
                    business=business,
                    module=module,
                    defaults={'tier': 'free', 'is_active': True}
                )
            except ModuleCatalog.DoesNotExist:
                continue
                
        # Create a BusinessEmployee for the client as CEO
        from hub.models import BusinessEmployee
        try:
            BusinessEmployee.objects.get_or_create(
                business=business,
                user=client_user,
                defaults={
                    'name': client_user.get_full_name() or client_user.email,
                    'email': client_user.email,
                    'role': 'ceo',
                }
            )
        except Exception:
            pass
            
        # 3. Configure layout and hire custom agents
        answers = {
            'business_type': business_type,
            'main_challenge': 'getting_leads',
            'team_size': 'Just me',
            'platforms': [],
            'language': 'English',
            'payment_preference': 'Stripe',
        }
        
        configurator = DashboardConfigurator()
        configurator.configure(business, answers,
                               custom_agents=selected_agents if selected_agents else None,
                               agent_tiers=agent_tiers)
                               
        messages.success(request, f"Successfully pre-assigned package for {client_user.email}.")
        return redirect('workspace_admin:assign_package')
        
    return render(request, 'workspace_admin/assign_package.html', {
        'users': users,
        'modules': modules,
        'agents': agents,
        'tiers': tiers,
        'business_types': BUSINESS_TYPES,
    })


@workspace_admin_required
def control_center(request):
    """
    BengalBound IT & Executive Command Center.
    Aggregates simulated infrastructure, financials, staff directories,
    global admin settings, and Serea AI system queues.
    """
    from django.db.models import Sum
    from workspace_admin.models import FinanceRecord, Project, Task, WaaSSite, Subscription, Order, HiredAIEmployee
    from serea.models import SereaAgent
    
    # Financial indicators
    total_income = FinanceRecord.objects.filter(record_type='income').aggregate(Sum('amount'))['amount__sum'] or 0
    total_expense = FinanceRecord.objects.filter(record_type='expense').aggregate(Sum('amount'))['amount__sum'] or 0
    net_profit = total_income - total_expense
    
    # Client stats
    active_waas = WaaSSite.objects.filter(is_active=True).count()
    total_subscriptions = Subscription.objects.filter(status='active').count()
    recent_purchases = Order.objects.select_related('client').order_by('-created_at')[:10]
    
    # Staff / HR
    staff_members = User.objects.filter(role__in=['super_admin', 'manager', 'employee', 'contractor', 'auditor']).order_by('role')
    internal_tasks = Task.objects.select_related('assigned_to', 'project').order_by('-priority', '-due_date')[:15]
    
    # Serea AI oversight
    active_hired_ais = HiredAIEmployee.objects.select_related('employer', 'tier').filter(is_active=True).order_by('-hired_at')[:10]
    serea_agents = SereaAgent.objects.select_related('tenant').all()
    
    # Dynamic list of VPS systems.
    if 'vps_nodes' not in request.session:
        request.session['vps_nodes'] = {
            'VPS-01': {'name': 'Primary Dev-Backoffice', 'ip': '143.198.88.10', 'status': 'Online', 'cpu': 24, 'ram': 42, 'uptime': '14d 6h', 'region': 'US-East'},
            'VPS-02': {'name': 'AI Agent Orchestrator', 'ip': '143.198.88.22', 'status': 'Online', 'cpu': 68, 'ram': 81, 'uptime': '2d 11h', 'region': 'EU-West'},
            'VPS-03': {'name': 'Postgres Primary DB', 'ip': '143.198.88.3', 'status': 'Online', 'cpu': 12, 'ram': 55, 'uptime': '35d 2h', 'region': 'US-East'},
            'VPS-04': {'name': 'Public Landing CMS', 'ip': '143.198.88.45', 'status': 'Online', 'cpu': 8, 'ram': 19, 'uptime': '112d 18h', 'region': 'AS-East'},
            'VPS-05': {'name': 'Community Forums Node', 'ip': '143.198.88.99', 'status': 'Online', 'cpu': 15, 'ram': 34, 'uptime': '9d 5h', 'region': 'EU-West'},
        }
        request.session.modified = True

    # Global system settings simulation
    if 'system_settings' not in request.session:
        request.session['system_settings'] = {
            'maintenance_mode': False,
            'verbose_logging': True,
            'sandbox_payments': False,
            'ai_rate_limit': 60,
        }
        request.session.modified = True

    if request.method == 'POST' and not request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Handle regular form POST from the Super Admin panel settings save
        maintenance = request.POST.get('maintenance_mode') == 'on'
        logging = request.POST.get('verbose_logging') == 'on'
        sandbox = request.POST.get('sandbox_payments') == 'on'
        rate_limit = int(request.POST.get('ai_rate_limit', 60))
        
        request.session['system_settings'] = {
            'maintenance_mode': maintenance,
            'verbose_logging': logging,
            'sandbox_payments': sandbox,
            'ai_rate_limit': rate_limit,
        }
        request.session.modified = True
        messages.success(request, "Global system configurations updated successfully.")
        return redirect('workspace_admin:control_center')

    context = {
        'total_income': total_income,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'active_waas': active_waas,
        'total_subscriptions': total_subscriptions,
        'recent_purchases': recent_purchases,
        'staff_members': staff_members,
        'internal_tasks': internal_tasks,
        'active_hired_ais': active_hired_ais,
        'serea_agents_count': serea_agents.count(),
        'vps_nodes': request.session['vps_nodes'],
        'system_settings': request.session['system_settings'],
    }
    
    return render(request, 'workspace_admin/control_center.html', context)


@workspace_admin_required
def control_center_vps_action(request):
    """
    AJAX API endpoint for VPS action toggles (restart, shut_down, optimize).
    Persists simulated health metrics in user session.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
        
    import json
    import random
    from django.http import JsonResponse
    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)

    vps_id = data.get('vps_id')
    action = data.get('action')
    
    if 'vps_nodes' not in request.session:
        return JsonResponse({'success': False, 'error': 'No active VPS session'}, status=400)
        
    vps_nodes = request.session['vps_nodes']
    if vps_id not in vps_nodes:
        return JsonResponse({'success': False, 'error': 'VPS not found'}, status=404)
        
    vps = vps_nodes[vps_id]
    
    if action == 'restart':
        vps['status'] = 'Online'
        vps['cpu'] = random.randint(5, 20)
        vps['ram'] = random.randint(15, 30)
        vps['uptime'] = '0h 0m (Just Restarted)'
    elif action == 'power':
        if vps['status'] == 'Online':
            vps['status'] = 'Offline'
            vps['cpu'] = 0
            vps['ram'] = 0
        else:
            vps['status'] = 'Online'
            vps['cpu'] = random.randint(15, 45)
            vps['ram'] = random.randint(30, 50)
            vps['uptime'] = '0h 0m'
    elif action == 'optimize':
        if vps['status'] == 'Online':
            vps['ram'] = max(10, vps['ram'] - random.randint(15, 30))
            vps['cpu'] = max(5, vps['cpu'] - random.randint(5, 15))
        else:
            return JsonResponse({'success': False, 'error': 'Cannot optimize offline VPS'}, status=400)
            
    request.session['vps_nodes'] = vps_nodes
    request.session.modified = True
    
    return JsonResponse({
        'success': True,
        'vps_id': vps_id,
        'vps': vps
    })

