import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from hub.models import BusinessInstance, BusinessEmployee
from .models import CareClient, CarePlan, CareSession, StaffRota, ComplianceDocument


def _check(slug, user, min_level=1):
    biz = get_object_or_404(BusinessInstance, slug=slug)
    try:
        emp = BusinessEmployee.objects.get(business=biz, user=user, is_active=True)
    except BusinessEmployee.DoesNotExist:
        return None, None, None
    level = emp.access_level_numeric
    if level < min_level:
        return biz, emp, None
    return biz, emp, level


@login_required
def care_home(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    today = datetime.date.today()
    total_clients = CareClient.objects.filter(business=biz, status='active').count()
    active_plans = CarePlan.objects.filter(client__business=biz, is_active=True).count()
    sessions_today = CareSession.objects.filter(client__business=biz, session_date=today).count()
    expiring_docs = ComplianceDocument.objects.filter(
        business=biz, is_active=True, review_date__lte=today
    ).count()

    recent_sessions = CareSession.objects.filter(
        client__business=biz
    ).select_related('client', 'performed_by__user').order_by('-session_date', '-created_at')[:8]

    return render(request, 'care_manager/home.html', {
        'biz': biz,
        'access_level': level,
        'stats': {
            'total_clients': total_clients,
            'active_plans': active_plans,
            'sessions_today': sessions_today,
            'expiring_docs': expiring_docs,
        },
        'recent_sessions': recent_sessions,
    })


@login_required
def client_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'add_client':
            assigned_id = request.POST.get('assigned_to_id')
            assigned = BusinessEmployee.objects.filter(pk=assigned_id, business=biz).first() if assigned_id else emp
            client = CareClient.objects.create(
                business=biz,
                full_name=request.POST.get('full_name', ''),
                date_of_birth=request.POST.get('date_of_birth') or None,
                contact_name=request.POST.get('contact_name', ''),
                contact_phone=request.POST.get('contact_phone', ''),
                contact_email=request.POST.get('contact_email', ''),
                address=request.POST.get('address', ''),
                care_level=request.POST.get('care_level', 'assisted'),
                admission_date=request.POST.get('admission_date') or None,
                medical_notes=request.POST.get('medical_notes', ''),
                dietary_requirements=request.POST.get('dietary_requirements', ''),
                notes=request.POST.get('notes', ''),
                assigned_to=assigned,
            )
            messages.success(request, f'Client "{client.full_name}" added.')
            return redirect('care_manager:client_detail', slug=slug, client_id=client.pk)
        return redirect('care_manager:client_list', slug=slug)

    status_filter = request.GET.get('status', 'active')
    clients = CareClient.objects.filter(business=biz).select_related('assigned_to__user')
    if status_filter:
        clients = clients.filter(status=status_filter)

    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'care_manager/client_list.html', {
        'biz': biz,
        'access_level': level,
        'clients': clients,
        'status_filter': status_filter,
        'statuses': CareClient.STATUS_CHOICES,
        'care_levels': CareClient.CARE_LEVEL_CHOICES,
        'employees': employees,
    })


@login_required
def client_detail(request, slug, client_id):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    client = get_object_or_404(CareClient, pk=client_id, business=biz)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')

        if action == 'add_plan':
            assigned_id = request.POST.get('assigned_to_id')
            assigned = BusinessEmployee.objects.filter(pk=assigned_id, business=biz).first() if assigned_id else None
            CarePlan.objects.create(
                client=client,
                title=request.POST.get('title', ''),
                care_type=request.POST.get('care_type', 'personal'),
                description=request.POST.get('description', ''),
                frequency=request.POST.get('frequency', 'daily'),
                assigned_to=assigned,
                start_date=request.POST.get('start_date', ''),
                review_date=request.POST.get('review_date') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Care plan added.')

        elif action == 'log_session':
            plan_id = request.POST.get('care_plan_id')
            plan = CarePlan.objects.filter(pk=plan_id, client=client).first() if plan_id else None
            CareSession.objects.create(
                client=client,
                care_plan=plan,
                performed_by=emp,
                session_date=request.POST.get('session_date', ''),
                session_time=request.POST.get('session_time') or None,
                duration_minutes=request.POST.get('duration_minutes', 30),
                status=request.POST.get('status', 'completed'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Session logged.')

        elif action == 'update_status' and level >= 3:
            new_status = request.POST.get('status')
            if new_status in dict(CareClient.STATUS_CHOICES):
                client.status = new_status
                client.save(update_fields=['status'])
                messages.success(request, f'Status updated to {client.get_status_display()}.')

        return redirect('care_manager:client_detail', slug=slug, client_id=client_id)

    plans = CarePlan.objects.filter(client=client)
    sessions = CareSession.objects.filter(client=client).order_by('-session_date', '-created_at')[:20]
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'care_manager/client_detail.html', {
        'biz': biz,
        'access_level': level,
        'client': client,
        'plans': plans,
        'sessions': sessions,
        'employees': employees,
        'care_types': CarePlan.CARE_TYPE_CHOICES,
        'frequencies': CarePlan.FREQUENCY_CHOICES,
        'session_statuses': CareSession.STATUS_CHOICES,
        'statuses': CareClient.STATUS_CHOICES,
    })


@login_required
def staff_rota(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    today = datetime.date.today()

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_shift':
            employee_id = request.POST.get('employee_id')
            employee = get_object_or_404(BusinessEmployee, pk=employee_id, business=biz)
            StaffRota.objects.create(
                business=biz,
                employee=employee,
                shift_date=request.POST.get('shift_date', ''),
                start_time=request.POST.get('start_time', ''),
                end_time=request.POST.get('end_time', ''),
                role=request.POST.get('role', ''),
                notes=request.POST.get('notes', ''),
                is_confirmed='is_confirmed' in request.POST,
            )
            messages.success(request, 'Shift added.')
        return redirect('care_manager:staff_rota', slug=slug)

    date_str = request.GET.get('date', '')
    try:
        filter_date = datetime.date.fromisoformat(date_str) if date_str else today
    except ValueError:
        filter_date = today

    rota = StaffRota.objects.filter(
        business=biz, shift_date=filter_date
    ).select_related('employee__user')
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'care_manager/staff_rota.html', {
        'biz': biz,
        'access_level': level,
        'rota': rota,
        'filter_date': filter_date,
        'employees': employees,
    })


@login_required
def compliance(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'add_document':
            ComplianceDocument.objects.create(
                business=biz,
                title=request.POST.get('title', ''),
                doc_type=request.POST.get('doc_type', 'policy'),
                description=request.POST.get('description', ''),
                file_url=request.POST.get('file_url', ''),
                review_date=request.POST.get('review_date') or None,
                created_by=emp,
            )
            messages.success(request, 'Compliance document added.')
        elif action == 'toggle_doc':
            doc = get_object_or_404(ComplianceDocument, pk=request.POST.get('doc_id'), business=biz)
            doc.is_active = not doc.is_active
            doc.save(update_fields=['is_active'])
            messages.success(request, 'Document status updated.')
        return redirect('care_manager:compliance', slug=slug)

    type_filter = request.GET.get('type', '')
    docs = ComplianceDocument.objects.filter(business=biz).select_related('created_by__user')
    if type_filter:
        docs = docs.filter(doc_type=type_filter)

    return render(request, 'care_manager/compliance.html', {
        'biz': biz,
        'access_level': level,
        'docs': docs,
        'type_filter': type_filter,
        'doc_types': ComplianceDocument.DOC_TYPE_CHOICES,
        'today': datetime.date.today(),
    })
