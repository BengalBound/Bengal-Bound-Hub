from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from hub.models import BusinessInstance, BusinessEmployee
from .models import RetailStore, StoreReport, StoreTask


def _so_check(slug, user, min_level=1):
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
def store_ops_home(request, slug):
    biz, emp, level = _so_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    stores = RetailStore.objects.filter(business=biz)
    today = timezone.now().date()
    today_reports = StoreReport.objects.filter(store__business=biz, report_date=today).select_related('store')
    open_tasks = StoreTask.objects.filter(store__business=biz, is_done=False).select_related('store')

    today_sales = sum(r.sales_total or 0 for r in today_reports)

    stats = {
        'stores': stores.count(),
        'active_stores': stores.filter(is_active=True).count(),
        'reported_today': today_reports.count(),
        'open_tasks': open_tasks.count(),
        'today_sales': today_sales,
    }

    return render(request, 'store_ops/home.html', {
        'biz': biz, 'access_level': level, 'stats': stats,
        'stores': stores, 'today_reports': today_reports, 'open_tasks': open_tasks[:10],
    })


@login_required
def store_list(request, slug):
    biz, emp, level = _so_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    if request.method == 'POST' and level >= 3:
        action = request.POST.get('action')
        if action == 'create_store':
            mgr_id = request.POST.get('manager_id')
            manager = BusinessEmployee.objects.filter(pk=mgr_id, business=biz).first() if mgr_id else None
            RetailStore.objects.create(
                business=biz,
                name=request.POST.get('name', ''),
                address=request.POST.get('address', ''),
                phone=request.POST.get('phone', ''),
                manager=manager,
                opening_time=request.POST.get('opening_time') or None,
                closing_time=request.POST.get('closing_time') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Store added.')
        elif action == 'toggle_store':
            store = get_object_or_404(RetailStore, pk=request.POST.get('store_id'), business=biz)
            store.is_active = not store.is_active
            store.save(update_fields=['is_active'])
        return redirect('store_ops:store_list', slug=slug)

    stores = RetailStore.objects.filter(business=biz)
    return render(request, 'store_ops/store_list.html', {
        'biz': biz, 'access_level': level, 'stores': stores, 'employees': employees,
    })


@login_required
def store_detail(request, slug, store_id):
    biz, emp, level = _so_check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    store = get_object_or_404(RetailStore, pk=store_id, business=biz)
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_report' and level >= 2:
            report_date = request.POST.get('report_date', '')
            report, created = StoreReport.objects.update_or_create(
                store=store, report_date=report_date,
                defaults={
                    'sales_total': request.POST.get('sales_total') or None,
                    'transaction_count': request.POST.get('transaction_count') or None,
                    'top_selling_product': request.POST.get('top_selling_product', ''),
                    'notes': request.POST.get('notes', ''),
                    'submitted_by': emp,
                }
            )
            messages.success(request, 'Daily report saved.')
        elif action == 'add_task' and level >= 2:
            assignee_id = request.POST.get('assigned_to_id')
            assignee = BusinessEmployee.objects.filter(pk=assignee_id, business=biz).first() if assignee_id else None
            StoreTask.objects.create(
                store=store,
                title=request.POST.get('title', ''),
                description=request.POST.get('description', ''),
                assigned_to=assignee,
                due_date=request.POST.get('due_date') or None,
                priority=request.POST.get('priority', 'medium'),
            )
            messages.success(request, 'Task added.')
        elif action == 'complete_task':
            task = get_object_or_404(StoreTask, pk=request.POST.get('task_id'), store=store)
            task.is_done = True
            task.save(update_fields=['is_done'])
        elif action == 'delete_task' and level >= 3:
            StoreTask.objects.filter(pk=request.POST.get('task_id'), store=store).delete()
        return redirect('store_ops:store_detail', slug=slug, store_id=store_id)

    reports = store.reports.all()[:30]
    tasks = store.tasks.all()
    return render(request, 'store_ops/store_detail.html', {
        'biz': biz, 'access_level': level, 'store': store,
        'reports': reports, 'tasks': tasks, 'employees': employees,
        'priority_choices': StoreTask.PRIORITY,
    })
