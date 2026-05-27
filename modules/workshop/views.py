import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import ServiceBay, JobCard, ServiceItem, JobStatusLog, VehicleServiceHistory


def _ws_check(slug, user, min_level=2):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


def _next_job_number(business):
    last = JobCard.objects.filter(business=business).order_by('-pk').first()
    if last:
        try:
            num = int(last.job_number) + 1
        except ValueError:
            num = JobCard.objects.filter(business=business).count() + 1
    else:
        num = 1
    return str(num).zfill(5)


@login_required(login_url='/accounts/login/')
def workshop_dashboard(request, slug):
    biz, err = _ws_check(slug, request.user)
    if err:
        return err

    status_counts = {}
    for s, _ in JobCard.STATUS:
        status_counts[s] = JobCard.objects.filter(business=biz, status=s).count()

    open_jobs = JobCard.objects.filter(
        business=biz,
        status__in=['received', 'diagnosing', 'in_progress', 'waiting_parts', 'waiting_approval']
    ).select_related('assigned_to', 'bay').order_by('priority', '-received_at')[:10]

    bays = ServiceBay.objects.filter(business=biz)
    today_ready = JobCard.objects.filter(business=biz, status='ready').count()

    return render(request, 'workshop/dashboard.html', {
        'biz': biz,
        'status_counts': status_counts,
        'open_jobs': open_jobs,
        'bays': bays,
        'today_ready': today_ready,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def job_card_list(request, slug):
    biz, err = _ws_check(slug, request.user)
    if err:
        return err

    status_filter = request.GET.get('status', '')
    search = request.GET.get('q', '').strip()
    jobs = JobCard.objects.filter(business=biz).select_related('assigned_to', 'bay')
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    if search:
        jobs = jobs.filter(
            vehicle_reg__icontains=search
        ) | JobCard.objects.filter(
            business=biz, customer_name__icontains=search
        ) | JobCard.objects.filter(
            business=biz, vehicle_make__icontains=search
        )

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    bays = ServiceBay.objects.filter(business=biz)

    return render(request, 'workshop/job_list.html', {
        'biz': biz,
        'jobs': jobs,
        'statuses': JobCard.STATUS,
        'status_filter': status_filter,
        'search': search,
        'employees': employees,
        'bays': bays,
        'service_types': JobCard.SERVICE_TYPES,
        'priorities': JobCard.PRIORITY,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def job_card_create(request, slug):
    biz, err = _ws_check(slug, request.user, min_level=3)
    if err:
        return err

    if request.method == 'POST':
        from hub.models import BusinessEmployee
        emp_id = request.POST.get('assigned_to_id', '')
        bay_id = request.POST.get('bay_id', '')
        est_completion = request.POST.get('estimated_completion', '') or None

        job = JobCard.objects.create(
            business=biz,
            job_number=_next_job_number(biz),
            customer_name=request.POST.get('customer_name', '').strip(),
            customer_phone=request.POST.get('customer_phone', '').strip(),
            customer_email=request.POST.get('customer_email', '').strip(),
            vehicle_make=request.POST.get('vehicle_make', '').strip(),
            vehicle_model=request.POST.get('vehicle_model', '').strip(),
            vehicle_year=request.POST.get('vehicle_year', '') or None,
            vehicle_reg=request.POST.get('vehicle_reg', '').strip().upper(),
            vin=request.POST.get('vin', '').strip(),
            colour=request.POST.get('colour', '').strip(),
            mileage_in=request.POST.get('mileage_in', '') or None,
            fuel_level=request.POST.get('fuel_level', '').strip(),
            service_type=request.POST.get('service_type', 'repair'),
            priority=request.POST.get('priority', 'normal'),
            customer_complaint=request.POST.get('customer_complaint', '').strip(),
            assigned_to_id=int(emp_id) if emp_id else None,
            bay_id=int(bay_id) if bay_id else None,
            estimated_completion=est_completion,
            created_by=request.user,
        )

        # Update or create service history record
        reg = job.vehicle_reg
        if reg:
            VehicleServiceHistory.objects.get_or_create(
                business=biz,
                vehicle_reg=reg,
                defaults={
                    'vehicle_make': job.vehicle_make,
                    'vehicle_model': job.vehicle_model,
                    'vehicle_year': job.vehicle_year,
                    'customer_name': job.customer_name,
                    'customer_phone': job.customer_phone,
                }
            )

        messages.success(request, f"Job card JC-{job.job_number} created.")
        return redirect('workshop:job_detail', slug=slug, job_id=job.pk)

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    bays = ServiceBay.objects.filter(business=biz)
    return render(request, 'workshop/job_form.html', {
        'biz': biz,
        'employees': employees,
        'bays': bays,
        'service_types': JobCard.SERVICE_TYPES,
        'priorities': JobCard.PRIORITY,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def job_card_detail(request, slug, job_id):
    biz, err = _ws_check(slug, request.user)
    if err:
        return err

    job = get_object_or_404(JobCard, pk=job_id, business=biz)
    level = get_access_level(biz, request.user)

    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'status' and level >= 3:
            old_status = job.status
            new_status = request.POST.get('status', job.status)
            note = request.POST.get('note', '').strip()
            job.status = new_status
            if new_status == 'collected' and not job.collected_at:
                job.collected_at = timezone.now()
            if new_status in ('ready', 'invoiced') and not job.completed_at:
                job.completed_at = timezone.now()
            job.save()
            JobStatusLog.objects.create(
                job_card=job, old_status=old_status, new_status=new_status,
                note=note, changed_by=request.user,
            )
            messages.success(request, f"Status updated to {job.get_status_display()}.")

        elif action == 'assign' and level >= 4:
            emp_id = request.POST.get('assigned_to_id', '')
            bay_id = request.POST.get('bay_id', '')
            job.assigned_to_id = int(emp_id) if emp_id else None
            job.bay_id = int(bay_id) if bay_id else None
            job.save(update_fields=['assigned_to', 'bay'])
            messages.success(request, "Assignment updated.")

        elif action == 'diagnosis' and level >= 3:
            job.diagnosis = request.POST.get('diagnosis', '').strip()
            job.work_done = request.POST.get('work_done', '').strip()
            job.internal_notes = request.POST.get('internal_notes', '').strip()
            job.mileage_out = request.POST.get('mileage_out', '') or None
            job.save(update_fields=['diagnosis', 'work_done', 'internal_notes', 'mileage_out'])
            messages.success(request, "Job details updated.")

        elif action == 'add_item' and level >= 3:
            ServiceItem.objects.create(
                job_card=job,
                item_type=request.POST.get('item_type', 'labour'),
                description=request.POST.get('description', '').strip(),
                part_number=request.POST.get('part_number', '').strip(),
                quantity=request.POST.get('quantity', 1),
                unit_price=request.POST.get('unit_price', 0),
                discount_percent=request.POST.get('discount_percent', 0),
            )
            messages.success(request, "Item added.")

        elif action == 'delete_item' and level >= 4:
            item_id = request.POST.get('item_id', '')
            if item_id:
                ServiceItem.objects.filter(pk=int(item_id), job_card=job).delete()

        elif action == 'notify':
            job.customer_notified = True
            job.notification_method = request.POST.get('notification_method', 'none')
            job.save(update_fields=['customer_notified', 'notification_method'])
            messages.success(request, "Customer notification recorded.")

        return redirect('workshop:job_detail', slug=slug, job_id=job_id)

    from hub.models import BusinessEmployee
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    bays = ServiceBay.objects.filter(business=biz)
    items = job.service_items.all()
    logs = job.status_logs.all()

    return render(request, 'workshop/job_detail.html', {
        'biz': biz,
        'job': job,
        'items': items,
        'logs': logs,
        'employees': employees,
        'bays': bays,
        'statuses': JobCard.STATUS,
        'item_types': ServiceItem.TYPES,
        'access_level': level,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def service_bays(request, slug):
    biz, err = _ws_check(slug, request.user, min_level=5)
    if err:
        return err

    if request.method == 'POST':
        action = request.POST.get('action', 'create')
        if action == 'create':
            ServiceBay.objects.create(
                business=biz,
                name=request.POST.get('name', '').strip(),
                bay_type=request.POST.get('bay_type', '').strip(),
            )
            messages.success(request, "Bay created.")
        elif action == 'status':
            bay_id = request.POST.get('bay_id', '')
            if bay_id:
                bay = get_object_or_404(ServiceBay, pk=int(bay_id), business=biz)
                bay.status = request.POST.get('status', bay.status)
                bay.save(update_fields=['status'])
        return redirect('workshop:service_bays', slug=slug)

    bays = ServiceBay.objects.filter(business=biz)
    return render(request, 'workshop/service_bays.html', {
        'biz': biz,
        'bays': bays,
        'statuses': ServiceBay.STATUS,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def vehicle_history(request, slug):
    biz, err = _ws_check(slug, request.user)
    if err:
        return err

    search = request.GET.get('q', '').strip()
    history = VehicleServiceHistory.objects.filter(business=biz)
    if search:
        history = history.filter(vehicle_reg__icontains=search) | VehicleServiceHistory.objects.filter(
            business=biz, customer_name__icontains=search)

    return render(request, 'workshop/vehicle_history.html', {
        'biz': biz,
        'history': history,
        'search': search,
        'is_owner': biz.owner == request.user,
    })


@login_required(login_url='/accounts/login/')
def vehicle_history_detail(request, slug, reg):
    biz, err = _ws_check(slug, request.user)
    if err:
        return err

    vehicle = get_object_or_404(VehicleServiceHistory, business=biz, vehicle_reg=reg.upper())
    jobs = biz.job_cards.filter(vehicle_reg=reg.upper()).order_by('-received_at')
    return render(request, 'workshop/vehicle_history_detail.html', {
        'biz': biz,
        'vehicle': vehicle,
        'jobs': jobs,
        'is_owner': biz.owner == request.user,
    })
