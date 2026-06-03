from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils.text import slugify
from django.utils import timezone
from django.views.decorators.http import require_POST
import os
import markdown
from django.conf import settings
from .models import (
    BusinessInstance, ModuleCatalog, TenantModule,
    BusinessEmployee, ConnectorSession, SyncLog,
    HubPlanConfig, BusinessSubscription, StorageIncreaseRequest,
    CustomPosition, UserBusinessMembership,
    INDUSTRY_MODULE_PRIORITY,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_business_for_user(slug, user):
    """Return a BusinessInstance the user owns, is an employee of, or has a membership in."""
    try:
        biz = BusinessInstance.objects.get(slug=slug, is_active=True)
    except BusinessInstance.DoesNotExist:
        return None
    if biz.owner == user:
        return biz
    if BusinessEmployee.objects.filter(business=biz, user=user, is_active=True).exists():
        return biz
    if UserBusinessMembership.objects.filter(business=biz, user=user, is_active=True).exists():
        return biz
    return None


def _get_or_create_subscription(biz):
    """Return the BusinessSubscription for a business, creating Freemium if missing."""
    sub, _ = BusinessSubscription.objects.get_or_create(
        business=biz,
        defaults={'plan_type': 'freemium', 'status': 'active'},
    )
    return sub


def _unique_slug(name):
    base = slugify(name)[:80]
    slug = base
    counter = 1
    while BusinessInstance.objects.filter(slug=slug).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug


# ─── Business Hub Landing (multi-business selector) ──────────────────────────

@login_required(login_url='/accounts/login/')
def hub_landing(request):
    owned = BusinessInstance.objects.filter(owner=request.user, is_active=True)
    employed = BusinessInstance.objects.filter(
        employees__user=request.user, employees__is_active=True, is_active=True
    ).exclude(owner=request.user)

    if owned.count() == 1 and not employed.exists():
        return redirect('hub:hub_dashboard', slug=owned.first().slug)

    return render(request, 'hub/hub_landing.html', {
        'owned_businesses': owned,
        'employed_businesses': employed,
    })


# ─── Create Business ─────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_create(request):
    if BusinessInstance.objects.filter(owner=request.user).exists():
        messages.error(
            request,
            "You already own a business. Each account can own only one business hub. "
            "To access another business, ask its owner to send you an invitation."
        )
        return redirect('hub:hub_landing')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        business_type = request.POST.get('business_type', 'business')
        installation_type = request.POST.get('installation_type', 'cloud')
        tagline = request.POST.get('tagline', '').strip()
        email = request.POST.get('business_email', '').strip()
        phone = request.POST.get('business_phone', '').strip()

        if not name:
            messages.error(request, "Business name is required.")
            return redirect('hub:hub_create')

        slug = _unique_slug(name)
        biz = BusinessInstance.objects.create(
            owner=request.user,
            name=name,
            slug=slug,
            business_type=business_type,
            installation_type=installation_type,
            tagline=tagline,
            business_email=email,
            business_phone=phone,
        )
        if installation_type == 'self_hosted':
            biz.generate_sync_token()

        BusinessEmployee.objects.create(
            business=biz,
            user=request.user,
            name=request.user.get_full_name() or request.user.email,
            email=request.user.email,
            role='ceo',
        )
        # Auto-provision Freemium subscription
        _get_or_create_subscription(biz)
        messages.success(request, f"'{biz.name}' created! Let's get you set up.")
        return redirect('hub:hub_onboarding', slug=biz.slug)

    return render(request, 'hub/hub_create.html', {
        'business_types': BusinessInstance._meta.get_field('business_type').choices,
        'installation_types': BusinessInstance._meta.get_field('installation_type').choices,
    })


# ─── Business Dashboard ───────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_dashboard(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    is_owner = biz.owner == request.user
    sub = _get_or_create_subscription(biz)
    employee = BusinessEmployee.objects.filter(business=biz, user=request.user, is_active=True).first()

    # Non-owners land on employee portal
    if not is_owner:
        return render(request, 'hub/hub_employee_portal.html', {
            'biz': biz,
            'employee': employee,
        })

    employees = BusinessEmployee.objects.filter(business=biz, is_active=True).select_related('user').order_by('name')
    employee_count = employees.count()
    member_count = UserBusinessMembership.objects.filter(business=biz, is_active=True).count()
    recent_syncs = None
    if biz.installation_type == 'self_hosted':
        recent_syncs = SyncLog.objects.filter(business=biz).order_by('-started_at')[:5]

    return render(request, 'hub/hub_dashboard.html', {
        'biz': biz,
        'sub': sub,
        'is_owner': is_owner,
        'employee': employee,
        'employees': employees,
        'employee_count': employee_count,
        'member_count': member_count,
        'recent_syncs': recent_syncs,
    })


# ─── Employee Portal ──────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_employee_portal(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    employee = BusinessEmployee.objects.filter(business=biz, user=request.user, is_active=True).first()
    if not employee:
        messages.error(request, "You don't have employee access to this business.")
        return redirect('hub:hub_landing')
    return render(request, 'hub/hub_employee_portal.html', {
        'biz': biz,
        'employee': employee,
    })


# ─── Module Store ─────────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_module_store(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    active_ids = biz.active_module_ids()
    sub = _get_or_create_subscription(biz)
    all_modules = ModuleCatalog.objects.filter(is_available=True)
    category_filter = request.GET.get('cat', '')
    if category_filter:
        all_modules = all_modules.filter(category=category_filter)

    # Industry priority module IDs for this business
    priority_ids = INDUSTRY_MODULE_PRIORITY.get(biz.business_type, [])

    # Group by category, annotating each module with subscription status
    from collections import defaultdict
    grouped = defaultdict(list)
    priority_modules = []

    for mod in all_modules:
        allowed = sub.allows_module(mod.module_id)
        upgrade_to = sub.get_upgrade_required(mod.module_id) if not allowed else None
        entry = {
            'obj': mod,
            'is_active': mod.module_id in active_ids,
            'can_activate': (
                not mod.is_coming_soon and
                allowed
            ),
            'is_priority': mod.module_id in priority_ids,
            'included_in_plan': allowed,
            'upgrade_to': upgrade_to,
        }
        grouped[mod.get_category_display()].append(entry)
        if mod.module_id in priority_ids:
            priority_modules.append(entry)

    # Sort priority modules by their position in the priority list
    priority_modules.sort(key=lambda e: priority_ids.index(e['obj'].module_id) if e['obj'].module_id in priority_ids else 99)

    return render(request, 'hub/hub_modules.html', {
        'biz': biz,
        'grouped_modules': dict(grouped),
        'active_ids': active_ids,
        'categories': ModuleCatalog.CATEGORIES,
        'current_cat': category_filter,
        'is_owner': biz.owner == request.user,
        'priority_modules': priority_modules,
        'sub': sub,
        'plan_types': BusinessSubscription.PLAN_TYPES,
        'current_business': biz,
    })


@login_required(login_url='/accounts/login/')
@require_POST
def hub_activate_module(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz or biz.owner != request.user:
        return HttpResponseForbidden()

    module_id = request.POST.get('module_id', '').strip()
    mod = get_object_or_404(ModuleCatalog, module_id=module_id, is_available=True, is_coming_soon=False)

    TenantModule.objects.get_or_create(
        business=biz,
        module=mod,
        defaults={'tier': 'free', 'is_active': True},
    )
    messages.success(request, f"'{mod.name}' has been activated.")
    return redirect('hub:hub_module_store', slug=slug)


@login_required(login_url='/accounts/login/')
@require_POST
def hub_deactivate_module(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz or biz.owner != request.user:
        return HttpResponseForbidden()

    module_id = request.POST.get('module_id', '').strip()
    TenantModule.objects.filter(business=biz, module__module_id=module_id).update(is_active=False)
    messages.info(request, "Module deactivated.")
    return redirect('hub:hub_module_store', slug=slug)


# ─── Employee Management ──────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_employees(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    employees = BusinessEmployee.objects.filter(business=biz).order_by('name')
    active_modules = TenantModule.objects.filter(business=biz, is_active=True).select_related('module')
    custom_positions = CustomPosition.objects.filter(business=biz)

    from workspace_admin.models import HiredAIEmployee
    hired_ais = HiredAIEmployee.objects.filter(employer=request.user).select_related('tier').order_by('-hired_at')

    return render(request, 'hub/hub_employees.html', {
        'biz': biz,
        'employees': employees,
        'active_modules': active_modules,
        'custom_positions': custom_positions,
        'is_owner': biz.owner == request.user,
        'hired_ais': hired_ais,
    })


@login_required(login_url='/accounts/login/')
@require_POST
def hub_add_employee(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz or biz.owner != request.user:
        return HttpResponseForbidden()

    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip()
    employee_id = request.POST.get('employee_id', '').strip()
    pin_code = request.POST.get('pin_code', '').strip()
    custom_pos_id = request.POST.get('custom_position_id', '')

    if not name:
        messages.error(request, "Employee name is required.")
        return redirect('hub:hub_employees', slug=slug)

    emp = BusinessEmployee.objects.create(
        business=biz,
        name=name,
        role='staff', # Default fallback, unused if custom position is set
        email=email,
        employee_id=employee_id,
        pin_code=pin_code,
    )

    if custom_pos_id:
        emp.custom_position_id = int(custom_pos_id)
        emp.save(update_fields=['custom_position_id'])

    messages.success(request, f"Employee '{name}' added.")
    return redirect('hub:hub_employees', slug=slug)


@login_required(login_url='/accounts/login/')
@require_POST
def hub_toggle_employee(request, slug, emp_id):
    biz = _get_business_for_user(slug, request.user)
    if not biz or biz.owner != request.user:
        return HttpResponseForbidden()

    emp = get_object_or_404(BusinessEmployee, pk=emp_id, business=biz)
    emp.is_active = not emp.is_active
    emp.save(update_fields=['is_active'])
    return redirect('hub:hub_employees', slug=slug)


# ─── Business Settings ────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_settings(request, slug):
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)

    if request.method == 'POST':
        biz.name = request.POST.get('name', biz.name).strip()
        biz.tagline = request.POST.get('tagline', '').strip()
        biz.business_email = request.POST.get('business_email', '').strip()
        biz.business_phone = request.POST.get('business_phone', '').strip()
        biz.business_address = request.POST.get('business_address', '').strip()
        if 'logo' in request.FILES:
            biz.logo = request.FILES['logo']
        biz.save()
        messages.success(request, "Settings saved.")
        return redirect('hub:hub_settings', slug=slug)

    return render(request, 'hub/hub_settings.html', {
        'biz': biz,
        'business_types': BusinessInstance._meta.get_field('business_type').choices,
    })


# ─── IP Access Control (ip_locked) ───────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_ip_access(request, slug):
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    if biz.installation_type not in ('ip_locked', 'self_hosted'):
        messages.warning(request, "IP access control is only available for IP-Locked or Self-Hosted plans.")
        return redirect('hub:hub_settings', slug=slug)

    return render(request, 'hub/hub_ip_access.html', {'biz': biz})


@login_required(login_url='/accounts/login/')
@require_POST
def hub_add_ip(request, slug):
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    ip = request.POST.get('ip_address', '').strip()
    if ip and ip not in biz.allowed_ips:
        biz.allowed_ips.append(ip)
        biz.save(update_fields=['allowed_ips'])
        messages.success(request, f"IP {ip} added to allowlist.")
    return redirect('hub:hub_ip_access', slug=slug)


@login_required(login_url='/accounts/login/')
@require_POST
def hub_remove_ip(request, slug):
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    ip = request.POST.get('ip_address', '').strip()
    if ip in biz.allowed_ips:
        biz.allowed_ips.remove(ip)
        biz.save(update_fields=['allowed_ips'])
        messages.success(request, f"IP {ip} removed.")
    return redirect('hub:hub_ip_access', slug=slug)


# ─── Connector App Sessions ───────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_connector(request, slug):
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    sessions = ConnectorSession.objects.filter(business=biz).order_by('-created_at')
    now = timezone.now()
    return render(request, 'hub/hub_connector.html', {
        'biz': biz,
        'sessions': sessions,
        'now': now,
    })


@login_required(login_url='/accounts/login/')
@require_POST
def hub_generate_token(request, slug):
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    label = request.POST.get('label', '').strip()
    days = int(request.POST.get('days_valid', 30))
    ConnectorSession.generate(biz, label=label, days_valid=days)
    messages.success(request, "Connector token generated.")
    return redirect('hub:hub_connector', slug=slug)


@login_required(login_url='/accounts/login/')
@require_POST
def hub_revoke_token(request, slug, session_id):
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    session = get_object_or_404(ConnectorSession, pk=session_id, business=biz)
    session.is_active = False
    session.save(update_fields=['is_active'])
    messages.info(request, "Connector token revoked.")
    return redirect('hub:hub_connector', slug=slug)


# ─── Self-Hosted Sync ─────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_sync(request, slug):
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    if biz.installation_type != 'self_hosted':
        messages.warning(request, "Sync is only available for Self-Hosted installations.")
        return redirect('hub:hub_settings', slug=slug)

    recent_logs = SyncLog.objects.filter(business=biz).order_by('-started_at')[:20]
    return render(request, 'hub/hub_sync.html', {
        'biz': biz,
        'recent_logs': recent_logs,
    })


@login_required(login_url='/accounts/login/')
@require_POST
def hub_regenerate_sync_token(request, slug):
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    biz.generate_sync_token()
    messages.success(request, "Sync token regenerated. Update your self-hosted configuration.")
    return redirect('hub:hub_sync', slug=slug)


# ─── Sync API Endpoint (used by self-hosted connector) ───────────────────────

def hub_sync_api(request):
    """
    Token-authenticated endpoint for self-hosted instances to push/pull sync data.
    Called by the local server's sync daemon, not by a browser user.
    """
    token = request.headers.get('X-Sync-Token', '')
    if not token:
        return JsonResponse({'error': 'Missing sync token'}, status=401)

    try:
        biz = BusinessInstance.objects.get(sync_token=token, is_active=True)
    except BusinessInstance.DoesNotExist:
        return JsonResponse({'error': 'Invalid token'}, status=403)

    if request.method == 'POST':
        import json
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        log = SyncLog.objects.create(
            business=biz,
            sync_type=payload.get('sync_type', 'push'),
            status='success',
            records_synced=payload.get('records_count', 0),
        )
        log.completed_at = timezone.now()
        log.save(update_fields=['completed_at'])

        biz.last_synced_at = timezone.now()
        biz.save(update_fields=['last_synced_at'])

        return JsonResponse({'status': 'ok', 'synced_at': biz.last_synced_at.isoformat()})

    return JsonResponse({'status': 'ok', 'business': biz.name, 'last_synced': str(biz.last_synced_at)})


# ── Subscription Management ───────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_subscription(request, slug):
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    sub = _get_or_create_subscription(biz)
    plans = HubPlanConfig.objects.filter(is_visible=True).order_by('monthly_price_usd')

    # Seed defaults if none exist
    if not plans.exists():
        _seed_plan_defaults()
        plans = HubPlanConfig.objects.filter(is_visible=True).order_by('monthly_price_usd')

    storage_requests = StorageIncreaseRequest.objects.filter(business=biz).order_by('-created_at')[:5]

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'change_plan':
            new_plan = request.POST.get('plan_type', '').strip()
            valid_plans = [p[0] for p in BusinessSubscription.PLAN_TYPES]
            if new_plan not in valid_plans:
                messages.error(request, 'Invalid plan selected.')
            elif new_plan == 'advance':
                return redirect('hub:hub_advance_quote', slug=slug)
            else:
                billing = request.POST.get('billing_cycle', 'monthly')
                if new_plan in ('standard', 'premium'):
                    return redirect(f'/billing/checkout/{new_plan}/?cycle={billing}&business_id={biz.id}')
                
                old_plan = sub.plan_type
                sub.plan_type = new_plan
                sub.billing_cycle = billing if billing in ('monthly', 'annual') else 'monthly'
                sub.status = 'active'
                # Reset plan-specific fields when changing plan
                if new_plan != 'premium':
                    sub.premium_industry = ''
                if new_plan != 'advance':
                    sub.advance_selected_modules = []
                    sub.advance_storage_gb = 100
                    sub.advance_installation_types = []
                    sub.advance_discount_applied = 0
                    sub.advance_monthly_price = 0
                sub.save()
                if new_plan == old_plan:
                    messages.info(request, 'You are already on this plan.')
                else:
                    direction = 'upgraded' if valid_plans.index(new_plan) > valid_plans.index(old_plan) else 'changed'
                    messages.success(request, f'Plan {direction} to {sub.get_plan_type_display()} successfully.')

        elif action == 'request_storage':
            gb = float(request.POST.get('requested_gb', 10))
            msg = request.POST.get('message', '').strip()
            StorageIncreaseRequest.objects.create(
                business=biz, requested_by=request.user, requested_gb=gb, message=msg
            )
            messages.success(request, f'Storage increase request for {gb}GB submitted.')

        elif action == 'select_premium_industry':
            industry = request.POST.get('premium_industry', '')
            if sub.plan_type == 'premium':
                sub.premium_industry = industry
                sub.save(update_fields=['premium_industry'])
                messages.success(request, 'Industry set for your Premium module pack.')

        return redirect('hub:hub_subscription', slug=slug)

    from .models import BUSINESS_TYPES
    return render(request, 'hub/hub_subscription.html', {
        'biz': biz,
        'sub': sub,
        'plans': plans,
        'storage_requests': storage_requests,
        'business_types': BUSINESS_TYPES,
        'current_business': biz,
        'is_owner': True,
    })


@login_required(login_url='/accounts/login/')
def hub_advance_quote(request, slug):
    """Advance plan configurator — client selects modules, storage, installation types."""
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    sub = _get_or_create_subscription(biz)
    all_modules = ModuleCatalog.objects.filter(is_available=True, is_coming_soon=False)

    # Fetch pricing info
    from workspace_admin.models import ModulePricingConfig
    pricing_map = {p.module_id: p for p in ModulePricingConfig.objects.all()}
    advance_plan = HubPlanConfig.get_plan('advance')

    modules_with_price = []
    for mod in all_modules:
        price_cfg = pricing_map.get(mod.module_id)
        monthly = price_cfg.monthly_price_usd if price_cfg else mod.monthly_price_usd
        modules_with_price.append({'obj': mod, 'monthly': monthly})

    if request.method == 'POST':
        selected_module_ids = request.POST.getlist('module_ids')
        storage_gb = float(request.POST.get('storage_gb', 100))
        install_types = request.POST.getlist('installation_types')
        notes = request.POST.get('notes', '').strip()

        # Calculate base price
        module_total = sum(
            float(pricing_map[mid].monthly_price_usd) if mid in pricing_map else 0
            for mid in selected_module_ids
        )
        storage_cost = max(0, storage_gb - 100) * float(advance_plan.extra_storage_price_per_gb or 0.5)
        install_cost = 0
        if 'ip_locked' in install_types:
            install_cost += float(advance_plan.ip_locked_addon_usd or 0)
        if 'self_hosted' in install_types:
            install_cost += float(advance_plan.self_hosted_addon_usd or 0)
        base_price = module_total + storage_cost + install_cost
        discount = float(advance_plan.advance_discount_percent or 0)
        final_price = base_price * (1 - discount / 100)

        from workspace_admin.models import AdvancePlanQuote
        AdvancePlanQuote.objects.create(
            business=biz,
            requested_by=request.user,
            selected_modules=selected_module_ids,
            requested_storage_gb=storage_gb,
            installation_types=install_types,
            notes=notes,
            base_price_usd=round(base_price, 2),
            discount_percent=discount,
            final_price_usd=round(final_price, 2),
        )
        messages.success(request, 'Your Advance plan quote has been submitted. Our team will review and get back to you.')
        return redirect('hub:hub_subscription', slug=slug)

    return render(request, 'hub/hub_advance_quote.html', {
        'biz': biz,
        'sub': sub,
        'modules_with_price': modules_with_price,
        'advance_plan': advance_plan,
        'current_business': biz,
        'is_owner': True,
    })


def _seed_plan_defaults():
    """Create default HubPlanConfig rows if none exist."""
    defaults = [
        dict(plan_type='freemium', display_name='Freemium', tagline='Start for free',
             monthly_price_usd=0, annual_price_usd=0, storage_gb=5,
             allows_cloud=True, includes_basic_modules=True),
        dict(plan_type='standard', display_name='Standard', tagline='For growing teams',
             monthly_price_usd=29, annual_price_usd=290, storage_gb=20,
             allows_cloud=True, includes_basic_modules=True,
             ip_locked_addon_usd=15, self_hosted_addon_usd=25),
        dict(plan_type='premium', display_name='Premium', tagline='Full industry solution',
             monthly_price_usd=79, annual_price_usd=790, storage_gb=50,
             allows_cloud=True, allows_ip_locked=True,
             includes_basic_modules=True, includes_full_industry_set=True,
             self_hosted_addon_usd=40),
        dict(plan_type='advance', display_name='Advance', tagline='Fully customizable',
             monthly_price_usd=0, annual_price_usd=0, storage_gb=100,
             allows_cloud=True, allows_ip_locked=True, allows_self_hosted=True,
             includes_basic_modules=True, includes_full_industry_set=True,
             is_fully_customizable=True, advance_discount_percent=10,
             extra_storage_price_per_gb=0.40),
    ]
    for d in defaults:
        HubPlanConfig.objects.get_or_create(plan_type=d['plan_type'], defaults=d)


# ─── Custom Positions ─────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_positions(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    from .access import get_access_level
    if get_access_level(biz, request.user) < 9:
        return HttpResponseForbidden()

    positions = CustomPosition.objects.filter(business=biz).order_by('-access_level', 'name')
    active_modules = TenantModule.objects.filter(business=biz, is_active=True).select_related('module')
    return render(request, 'hub/hub_positions.html', {
        'biz': biz,
        'positions': positions,
        'active_modules': active_modules,
        'is_owner': biz.owner == request.user,
        'access_range': range(1, 10),
    })


@login_required(login_url='/accounts/login/')
def hub_position_create(request, slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    from .access import get_access_level
    if get_access_level(biz, request.user) < 9:
        return HttpResponseForbidden()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        access_level = int(request.POST.get('access_level', 3))
        if not name:
            messages.error(request, "Position name is required.")
            return redirect('hub:hub_position_create', slug=slug)

        perm_fields = [
            'perm_view_financials', 'perm_approve_expenses', 'perm_manage_employees',
            'perm_manage_modules', 'perm_access_reports', 'perm_manage_inventory',
            'perm_manage_production', 'perm_manage_quality', 'perm_manage_assets',
            'perm_manage_plm', 'perm_manage_erp', 'perm_manage_mes',
        ]
        perm_values = {f: f in request.POST for f in perm_fields}

        pos, created = CustomPosition.objects.get_or_create(
            business=biz, name=name,
            defaults={'description': description, 'access_level': access_level,
                      'created_by': request.user, **perm_values}
        )
        if not created:
            messages.error(request, f"A position named '{name}' already exists.")
            return redirect('hub:hub_position_create', slug=slug)

        messages.success(request, f"Position '{name}' created.")
        return redirect('hub:hub_positions', slug=slug)

    active_modules = TenantModule.objects.filter(business=biz, is_active=True).select_related('module')
    return render(request, 'hub/hub_position_form.html', {
        'biz': biz,
        'active_modules': active_modules,
        'is_owner': biz.owner == request.user,
        'position': None,
        'access_range': range(1, 10),
    })


@login_required(login_url='/accounts/login/')
def hub_position_edit(request, slug, pos_id):
    biz = _get_business_for_user(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    from .access import get_access_level
    if get_access_level(biz, request.user) < 9:
        return HttpResponseForbidden()

    position = get_object_or_404(CustomPosition, pk=pos_id, business=biz)

    if request.method == 'POST':
        position.name = request.POST.get('name', position.name).strip()
        position.description = request.POST.get('description', '').strip()
        position.access_level = int(request.POST.get('access_level', position.access_level))
        perm_fields = [
            'perm_view_financials', 'perm_approve_expenses', 'perm_manage_employees',
            'perm_manage_modules', 'perm_access_reports', 'perm_manage_inventory',
            'perm_manage_production', 'perm_manage_quality', 'perm_manage_assets',
            'perm_manage_plm', 'perm_manage_erp', 'perm_manage_mes',
        ]
        for f in perm_fields:
            setattr(position, f, f in request.POST)
        position.save()
        messages.success(request, f"Position '{position.name}' updated.")
        return redirect('hub:hub_positions', slug=slug)

    active_modules = TenantModule.objects.filter(business=biz, is_active=True).select_related('module')
    return render(request, 'hub/hub_position_form.html', {
        'biz': biz,
        'active_modules': active_modules,
        'is_owner': biz.owner == request.user,
        'position': position,
        'access_range': range(1, 10),
    })


@login_required(login_url='/accounts/login/')
@require_POST
def hub_position_delete(request, slug, pos_id):
    biz = _get_business_for_user(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    from .access import get_access_level
    if get_access_level(biz, request.user) < 9:
        return HttpResponseForbidden()

    position = get_object_or_404(CustomPosition, pk=pos_id, business=biz)
    name = position.name
    position.delete()
    messages.success(request, f"Position '{name}' deleted.")
    return redirect('hub:hub_positions', slug=slug)


@login_required(login_url='/accounts/login/')
def hub_employee_edit(request, slug, emp_id):
    biz = _get_business_for_user(slug, request.user)
    if not biz or biz.owner != request.user:
        return HttpResponseForbidden()

    employee = get_object_or_404(BusinessEmployee, pk=emp_id, business=biz)
    custom_positions = CustomPosition.objects.filter(business=biz)

    if request.method == 'POST':
        employee.name = request.POST.get('name', employee.name).strip()
        employee.role = request.POST.get('role', employee.role)
        employee.email = request.POST.get('email', employee.email).strip()
        employee.phone = request.POST.get('phone', employee.phone or '').strip()
        employee.department = request.POST.get('department', employee.department or '').strip()
        employee.employee_id = request.POST.get('employee_id', employee.employee_id or '').strip()
        custom_pos_id = request.POST.get('custom_position_id', '')
        if custom_pos_id:
            employee.custom_position_id = int(custom_pos_id)
        else:
            employee.custom_position = None
        employee.save()
        messages.success(request, f"Employee '{employee.name}' updated.")
        return redirect('hub:hub_employees', slug=slug)

    active_modules = TenantModule.objects.filter(business=biz, is_active=True).select_related('module')
    return render(request, 'hub/hub_employee_edit.html', {
        'biz': biz,
        'employee': employee,
        'custom_positions': custom_positions,
        'roles': BusinessEmployee.ROLES,
        'active_modules': active_modules,
        'is_owner': True,
    })


# ─── Business Membership Management ──────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_members(request, slug):
    """List and manage non-owner members of a business hub."""
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    memberships = UserBusinessMembership.objects.filter(
        business=biz
    ).select_related('user', 'invited_by').order_by('-joined_at')
    return render(request, 'hub/hub_members.html', {
        'biz': biz,
        'memberships': memberships,
        'is_owner': True,
    })


@login_required(login_url='/accounts/login/')
@require_POST
def hub_invite_member(request, slug):
    """Invite a registered user by email as a business member."""
    from accounts.models import User as _User
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    email = request.POST.get('email', '').strip().lower()
    role = request.POST.get('role', 'member')

    if not email:
        messages.error(request, "Enter an email address.")
        return redirect('hub:hub_members', slug=slug)

    if email == request.user.email:
        messages.error(request, "You are already the owner.")
        return redirect('hub:hub_members', slug=slug)

    try:
        invitee = _User.objects.get(email=email)
    except _User.DoesNotExist:
        messages.error(request, f"No account found for {email}. They need to register first.")
        return redirect('hub:hub_members', slug=slug)

    mem, created = UserBusinessMembership.objects.get_or_create(
        user=invitee, business=biz,
        defaults={'role': role, 'invited_by': request.user, 'is_active': True},
    )
    if not created:
        mem.is_active = True
        mem.role = role
        mem.save(update_fields=['is_active', 'role'])
        messages.info(request, f"{email} membership updated.")
    else:
        messages.success(request, f"{email} added as {role}.")

    return redirect('hub:hub_members', slug=slug)


@login_required(login_url='/accounts/login/')
@require_POST
def hub_remove_member(request, slug, membership_id):
    """Remove a non-owner member from a business hub."""
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    mem = get_object_or_404(UserBusinessMembership, pk=membership_id, business=biz)
    mem.delete()
    messages.success(request, f"{mem.user.email} removed from {biz.name}.")
    return redirect('hub:hub_members', slug=slug)


# ─── Business Onboarding Wizard ───────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def hub_onboarding(request, slug):
    """
    3-step business onboarding wizard (shown once after hub_create):
      Step 1: Confirm name + business type
      Step 2: Pick 3-5 starter modules
      Step 3: Hire / link first AI employee
    """
    biz = get_object_or_404(BusinessInstance, slug=slug, owner=request.user)
    sub = _get_or_create_subscription(biz)
    step = int(request.GET.get('step', 1))

    if request.method == 'POST':
        posted_step = int(request.POST.get('step', 1))

        if posted_step == 1:
            # Save any business-type / name correction
            name = request.POST.get('name', biz.name).strip()
            biz_type = request.POST.get('business_type', biz.business_type)
            if name:
                biz.name = name
            biz.business_type = biz_type
            biz.save(update_fields=['name', 'business_type'])
            return redirect(f"{request.path}?step=2")

        elif posted_step == 2:
            # Activate selected starter modules
            selected_ids = request.POST.getlist('module_ids')
            for mid in selected_ids[:6]:   # cap at 6 during onboarding
                try:
                    mod = ModuleCatalog.objects.get(module_id=mid, is_available=True)
                    TenantModule.objects.get_or_create(
                        business=biz, module=mod,
                        defaults={'tier': 'free', 'is_active': True},
                    )
                except ModuleCatalog.DoesNotExist:
                    pass
            return redirect(f"{request.path}?step=3")

        elif posted_step == 3:
            # Step 3 just redirects to hire-ai or the dashboard
            action = request.POST.get('action', 'skip')
            if action == 'hire':
                return redirect('console_admin:hire_ai')
            return redirect('console_admin:dashboard')

    # Priority modules for this business type
    priority_ids = INDUSTRY_MODULE_PRIORITY.get(biz.business_type, [])
    priority_modules = []
    for mid in priority_ids[:12]:
        try:
            priority_modules.append(ModuleCatalog.objects.get(module_id=mid))
        except ModuleCatalog.DoesNotExist:
            pass

    active_ids = biz.active_module_ids()

    return render(request, 'hub/hub_onboarding.html', {
        'biz': biz,
        'step': step,
        'business_types': BusinessInstance._meta.get_field('business_type').choices,
        'priority_modules': priority_modules,
        'active_ids': active_ids,
        'sub': sub,
        'current_business': biz,
        'is_owner': True,
    })


@login_required(login_url='/accounts/login/')
def hub_module_capabilities(request, slug, module_id):
    biz = get_object_or_404(BusinessInstance, slug=slug)
    module_obj = get_object_or_404(ModuleCatalog, module_id=module_id)

    readme_path = os.path.join(settings.BASE_DIR, 'modules', module_id, 'README.md')
    content = ""
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            raw_markdown = f.read()
            content = markdown.markdown(raw_markdown, extensions=['extra', 'codehilite'])
    else:
        content = f"<p>No detailed capability documentation found for {module_obj.name}.</p>"

    return render(request, 'hub/module_capabilities.html', {
        'biz': biz,
        'module_obj': module_obj,
        'content': content,
        'is_owner': biz.owner == request.user,
        'current_business': biz,
    })


@login_required(login_url='/accounts/login/')
def agent_capabilities(request, slug, agent_slug):
    biz = get_object_or_404(BusinessInstance, slug=slug)
    from agents.models import AgentCatalog
    agent_obj = get_object_or_404(AgentCatalog, slug=agent_slug)

    readme_path = os.path.join(settings.BASE_DIR, 'agents', agent_slug, 'README.md')
    content = ""
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            raw_markdown = f.read()
            content = markdown.markdown(raw_markdown, extensions=['extra', 'codehilite'])
    else:
        content = f"<p>No detailed capability documentation found for {agent_obj.name}.</p>"

    return render(request, 'hub/agent_capabilities.html', {
        'biz': biz,
        'agent_obj': agent_obj,
        'content': content,
        'is_owner': biz.owner == request.user,
        'current_business': biz,
    })


@login_required(login_url='/accounts/login/')
def agent_dashboard(request, slug, agent_slug):
    biz = _get_business_for_user(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    from agents.models import AgentCatalog, AgentInstance, AgentLog, AgentMemory, AgentIntegration
    from workspace_admin.models import HiredAIEmployee

    catalog = get_object_or_404(AgentCatalog, slug=agent_slug, is_active=True)
    instance = get_object_or_404(AgentInstance, business=biz, catalog=catalog)

    logs = AgentLog.objects.filter(instance=instance).order_by('-created_at')[:10]
    memories = AgentMemory.objects.filter(instance=instance)[:15]
    integrations = AgentIntegration.objects.filter(instance=instance)

    # Find the HiredAIEmployee matching this catalog and business owner
    hired_ai = HiredAIEmployee.objects.filter(
        employer=request.user,
        agent_catalog=catalog,
        is_active=True
    ).first()

    return render(request, 'hub/agent_dashboard.html', {
        'biz': biz,
        'catalog': catalog,
        'instance': instance,
        'logs': logs,
        'memories': memories,
        'integrations': integrations,
        'hired_ai': hired_ai,
        'current_business': biz,
        'is_owner': biz.owner == request.user,
    })
