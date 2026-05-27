import datetime
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F
from hub.models import BusinessInstance, BusinessEmployee
from .models import ClientSite, GardenJob, GardenInventoryItem


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
def garden_home(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    today = datetime.date.today()
    total_sites = ClientSite.objects.filter(business=biz, is_active=True).count()
    pending_jobs = GardenJob.objects.filter(business=biz, status__in=['pending', 'scheduled']).count()
    jobs_today = GardenJob.objects.filter(business=biz, scheduled_date=today).count()
    low_stock = GardenInventoryItem.objects.filter(
        business=biz,
        low_stock_threshold__isnull=False,
        quantity__lte=F('low_stock_threshold'),
    ).count()

    recent_jobs = GardenJob.objects.filter(business=biz).select_related(
        'site', 'assigned_to__user'
    ).order_by('-created_at')[:8]

    return render(request, 'garden_ops/home.html', {
        'biz': biz,
        'access_level': level,
        'stats': {
            'total_sites': total_sites,
            'pending_jobs': pending_jobs,
            'jobs_today': jobs_today,
            'low_stock': low_stock,
        },
        'recent_jobs': recent_jobs,
    })


@login_required
def site_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'add_site':
            assigned_id = request.POST.get('assigned_to_id')
            assigned = BusinessEmployee.objects.filter(pk=assigned_id, business=biz).first() if assigned_id else None
            site = ClientSite.objects.create(
                business=biz,
                client_name=request.POST['client_name'],
                site_name=request.POST.get('site_name', ''),
                address=request.POST.get('address', ''),
                site_type=request.POST.get('site_type', 'residential'),
                area_sqm=request.POST.get('area_sqm') or None,
                contact_phone=request.POST.get('contact_phone', ''),
                contact_email=request.POST.get('contact_email', ''),
                assigned_to=assigned,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, f'Site "{site.client_name}" added.')
            return redirect('garden_ops:site_detail', slug=slug, site_id=site.pk)
        return redirect('garden_ops:site_list', slug=slug)

    type_filter = request.GET.get('type', '')
    sites = ClientSite.objects.filter(business=biz, is_active=True).select_related('assigned_to__user')
    if type_filter:
        sites = sites.filter(site_type=type_filter)

    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'garden_ops/site_list.html', {
        'biz': biz,
        'access_level': level,
        'sites': sites,
        'type_filter': type_filter,
        'site_types': ClientSite.SITE_TYPE_CHOICES,
        'employees': employees,
    })


@login_required
def site_detail(request, slug, site_id):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    site = get_object_or_404(ClientSite, pk=site_id, business=biz)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'add_job':
            assigned_id = request.POST.get('assigned_to_id')
            assigned = BusinessEmployee.objects.filter(pk=assigned_id, business=biz).first() if assigned_id else None
            GardenJob.objects.create(
                business=biz,
                site=site,
                title=request.POST['title'],
                job_type=request.POST.get('job_type', 'maintenance'),
                status='scheduled',
                scheduled_date=request.POST.get('scheduled_date') or None,
                assigned_to=assigned,
                estimated_hours=request.POST.get('estimated_hours') or None,
                estimated_cost=request.POST.get('estimated_cost') or None,
                currency=request.POST.get('currency', 'USD'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Job added.')
        return redirect('garden_ops:site_detail', slug=slug, site_id=site_id)

    jobs = GardenJob.objects.filter(site=site).select_related('assigned_to__user').order_by('-created_at')
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)

    return render(request, 'garden_ops/site_detail.html', {
        'biz': biz,
        'access_level': level,
        'site': site,
        'jobs': jobs,
        'employees': employees,
        'job_types': GardenJob.JOB_TYPE_CHOICES,
        'job_statuses': GardenJob.STATUS_CHOICES,
    })


@login_required
def job_list(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'update_job_status':
            job = get_object_or_404(GardenJob, pk=request.POST.get('job_id'), business=biz)
            new_status = request.POST.get('status')
            if new_status in dict(GardenJob.STATUS_CHOICES):
                job.status = new_status
                if new_status == 'completed':
                    job.completed_date = datetime.date.today()
                    job.actual_hours = request.POST.get('actual_hours') or job.actual_hours
                    job.actual_cost = request.POST.get('actual_cost') or job.actual_cost
                    job.save(update_fields=['status', 'completed_date', 'actual_hours', 'actual_cost'])
                else:
                    job.save(update_fields=['status'])
                messages.success(request, f'Job updated to {job.get_status_display()}.')
        return redirect('garden_ops:job_list', slug=slug)

    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')
    jobs = GardenJob.objects.filter(business=biz).select_related('site', 'assigned_to__user')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    if type_filter:
        jobs = jobs.filter(job_type=type_filter)

    return render(request, 'garden_ops/job_list.html', {
        'biz': biz,
        'access_level': level,
        'jobs': jobs,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'job_types': GardenJob.JOB_TYPE_CHOICES,
        'job_statuses': GardenJob.STATUS_CHOICES,
    })


@login_required
def inventory(request, slug):
    biz, emp, level = _check(slug, request.user)
    if not level:
        return redirect('hub:hub_dashboard', slug=slug)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'add_item':
            GardenInventoryItem.objects.create(
                business=biz,
                name=request.POST['name'],
                category=request.POST.get('category', 'plant'),
                quantity=request.POST.get('quantity', 0),
                unit=request.POST.get('unit', 'each'),
                cost_per_unit=request.POST.get('cost_per_unit') or None,
                supplier=request.POST.get('supplier', ''),
                low_stock_threshold=request.POST.get('low_stock_threshold') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Item added to inventory.')
        elif action == 'adjust_qty':
            item = get_object_or_404(GardenInventoryItem, pk=request.POST.get('item_id'), business=biz)
            item.quantity = request.POST.get('quantity', item.quantity)
            item.save(update_fields=['quantity'])
            messages.success(request, f'Quantity updated for {item.name}.')
        return redirect('garden_ops:inventory', slug=slug)

    cat_filter = request.GET.get('cat', '')
    items = GardenInventoryItem.objects.filter(business=biz)
    if cat_filter:
        items = items.filter(category=cat_filter)

    return render(request, 'garden_ops/inventory.html', {
        'biz': biz,
        'access_level': level,
        'items': items,
        'cat_filter': cat_filter,
        'categories': GardenInventoryItem.CATEGORY_CHOICES,
    })
