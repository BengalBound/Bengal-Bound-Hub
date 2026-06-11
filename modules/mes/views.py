from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.db.models import Count, Avg

from hub.views import _get_business_for_user
from hub.access import get_access_level
from .models import WorkCenter, ProductionOrder, ProductionLog, QualityCheck, DowntimeRecord, OEESnapshot, RoutingStation, FootwearProductionSchedule, ProductionDayEntry
from modules.quality_control.models import Inspection
from modules.asset_management.models import Asset


def _mes_check(slug, user, min_level=4):
    biz = _get_business_for_user(slug, user)
    if not biz:
        return None, HttpResponseForbidden()
    if get_access_level(biz, user) < min_level:
        return None, HttpResponseForbidden()
    return biz, None


@login_required(login_url='/accounts/login/')
def mes_dashboard(request, slug):
    biz, err = _mes_check(slug, request.user)
    if err:
        return err

    work_centers = WorkCenter.objects.filter(business=biz)
    active_orders = ProductionOrder.objects.filter(business=biz, status__in=['released', 'in_progress'])
    recent_checks = QualityCheck.objects.filter(production_order__business=biz).order_by('-inspected_at')[:5]

    status_counts = {
        'planned': ProductionOrder.objects.filter(business=biz, status='planned').count(),
        'in_progress': ProductionOrder.objects.filter(business=biz, status='in_progress').count(),
        'completed': ProductionOrder.objects.filter(business=biz, status='completed').count(),
        'paused': ProductionOrder.objects.filter(business=biz, status='paused').count(),
    }

    bottleneck_stations = RoutingStation.objects.filter(routing__business=biz).annotate(
        active_count=Count('active_orders')
    ).order_by('-active_count')[:5]

    return render(request, 'mes/dashboard.html', {
        'biz': biz,
        'work_centers': work_centers,
        'active_orders': active_orders,
        'recent_checks': recent_checks,
        'status_counts': status_counts,
        'bottleneck_stations': bottleneck_stations,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def executive_dashboard(request, slug):
    biz, err = _mes_check(slug, request.user)
    if err:
        return err

    total_wip_orders = ProductionOrder.objects.filter(business=biz, status='in_progress').count()

    avg_oee_val = OEESnapshot.objects.filter(work_center__business=biz).aggregate(Avg('oee'))['oee__avg']
    avg_oee = round(avg_oee_val, 2) if avg_oee_val else 0

    total_inspections = Inspection.objects.filter(business=biz).count()
    passed_inspections = Inspection.objects.filter(business=biz, result='pass').count()
    aql_pass_rate = round((passed_inspections / total_inspections * 100), 1) if total_inspections > 0 else 100

    worn_assets = Asset.objects.filter(business=biz, is_tooling=True, lifespan_capacity__gt=0)
    wear_alerts = [a for a in worn_assets if (a.lifespan_consumed / a.lifespan_capacity) > 0.9]

    return render(request, 'mes/executive_dashboard.html', {
        'biz': biz,
        'total_wip_orders': total_wip_orders,
        'avg_oee': avg_oee,
        'aql_pass_rate': aql_pass_rate,
        'wear_alerts': wear_alerts,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def mes_work_centers(request, slug):
    biz, err = _mes_check(slug, request.user)
    if err:
        return err

    if request.method == 'POST' and get_access_level(biz, request.user) >= 6:
        from hub.models import BusinessEmployee
        op_id = request.POST.get('operator_id', '')
        WorkCenter.objects.create(
            business=biz,
            code=request.POST.get('code', '').strip(),
            name=request.POST.get('name', '').strip(),
            description=request.POST.get('description', '').strip(),
            capacity_per_hour=request.POST.get('capacity_per_hour', 0) or 0,
            machine_id=request.POST.get('machine_id', '').strip(),
            location=request.POST.get('location', '').strip(),
            operator_id=int(op_id) if op_id else None,
        )
        messages.success(request, "Work center created.")
        return redirect('mes:work_centers', slug=slug)

    from hub.models import BusinessEmployee
    centers = WorkCenter.objects.filter(business=biz).select_related('operator')
    employees = BusinessEmployee.objects.filter(business=biz, is_active=True)
    return render(request, 'mes/work_centers.html', {
        'biz': biz,
        'centers': centers,
        'employees': employees,
        'statuses': WorkCenter.STATUS,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def mes_production_orders(request, slug):
    biz, err = _mes_check(slug, request.user)
    if err:
        return err

    status_filter = request.GET.get('status', '')
    orders = ProductionOrder.objects.filter(business=biz).select_related('work_center')
    if status_filter:
        orders = orders.filter(status=status_filter)

    if request.method == 'POST' and get_access_level(biz, request.user) >= 5:
        wc_id = request.POST.get('work_center_id', '')
        import random
        import string
        wo_num = f"WO-{''.join(random.choices(string.digits, k=6))}"
        ProductionOrder.objects.create(
            business=biz,
            order_number=wo_num,
            product_name=request.POST.get('product_name', '').strip(),
            product_code=request.POST.get('product_code', '').strip(),
            quantity_planned=request.POST.get('quantity_planned', 1),
            unit=request.POST.get('unit', 'pcs'),
            priority=request.POST.get('priority', 'normal'),
            work_center_id=int(wc_id) if wc_id else None,
            notes=request.POST.get('notes', '').strip(),
            created_by=request.user,
        )
        messages.success(request, "Production order created.")
        return redirect('mes:production_orders', slug=slug)

    work_centers = WorkCenter.objects.filter(business=biz)
    return render(request, 'mes/production_orders.html', {
        'biz': biz,
        'orders': orders,
        'work_centers': work_centers,
        'statuses': ProductionOrder.STATUS,
        'priorities': ProductionOrder.PRIORITY,
        'status_filter': status_filter,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def mes_production_order_detail(request, slug, order_id):
    biz, err = _mes_check(slug, request.user)
    if err:
        return err

    order = get_object_or_404(ProductionOrder, pk=order_id, business=biz)

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'log':
            qty = request.POST.get('quantity', '')
            ProductionLog.objects.create(
                production_order=order,
                action=request.POST.get('log_action', 'note'),
                quantity=float(qty) if qty else None,
                note=request.POST.get('note', '').strip(),
                recorded_by=request.user,
            )
            if qty:
                order.quantity_produced += float(qty)
                order.save(update_fields=['quantity_produced'])
        elif action == 'status' and get_access_level(biz, request.user) >= 5:
            new_status = request.POST.get('status', order.status)
            order.status = new_status
            if new_status == 'in_progress' and not order.actual_start:
                order.actual_start = timezone.now()
            elif new_status == 'completed' and not order.actual_end:
                order.actual_end = timezone.now()
            order.save()
        elif action == 'qc':
            QualityCheck.objects.create(
                production_order=order,
                checkpoint=request.POST.get('checkpoint', '').strip(),
                result=request.POST.get('result', 'pass'),
                measured_value=request.POST.get('measured_value', '').strip(),
                acceptable_range=request.POST.get('acceptable_range', '').strip(),
                defect_description=request.POST.get('defect_description', '').strip(),
                inspected_by=request.user,
            )
        messages.success(request, "Updated.")
        return redirect('mes:order_detail', slug=slug, order_id=order_id)

    return render(request, 'mes/order_detail.html', {
        'biz': biz,
        'order': order,
        'logs': order.logs.all(),
        'quality_checks': order.quality_checks.all(),
        'log_actions': ProductionLog.ACTIONS,
        'qc_results': QualityCheck.RESULT,
        'statuses': ProductionOrder.STATUS,
        'is_owner': biz.owner == request.user,
        'access_level': get_access_level(biz, request.user),
    })


@login_required(login_url='/accounts/login/')
def mes_downtime(request, slug):
    biz, err = _mes_check(slug, request.user)
    if err:
        return err

    if request.method == 'POST':
        wc_id = request.POST.get('work_center_id', '')
        if not wc_id:
            messages.error(request, "Work center is required.")
            return redirect('mes:downtime', slug=slug)
        DowntimeRecord.objects.create(
            work_center_id=int(wc_id),
            category=request.POST.get('category', 'other'),
            description=request.POST.get('description', '').strip(),
            started_at=request.POST.get('started_at') or timezone.now(),
            recorded_by=request.user,
        )
        messages.success(request, "Downtime recorded.")
        return redirect('mes:downtime', slug=slug)

    work_centers = WorkCenter.objects.filter(business=biz)
    records = DowntimeRecord.objects.filter(work_center__business=biz).select_related('work_center').order_by('-started_at')[:30]
    return render(request, 'mes/downtime.html', {
        'biz': biz,
        'work_centers': work_centers,
        'records': records,
        'categories': DowntimeRecord.CATEGORIES,
        'is_owner': biz.owner == request.user,
    })


# ── Footwear Production Schedule Views ───────────────────────────────────────

@login_required(login_url='/accounts/login/')
def footwear_schedule_list(request, slug):
    biz, err = _mes_check(slug, request.user, min_level=2)
    if err:
        return err
    level = get_access_level(biz, request.user)

    if request.method == 'POST' and level >= 3:
        sched = FootwearProductionSchedule.objects.create(
            business=biz,
            article_code=request.POST.get('article_code', '').strip(),
            buyer=request.POST.get('buyer', '').strip(),
            footwear_type=request.POST.get('footwear_type', 'other'),
            total_pairs_planned=request.POST.get('total_pairs_planned', 0) or 0,
            start_date=request.POST.get('start_date', ''),
            created_by=request.user,
        )
        # Auto-create 12 day entries from the standard plan
        DEFAULT_PLAN = [
            ('D-3', 'pre_d3', 'Material verification, last issue, pattern release, marker check', 0, 'Product Developer + Merchandiser'),
            ('D-2', 'pre_d2', 'Pilot run (10 pairs / type), trim grading, line set-up', 50, 'Production In-Charge'),
            ('D-1', 'pre_d1', 'Cutting dies finalized, leather inspection, shade sorting', 0, 'Cutting Supervisor'),
            ('1', 'cutting', 'Leather + lining cutting; shade & defect sorting', 300, 'Cutting Supervisor'),
            ('2', 'cutting', 'Cutting continues; skiving, splitting, eyelet punching', 300, 'Cutting Supervisor'),
            ('3', 'closing', 'Upper assembly, logo attach, decorative stitching', 250, 'Sewing Executive'),
            ('4', 'closing', 'Stitch density audit, lining attach, eyelet set', 300, 'Sewing Executive'),
            ('5', 'closing', 'Sewing completion + in-line QC of uppers', 350, 'Sewing Executive + QC'),
            ('6', 'lasting', 'Insole tacking, toe & heel lasting, heat-setting', 300, 'Lasting In-Charge'),
            ('7', 'lasting', 'Side-lasting, sole roughing, primer application', 350, 'Lasting In-Charge'),
            ('8', 'bottoming', 'Cementing, sole press (chiller pass), heel attach', 400, 'Lasting In-Charge'),
            ('9', 'bottoming', 'Sole press completion, de-lasting, sock liner insert', 450, 'Lasting In-Charge'),
            ('10', 'finishing', 'Cleaning, polishing, lace-up, branding, hangtags', 500, 'Finishing In-Charge'),
            ('11', 'qc', 'Final inspection (AQL 2.5), packing in inner boxes', 500, 'Finishing + QC'),
            ('12', 'packout', 'Carton packing, shipping marks, pre-shipment audit', 500, 'Warehouse + QC'),
        ]
        cumulative = 0
        for day_label, stage, activities, target, owner in DEFAULT_PLAN:
            cumulative += target
            ProductionDayEntry.objects.create(
                schedule=sched,
                day_label=day_label,
                stage=stage,
                key_activities=activities,
                daily_target=target,
                cumulative_target=cumulative,
                owner=owner,
            )
        messages.success(request, 'Production schedule created with 15 day entries.')
        return redirect('mes:footwear_schedule_detail', slug=slug, schedule_id=sched.pk)

    schedules = FootwearProductionSchedule.objects.filter(business=biz).prefetch_related('day_entries')
    return render(request, 'mes/footwear_schedule_list.html', {
        'biz': biz,
        'schedules': schedules,
        'access_level': level,
        'footwear_types': FootwearProductionSchedule.FOOTWEAR_TYPE,
    })


@login_required(login_url='/accounts/login/')
def footwear_schedule_detail(request, slug, schedule_id):
    biz, err = _mes_check(slug, request.user, min_level=2)
    if err:
        return err
    level = get_access_level(biz, request.user)
    schedule = get_object_or_404(FootwearProductionSchedule, pk=schedule_id, business=biz)

    if request.method == 'POST' and level >= 2:
        action = request.POST.get('action')
        if action == 'update_day':
            entry = get_object_or_404(ProductionDayEntry, pk=request.POST.get('entry_id'), schedule=schedule)
            entry.actual_output = request.POST.get('actual_output', 0) or 0
            entry.production_date = request.POST.get('production_date') or None
            entry.bottleneck = request.POST.get('bottleneck', '').strip()
            entry.save(update_fields=['actual_output', 'production_date', 'bottleneck'])
            # Recompute cumulative actuals
            running = 0
            for e in schedule.day_entries.order_by('day_label'):
                running += e.actual_output
                if e.cumulative_actual != running:
                    e.cumulative_actual = running
                    e.save(update_fields=['cumulative_actual'])
            messages.success(request, f'Day {entry.day_label} updated.')
        return redirect('mes:footwear_schedule_detail', slug=slug, schedule_id=schedule_id)

    day_entries = schedule.day_entries.all()
    return render(request, 'mes/footwear_schedule_detail.html', {
        'biz': biz,
        'schedule': schedule,
        'day_entries': day_entries,
        'access_level': level,
        'stages': ProductionDayEntry.STAGE,
    })
