from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
import datetime
from hub.models import BusinessInstance, BusinessEmployee
from .models import HousekeepingSchedule, MaintenanceTicket, ServiceRequest, ConciergeNote


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
def ops_home(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    today = datetime.date.today()

    pending_housekeeping = HousekeepingSchedule.objects.filter(
        business=biz, scheduled_date=today, status='pending'
    ).count()
    open_maintenance = MaintenanceTicket.objects.filter(
        business=biz, status__in=['open', 'assigned', 'in_progress']
    ).count()
    pending_service = ServiceRequest.objects.filter(business=biz, status='pending').count()
    vip_alerts = ConciergeNote.objects.filter(
        business=biz, note_type='vip_alert', is_resolved=False
    ).count()

    stats = {
        'pending_housekeeping': pending_housekeeping,
        'open_maintenance': open_maintenance,
        'pending_service': pending_service,
        'vip_alerts': vip_alerts,
    }

    todays_housekeeping = HousekeepingSchedule.objects.filter(
        business=biz, scheduled_date=today
    ).select_related('assigned_to__user')

    open_service_requests = ServiceRequest.objects.filter(
        business=biz, status__in=['pending', 'in_progress']
    ).select_related('assigned_to__user')

    return render(request, 'hospitality_ops/home.html', {
        'biz': biz,
        'access_level': level,
        'stats': stats,
        'todays_housekeeping': todays_housekeeping,
        'open_service_requests': open_service_requests,
    })


@login_required
def housekeeping(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    today = datetime.date.today()

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'add_task':
            assigned_id = request.POST.get('assigned_to')
            assigned = (
                BusinessEmployee.objects.filter(pk=assigned_id, business=biz).first()
                if assigned_id else None
            )
            HousekeepingSchedule.objects.create(
                business=biz,
                room_identifier=request.POST.get('room_identifier', ''),
                task_type=request.POST.get('task_type', 'checkout_clean'),
                status=request.POST.get('status', 'pending'),
                assigned_to=assigned,
                scheduled_date=request.POST.get('scheduled_date', today),
                priority=request.POST.get('priority', 'normal'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Housekeeping task added.')
        elif action == 'update_status':
            task = get_object_or_404(HousekeepingSchedule, pk=request.POST.get('task_id'), business=biz)
            new_status = request.POST.get('status', task.status)
            task.status = new_status
            if new_status == 'done' and not task.completed_at:
                task.completed_at = timezone.now()
            task.save(update_fields=['status', 'completed_at'])
            messages.success(request, 'Task status updated.')
        return redirect('hospitality_ops:housekeeping', slug=slug)

    date_str = request.GET.get('date', '')
    status_filter = request.GET.get('status', '')

    try:
        filter_date = datetime.date.fromisoformat(date_str) if date_str else today
    except ValueError:
        filter_date = today

    tasks = HousekeepingSchedule.objects.filter(
        business=biz, scheduled_date=filter_date
    ).select_related('assigned_to__user')

    if status_filter:
        tasks = tasks.filter(status=status_filter)

    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'hospitality_ops/housekeeping.html', {
        'biz': biz,
        'access_level': level,
        'tasks': tasks,
        'filter_date': filter_date,
        'status_filter': status_filter,
        'employees': employees,
    })


@login_required
def maintenance(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create_ticket' and level >= 2:
            ticket = MaintenanceTicket.objects.create(
                business=biz,
                room_identifier=request.POST.get('room_identifier', ''),
                location=request.POST.get('location', ''),
                category=request.POST.get('category', 'general'),
                description=request.POST.get('description', ''),
                priority=request.POST.get('priority', 'normal'),
                reported_by=emp,
                estimated_cost=request.POST.get('estimated_cost') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, f'Maintenance ticket {ticket.ticket_number} created.')

        elif action == 'assign_ticket' and level >= 3:
            ticket = get_object_or_404(MaintenanceTicket, pk=request.POST.get('ticket_id'), business=biz)
            assigned_id = request.POST.get('assigned_to')
            assigned = (
                BusinessEmployee.objects.filter(pk=assigned_id, business=biz).first()
                if assigned_id else None
            )
            ticket.assigned_to = assigned
            ticket.status = 'assigned'
            ticket.save(update_fields=['assigned_to', 'status'])
            messages.success(request, f'Ticket {ticket.ticket_number} assigned.')

        elif action == 'resolve_ticket' and level >= 3:
            ticket = get_object_or_404(MaintenanceTicket, pk=request.POST.get('ticket_id'), business=biz)
            ticket.status = 'resolved'
            ticket.resolved_at = timezone.now()
            ticket.actual_cost = request.POST.get('actual_cost') or ticket.actual_cost
            ticket.save(update_fields=['status', 'resolved_at', 'actual_cost'])
            messages.success(request, f'Ticket {ticket.ticket_number} resolved.')

        return redirect('hospitality_ops:maintenance', slug=slug)

    status_filter = request.GET.get('status', '')
    tickets = MaintenanceTicket.objects.filter(business=biz).select_related(
        'reported_by__user', 'assigned_to__user'
    )
    if status_filter:
        tickets = tickets.filter(status=status_filter)

    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'hospitality_ops/maintenance.html', {
        'biz': biz,
        'access_level': level,
        'tickets': tickets,
        'status_filter': status_filter,
        'employees': employees,
    })


@login_required
def service_requests(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')

        if action == 'create_request':
            assigned_id = request.POST.get('assigned_to')
            assigned = (
                BusinessEmployee.objects.filter(pk=assigned_id, business=biz).first()
                if assigned_id else None
            )
            ServiceRequest.objects.create(
                business=biz,
                room_identifier=request.POST.get('room_identifier', ''),
                guest_name=request.POST.get('guest_name', ''),
                request_type=request.POST.get('request_type', 'concierge'),
                description=request.POST.get('description', ''),
                priority=request.POST.get('priority', 'normal'),
                assigned_to=assigned,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Service request created.')

        elif action == 'update_request':
            sr = get_object_or_404(ServiceRequest, pk=request.POST.get('request_id'), business=biz)
            new_status = request.POST.get('status', sr.status)
            sr.status = new_status
            if new_status == 'completed' and not sr.completed_at:
                sr.completed_at = timezone.now()
            sr.save(update_fields=['status', 'completed_at'])
            messages.success(request, 'Service request updated.')

        return redirect('hospitality_ops:service_requests', slug=slug)

    status_filter = request.GET.get('status', '')
    srs = ServiceRequest.objects.filter(business=biz).select_related('assigned_to__user')
    if status_filter:
        srs = srs.filter(status=status_filter)

    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'hospitality_ops/service_requests.html', {
        'biz': biz,
        'access_level': level,
        'service_requests': srs,
        'status_filter': status_filter,
        'employees': employees,
    })


@login_required
def concierge(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')

        if action == 'add_note':
            ConciergeNote.objects.create(
                business=biz,
                guest_name=request.POST.get('guest_name', ''),
                note_type=request.POST.get('note_type', 'preference'),
                content=request.POST.get('content', ''),
                created_by=emp,
            )
            messages.success(request, 'Concierge note added.')

        elif action == 'resolve_note':
            note = get_object_or_404(ConciergeNote, pk=request.POST.get('note_id'), business=biz)
            note.is_resolved = True
            note.save(update_fields=['is_resolved'])
            messages.success(request, 'Note marked as resolved.')

        return redirect('hospitality_ops:concierge', slug=slug)

    notes = ConciergeNote.objects.filter(business=biz).select_related('created_by__user')

    return render(request, 'hospitality_ops/concierge.html', {
        'biz': biz,
        'access_level': level,
        'notes': notes,
    })
