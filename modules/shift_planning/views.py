from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import ShiftTemplate, SchedulePeriod, Shift, ShiftSwapRequest

try:
    from modules.hr.models import Employee
except ImportError:
    Employee = None


def _biz(slug, user):
    return _get_business_for_user(slug, user)


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    today = timezone.now().date()
    stats = {
        'shifts_today': Shift.objects.filter(period__business=biz, date=today).count(),
        'open_periods': SchedulePeriod.objects.filter(business=biz, is_published=False).count(),
        'pending_swaps': ShiftSwapRequest.objects.filter(requester_shift__period__business=biz, status='pending').count(),
        'templates': ShiftTemplate.objects.filter(business=biz, is_active=True).count(),
    }
    recent_periods = SchedulePeriod.objects.filter(business=biz).order_by('-week_start')[:5]
    today_shifts = Shift.objects.filter(period__business=biz, date=today).select_related('employee', 'template')
    return render(request, 'shift_planning/index.html', {
        'biz': biz, 'stats': stats, 'recent_periods': recent_periods, 'today_shifts': today_shifts,
    })


@login_required(login_url='/accounts/login/')
def periods(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            SchedulePeriod.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                week_start=request.POST.get('week_start'),
                week_end=request.POST.get('week_end'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Schedule period created.')
        elif action == 'publish':
            period = get_object_or_404(SchedulePeriod, pk=request.POST.get('period_id'), business=biz)
            period.is_published = True
            period.published_by = request.user
            period.save(update_fields=['is_published', 'published_by'])
            messages.success(request, f'Period "{period.name}" published.')
        elif action == 'delete':
            SchedulePeriod.objects.filter(pk=request.POST.get('period_id'), business=biz).delete()
            messages.success(request, 'Period deleted.')
        return redirect('shift_planning:periods', slug=slug)
    all_periods = SchedulePeriod.objects.filter(business=biz).order_by('-week_start')
    return render(request, 'shift_planning/periods.html', {'biz': biz, 'periods': all_periods})


@login_required(login_url='/accounts/login/')
def schedule(request, slug, period_id):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    period = get_object_or_404(SchedulePeriod, pk=period_id, business=biz)
    shifts = period.shifts.select_related('employee', 'template').order_by('date', 'start_time')
    employees = Employee.objects.filter(business=biz, status='active') if Employee else []
    templates = ShiftTemplate.objects.filter(business=biz, is_active=True)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_shift':
            emp = get_object_or_404(Employee, pk=request.POST.get('employee'), business=biz) if Employee else None
            template_id = request.POST.get('template')
            start_time = request.POST.get('start_time')
            end_time = request.POST.get('end_time')
            if template_id:
                tmpl = ShiftTemplate.objects.get(pk=template_id)
                start_time = start_time or str(tmpl.start_time)
                end_time = end_time or str(tmpl.end_time)
            Shift.objects.create(
                period=period, employee=emp,
                template_id=template_id or None,
                date=request.POST.get('date'),
                start_time=start_time, end_time=end_time,
                break_minutes=request.POST.get('break_minutes', 0) or 0,
                role=request.POST.get('role', '').strip(),
                department=request.POST.get('department', '').strip(),
                created_by=request.user,
            )
            messages.success(request, 'Shift added.')
        elif action == 'delete_shift':
            Shift.objects.filter(pk=request.POST.get('shift_id'), period=period).delete()
            messages.success(request, 'Shift removed.')
        elif action == 'update_status':
            shift = get_object_or_404(Shift, pk=request.POST.get('shift_id'), period=period)
            shift.status = request.POST.get('status', shift.status)
            shift.save(update_fields=['status'])
            messages.success(request, 'Shift status updated.')
        return redirect('shift_planning:schedule', slug=slug, period_id=period_id)
    return render(request, 'shift_planning/schedule.html', {
        'biz': biz, 'period': period, 'shifts': shifts,
        'employees': employees, 'templates': templates,
    })


@login_required(login_url='/accounts/login/')
def shift_templates(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            ShiftTemplate.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                start_time=request.POST.get('start_time'),
                end_time=request.POST.get('end_time'),
                break_minutes=request.POST.get('break_minutes', 0) or 0,
                color=request.POST.get('color', '#3b82f6').strip(),
                department=request.POST.get('department', '').strip(),
            )
            messages.success(request, 'Shift template created.')
        elif action == 'delete':
            ShiftTemplate.objects.filter(pk=request.POST.get('template_id'), business=biz).delete()
            messages.success(request, 'Template deleted.')
        return redirect('shift_planning:shift_templates', slug=slug)
    all_templates = ShiftTemplate.objects.filter(business=biz)
    return render(request, 'shift_planning/shift_templates.html', {'biz': biz, 'templates': all_templates})


@login_required(login_url='/accounts/login/')
def swap_requests(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    swaps = ShiftSwapRequest.objects.filter(
        requester_shift__period__business=biz
    ).select_related('requester_shift__employee', 'target_shift__employee', 'reviewed_by').order_by('-created_at')
    if request.method == 'POST':
        action = request.POST.get('action')
        swap = get_object_or_404(ShiftSwapRequest, pk=request.POST.get('swap_id'), requester_shift__period__business=biz)
        if action in ('approve', 'reject'):
            swap.status = 'approved' if action == 'approve' else 'rejected'
            swap.reviewed_by = request.user
            swap.save(update_fields=['status', 'reviewed_by'])
            messages.success(request, f'Swap request {swap.status}.')
        return redirect('shift_planning:swap_requests', slug=slug)
    return render(request, 'shift_planning/swap_requests.html', {'biz': biz, 'swaps': swaps})
