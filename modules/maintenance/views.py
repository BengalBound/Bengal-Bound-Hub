from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import Asset, WorkOrder, MaintenanceSchedule


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _next_wo_number(biz):
    count = WorkOrder.objects.filter(business=biz).count() + 1
    return f"WO-{count:04d}"


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    today = timezone.now().date()
    total_assets = Asset.objects.filter(business=biz).count()
    open_work_orders = WorkOrder.objects.filter(business=biz, status__in=['open', 'assigned', 'in_progress']).count()
    overdue_schedules = MaintenanceSchedule.objects.filter(asset__business=biz, next_due__lt=today, is_active=True).count()
    completed_today = WorkOrder.objects.filter(business=biz, completed_at__date=today).count()
    recent_work_orders = WorkOrder.objects.filter(business=biz).order_by('-created_at')[:10]
    overdue = MaintenanceSchedule.objects.filter(asset__business=biz, next_due__lt=today, is_active=True).select_related('asset')
    return render(request, 'maintenance/index.html', {
        'biz': biz,
        'total_assets': total_assets,
        'open_work_orders': open_work_orders,
        'overdue_schedules': overdue_schedules,
        'completed_today': completed_today,
        'recent_work_orders': recent_work_orders,
        'overdue': overdue,
    })


@login_required(login_url='/accounts/login/')
def assets(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Asset.objects.create(
                business=biz, name=request.POST.get('name', '').strip(),
                asset_id=request.POST.get('asset_id', '').strip(),
                asset_type=request.POST.get('asset_type', 'equipment'),
                location=request.POST.get('location', ''), manufacturer=request.POST.get('manufacturer', ''),
                serial_number=request.POST.get('serial_number', ''),
                purchase_date=request.POST.get('purchase_date') or None,
                purchase_cost=request.POST.get('purchase_cost') or None,
            )
            messages.success(request, 'Asset added.')
        return redirect('maintenance:assets', slug=slug)
    all_assets = Asset.objects.filter(business=biz).order_by('name')
    return render(request, 'maintenance/assets.html', {'biz': biz, 'assets': all_assets})


@login_required(login_url='/accounts/login/')
def work_orders(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status = request.GET.get('status', '')
    qs = WorkOrder.objects.filter(business=biz).select_related('asset', 'assigned_to').order_by('-created_at')
    if status:
        qs = qs.filter(status=status)
    all_assets = Asset.objects.filter(business=biz, status='operational')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            WorkOrder.objects.create(
                business=biz, wo_number=_next_wo_number(biz),
                title=request.POST.get('title', '').strip(),
                description=request.POST.get('description', ''),
                work_type=request.POST.get('work_type', 'corrective'),
                priority=request.POST.get('priority', 'normal'),
                asset_id=request.POST.get('asset') or None,
                reported_by=request.user,
                assigned_to_id=request.POST.get('assigned_to') or None,
                scheduled_date=request.POST.get('scheduled_date') or None,
            )
            messages.success(request, 'Work order created.')
        elif action == 'update_status':
            wo = get_object_or_404(WorkOrder, pk=request.POST.get('wo_id'), business=biz)
            wo.status = request.POST.get('status', wo.status)
            if wo.status == 'completed':
                wo.completed_at = timezone.now()
            wo.completion_notes = request.POST.get('notes', wo.completion_notes)
            wo.save()
            messages.success(request, 'Work order updated.')
        return redirect('maintenance:work_orders', slug=slug)
    return render(request, 'maintenance/work_orders.html', {'biz': biz, 'work_orders': qs, 'assets': all_assets, 'status_filter': status})
