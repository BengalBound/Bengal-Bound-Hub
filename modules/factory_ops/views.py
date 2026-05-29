from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.db.models import Sum
import csv

from hub.models import BusinessInstance, BusinessEmployee
from .models import (
    ProductionOrder, ProductionPlan, RawMaterial, ProductSKU, WIPLot, FinishedGoodsLot,
    TimeStudy, SMVSheet, CapacityStudy, StyleCosting,
    DailyProductionReport, AttendanceSheet, MaterialIssue,
    QCInspection, ReworkRecord, FactorySOP,
    Buyer, SalesDeal, CustomerOrder, FactoryInvoice,
    Vendor, VendorPO, SupplierScore,
    DistributionChannel, WholesaleAccount, SalesRep, SalesTarget,
    FactoryTask, MarketingCampaign,
    ARAPEntry, BankAccount, LetterOfCredit,
    FactoryEmployee, ApprovalRequest,
    HourlyProductionEntry, PettyCash, WorkerAdvance,
    FactorySettings, StockMovement,
    KPITemplate, EmployeeEvaluation, SalesIncentive, SampleOrder,
)


def _biz(request, slug):
    """
    Resolve a BusinessInstance for the current user.
    Accepts: the business owner OR an active BusinessEmployee whose
    accessible_modules grants access to 'factory_ops'.
    Supports both legacy string format ["factory_ops"] and new dict
    format [{"module": "factory_ops", "role": "manager"}].
    """
    try:
        biz = BusinessInstance.objects.get(slug=slug)
    except BusinessInstance.DoesNotExist:
        raise Http404

    if biz.owner == request.user:
        return biz

    emp = BusinessEmployee.objects.filter(
        business=biz,
        user=request.user,
        is_active=True,
    ).first()
    if emp and emp.can_access_module('factory_ops'):
        return biz

    raise Http404


def _is_owner(request, biz):
    """True if the logged-in user is the business owner."""
    return biz.owner == request.user


def _get_settings(biz):
    """Return FactorySettings for a business, creating defaults if absent."""
    obj, _ = FactorySettings.objects.get_or_create(business=biz)
    return obj


def _next_id(prefix, qs, field='order_id'):
    today = timezone.now()
    base = f"{prefix}-{str(today.year)[2:]}{str(today.month).zfill(2)}"
    existing = qs.filter(**{f"{field}__startswith": base}).count()
    return f"{base}-{str(existing + 1).zfill(2)}"


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@login_required
def index(request, slug):
    biz = _biz(request, slug)
    today = timezone.now().date()

    active_orders   = ProductionOrder.objects.filter(business=biz).exclude(current_stage='shipped')
    overdue_orders  = [o for o in active_orders if o.is_overdue]
    low_stock_rm    = RawMaterial.objects.filter(business=biz).count()
    open_deals      = SalesDeal.objects.filter(business=biz).exclude(stage__in=['won', 'lost'])
    open_ar         = ARAPEntry.objects.filter(business=biz, entry_type='receivable', status__in=['open', 'overdue'])
    open_ap         = ARAPEntry.objects.filter(business=biz, entry_type='payable', status__in=['open', 'overdue'])
    pending_approvals = ApprovalRequest.objects.filter(business=biz, status='pending')
    open_tasks      = FactoryTask.objects.filter(business=biz).exclude(status__in=['done', 'cancelled'])
    headcount       = FactoryEmployee.objects.filter(business=biz, status__in=['active', 'probation']).count()
    open_pos        = VendorPO.objects.filter(business=biz).exclude(status='received')
    cash_position   = BankAccount.objects.filter(business=biz, is_active=True).aggregate(total=Sum('balance'))['total'] or 0
    total_ar        = open_ar.aggregate(total=Sum('amount'))['total'] or 0
    total_ap        = open_ap.aggregate(total=Sum('amount'))['total'] or 0
    overdue_ar      = open_ar.filter(status='overdue').aggregate(total=Sum('amount'))['total'] or 0

    # Low stock count using Python since we can't use F() cross-field easily
    rm_items = RawMaterial.objects.filter(business=biz)
    low_stock_count = sum(1 for r in rm_items if r.is_low_stock)

    return render(request, 'factory_ops/index.html', {
        'biz': biz,
        'active_orders_count': active_orders.count(),
        'overdue_orders_count': len(overdue_orders),
        'total_pairs_in_flow': active_orders.aggregate(total=Sum('qty'))['total'] or 0,
        'open_deals_count': open_deals.count(),
        'open_deals_value': open_deals.aggregate(total=Sum('value'))['total'] or 0,
        'total_ar': total_ar,
        'overdue_ar': overdue_ar,
        'total_ap': total_ap,
        'cash_position': cash_position,
        'low_stock_count': low_stock_count,
        'headcount': headcount,
        'open_pos_count': open_pos.count(),
        'pending_approvals_count': pending_approvals.count(),
        'open_tasks_count': open_tasks.count(),
        'recent_production': active_orders[:5],
        'recent_approvals': pending_approvals[:3],
        'attention_items': _attention_items(biz, today),
    })


def _attention_items(biz, today):
    items = []
    for o in ProductionOrder.objects.filter(business=biz).exclude(current_stage='shipped'):
        if o.is_overdue:
            items.append({'type': 'Production Overdue', 'desc': f"{o.order_id} · {o.style[:40]}", 'sev': 'red'})
    for e in ARAPEntry.objects.filter(business=biz, status='overdue'):
        items.append({'type': f"AR/AP Overdue ({e.entry_type.title()})", 'desc': f"{e.party} · {e.invoice_ref}", 'sev': 'red'})
    for r in ReworkRecord.objects.filter(business=biz, status__in=['open', 'in_progress']):
        items.append({'type': 'Open Rework', 'desc': f"{r.rework_id} · {r.defect_type[:40]}", 'sev': 'amber'})
    for t in FactoryTask.objects.filter(business=biz).exclude(status__in=['done', 'cancelled']):
        if t.is_overdue:
            items.append({'type': 'Task Overdue', 'desc': f"{t.title[:50]} → {t.assignee}", 'sev': 'amber'})
    for lc in LetterOfCredit.objects.filter(business=biz, status='active'):
        if lc.is_expiring_soon:
            items.append({'type': 'LC Expiring Soon', 'desc': f"{lc.lc_id} · {lc.description[:40]}", 'sev': 'amber'})
    return items[:10]


# ─── PRODUCTION ───────────────────────────────────────────────────────────────

@login_required
def production(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            ProductionOrder.objects.create(
                business=biz,
                order_id=_next_id('PO', ProductionOrder.objects.filter(business=biz)),
                style=request.POST.get('style', ''),
                buyer=request.POST.get('buyer', ''),
                qty=int(request.POST.get('qty') or 0),
                line=request.POST.get('line', ''),
                start_date=request.POST.get('start_date') or None,
                target_date=request.POST.get('target_date') or None,
                priority=request.POST.get('priority', 'med'),
                current_stage=request.POST.get('current_stage', 'planned'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Production order created.')
        elif action == 'delete':
            get_object_or_404(ProductionOrder, pk=request.POST.get('pk'), business=biz).delete()
            messages.success(request, 'Order deleted.')
        return redirect('factory_ops:production', slug=slug)

    stage_filter = request.GET.get('stage', '')
    qs = ProductionOrder.objects.filter(business=biz)
    if stage_filter:
        qs = qs.filter(current_stage=stage_filter)

    return render(request, 'factory_ops/production.html', {
        'biz': biz,
        'orders': qs,
        'stage_filter': stage_filter,
        'active_count': qs.exclude(current_stage='shipped').count(),
        'overdue_count': sum(1 for o in qs if o.is_overdue),
        'total_pairs': qs.aggregate(total=Sum('qty'))['total'] or 0,
        'stages': ProductionOrder.STAGE,
    })


@login_required
def production_detail(request, slug, pk):
    biz = _biz(request, slug)
    order = get_object_or_404(ProductionOrder, pk=pk, business=biz)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update':
            order.style         = request.POST.get('style', order.style)
            order.buyer         = request.POST.get('buyer', order.buyer)
            order.qty           = int(request.POST.get('qty') or order.qty)
            order.line          = request.POST.get('line', order.line)
            order.start_date    = request.POST.get('start_date') or order.start_date
            order.target_date   = request.POST.get('target_date') or order.target_date
            order.priority      = request.POST.get('priority', order.priority)
            order.current_stage = request.POST.get('current_stage', order.current_stage)
            order.notes         = request.POST.get('notes', order.notes)
            for stage in ['materials', 'cutting', 'stitching', 'lasting', 'sole', 'finishing', 'qc', 'packed', 'shipped']:
                setattr(order, f'stage_{stage}', request.POST.get(f'stage_{stage}') == 'on')
            order.save()
            messages.success(request, 'Order updated.')
        elif action == 'delete':
            order.delete()
            messages.success(request, 'Order deleted.')
            return redirect('factory_ops:production', slug=slug)
        return redirect('factory_ops:production_detail', slug=slug, pk=pk)
    return render(request, 'factory_ops/production_detail.html', {'biz': biz, 'order': order})


@login_required
def production_planning(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            ProductionPlan.objects.create(
                business=biz,
                plan_id=_next_id('PL', ProductionPlan.objects.filter(business=biz), 'plan_id'),
                style=request.POST.get('style', ''),
                buyer=request.POST.get('buyer', ''),
                qty=int(request.POST.get('qty') or 0),
                line=request.POST.get('line', ''),
                plan_start=request.POST.get('plan_start') or None,
                plan_end=request.POST.get('plan_end') or None,
                capacity_pct=int(request.POST.get('capacity_pct') or 80),
                status=request.POST.get('status', 'scheduled'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Plan added.')
        elif action == 'delete':
            get_object_or_404(ProductionPlan, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:planning', slug=slug)

    plans = ProductionPlan.objects.filter(business=biz)
    return render(request, 'factory_ops/planning.html', {
        'biz': biz, 'plans': plans,
        'total_qty': plans.aggregate(total=Sum('qty'))['total'] or 0,
        'scheduled': plans.filter(status='scheduled').count(),
    })


@login_required
def raw_materials(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            RawMaterial.objects.create(
                business=biz,
                item_id=_next_id('RM', RawMaterial.objects.filter(business=biz), 'item_id'),
                name=request.POST.get('name', ''),
                category=request.POST.get('category', 'Other'),
                uom=request.POST.get('uom', 'pcs'),
                on_hand=request.POST.get('on_hand') or 0,
                reorder_level=request.POST.get('reorder_level') or 0,
                unit_cost=request.POST.get('unit_cost') or 0,
                supplier=request.POST.get('supplier', ''),
                location=request.POST.get('location', ''),
                last_received=request.POST.get('last_received') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Material added.')
        elif action == 'delete':
            get_object_or_404(RawMaterial, pk=request.POST.get('pk'), business=biz).delete()
        elif action == 'adjust':
            rm = get_object_or_404(RawMaterial, pk=request.POST.get('pk'), business=biz)
            rm.on_hand = request.POST.get('on_hand') or rm.on_hand
            rm.save()
            messages.success(request, 'Stock adjusted.')
        return redirect('factory_ops:raw_materials', slug=slug)

    cat_filter = request.GET.get('cat', '')
    items = RawMaterial.objects.filter(business=biz)
    if cat_filter:
        items = items.filter(category=cat_filter)
    low_stock = [i for i in items if i.is_low_stock]
    return render(request, 'factory_ops/raw_materials.html', {
        'biz': biz, 'items': items,
        'low_stock_count': len(low_stock),
        'total_items': items.count(),
        'total_value': sum(i.stock_value for i in items),
        'cat_filter': cat_filter,
        'categories': [c[0] for c in RawMaterial._meta.get_field('category').choices],
    })


@login_required
def wip_inventory(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            WIPLot.objects.create(
                business=biz,
                wip_id=_next_id('WIP', WIPLot.objects.filter(business=biz), 'wip_id'),
                style=request.POST.get('style', ''),
                production_order_ref=request.POST.get('production_order_ref', ''),
                current_stage=request.POST.get('current_stage', 'cutting'),
                qty=int(request.POST.get('qty') or 0),
                line=request.POST.get('line', ''),
                wip_value=request.POST.get('wip_value') or 0,
                days_in_wip=int(request.POST.get('days_in_wip') or 0),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'WIP lot added.')
        elif action == 'delete':
            get_object_or_404(WIPLot, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:wip', slug=slug)

    lots = WIPLot.objects.filter(business=biz)
    return render(request, 'factory_ops/wip.html', {
        'biz': biz, 'lots': lots,
        'total_qty': lots.aggregate(total=Sum('qty'))['total'] or 0,
        'total_value': lots.aggregate(total=Sum('wip_value'))['total'] or 0,
        'aging_lots': lots.filter(days_in_wip__gte=30).count(),
    })


@login_required
def finished_goods(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            FinishedGoodsLot.objects.create(
                business=biz,
                fg_id=_next_id('FG', FinishedGoodsLot.objects.filter(business=biz), 'fg_id'),
                style=request.POST.get('style', ''),
                production_order_ref=request.POST.get('production_order_ref', ''),
                qty=int(request.POST.get('qty') or 0),
                uom=request.POST.get('uom', 'pairs'),
                unit_cost=request.POST.get('unit_cost') or 0,
                location=request.POST.get('location', ''),
                buyer=request.POST.get('buyer', ''),
                ready_date=request.POST.get('ready_date') or None,
                status=request.POST.get('status', 'ready_to_ship'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'FG lot added.')
        elif action == 'delete':
            get_object_or_404(FinishedGoodsLot, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:finished_goods', slug=slug)

    lots = FinishedGoodsLot.objects.filter(business=biz)
    return render(request, 'factory_ops/finished_goods.html', {
        'biz': biz, 'lots': lots,
        'ready_to_ship': lots.filter(status='ready_to_ship').count(),
        'total_qty': lots.aggregate(total=Sum('qty'))['total'] or 0,
        'total_value': sum(l.total_value for l in lots),
    })


@login_required
def daily_report(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            DailyProductionReport.objects.create(
                business=biz,
                report_date=request.POST.get('report_date') or timezone.now().date(),
                line=request.POST.get('line', ''),
                style=request.POST.get('style', ''),
                manpower=int(request.POST.get('manpower') or 0),
                hour_target=int(request.POST.get('hour_target') or 0),
                day_target=int(request.POST.get('day_target') or 0),
                actual_output=int(request.POST.get('actual_output') or 0),
                defects=int(request.POST.get('defects') or 0),
                downtime_minutes=int(request.POST.get('downtime_minutes') or 0),
                downtime_cause=request.POST.get('downtime_cause', ''),
                smv_per_pair=request.POST.get('smv_per_pair') or 0,
                status=request.POST.get('status', 'green'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Daily report added.')
        elif action == 'delete':
            get_object_or_404(DailyProductionReport, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:daily_report', slug=slug)

    date_filter = request.GET.get('date', '')
    reports = DailyProductionReport.objects.filter(business=biz)
    if date_filter:
        reports = reports.filter(report_date=date_filter)

    efficiencies = [r.line_efficiency_pct for r in reports if r.line_efficiency_pct > 0]
    avg_efficiency = round(sum(efficiencies) / len(efficiencies), 1) if efficiencies else 0

    return render(request, 'factory_ops/daily_report.html', {
        'biz': biz, 'reports': reports,
        'red_lines': reports.filter(status='red').count(),
        'green_lines': reports.filter(status='green').count(),
        'avg_efficiency': avg_efficiency,
        'efficiency_target': 65,
        'date_filter': date_filter,
    })


@login_required
def attendance(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            AttendanceSheet.objects.create(
                business=biz,
                sheet_date=request.POST.get('sheet_date') or timezone.now().date(),
                section=request.POST.get('section', ''),
                present=int(request.POST.get('present') or 0),
                absent=int(request.POST.get('absent') or 0),
                on_leave=int(request.POST.get('on_leave') or 0),
                ot_hours=request.POST.get('ot_hours') or 0,
                piece_rate_pairs=int(request.POST.get('piece_rate_pairs') or 0),
                day_wage_total=request.POST.get('day_wage_total') or 0,
                ot_wage_total=request.POST.get('ot_wage_total') or 0,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Attendance sheet added.')
        elif action == 'delete':
            get_object_or_404(AttendanceSheet, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:attendance', slug=slug)

    sheets = AttendanceSheet.objects.filter(business=biz)
    total_wages = sum(s.total_wages for s in sheets)
    return render(request, 'factory_ops/attendance.html', {
        'biz': biz, 'sheets': sheets,
        'total_present': sheets.aggregate(total=Sum('present'))['total'] or 0,
        'total_wages': total_wages,
        'total_ot_hours': sheets.aggregate(total=Sum('ot_hours'))['total'] or 0,
    })


@login_required
def material_consumption(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            MaterialIssue.objects.create(
                business=biz,
                issue_id=_next_id('ISS', MaterialIssue.objects.filter(business=biz), 'issue_id'),
                issue_date=request.POST.get('issue_date') or timezone.now().date(),
                production_order_ref=request.POST.get('production_order_ref', ''),
                style=request.POST.get('style', ''),
                material_name=request.POST.get('material_name', ''),
                uom=request.POST.get('uom', 'pcs'),
                issued_qty=request.POST.get('issued_qty') or 0,
                standard_qty=request.POST.get('standard_qty') or 0,
                qty_produced=int(request.POST.get('qty_produced') or 0),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Issue recorded.')
        elif action == 'delete':
            get_object_or_404(MaterialIssue, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:material_consumption', slug=slug)

    issues = MaterialIssue.objects.filter(business=biz)
    over_issues = [i for i in issues if i.variance_pct > 5]
    return render(request, 'factory_ops/material_consumption.html', {
        'biz': biz, 'issues': issues,
        'total_issues': issues.count(),
        'over_consumption_count': len(over_issues),
    })


# ─── INDUSTRIAL ENGINEERING ──────────────────────────────────────────────────

@login_required
def time_study(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            TimeStudy.objects.create(
                business=biz,
                study_id=_next_id('TS', TimeStudy.objects.filter(business=biz), 'study_id'),
                operation=request.POST.get('operation', ''),
                style=request.POST.get('style', ''),
                machine=request.POST.get('machine', ''),
                operator=request.POST.get('operator', ''),
                cycles=int(request.POST.get('cycles') or 10),
                observed_avg_seconds=request.POST.get('observed_avg_seconds') or 0,
                performance_rating=int(request.POST.get('performance_rating') or 100),
                allowance_pct=int(request.POST.get('allowance_pct') or 15),
                status=request.POST.get('status', 'draft'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Time study added.')
        elif action == 'delete':
            get_object_or_404(TimeStudy, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:time_study', slug=slug)

    studies = TimeStudy.objects.filter(business=biz)
    return render(request, 'factory_ops/time_study.html', {
        'biz': biz, 'studies': studies,
        'approved': studies.filter(status='approved').count(),
        'in_review': studies.filter(status='review').count(),
    })


@login_required
def smv_study(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            SMVSheet.objects.create(
                business=biz,
                smv_id=_next_id('SMV', SMVSheet.objects.filter(business=biz), 'smv_id'),
                style=request.POST.get('style', ''),
                section=request.POST.get('section', ''),
                total_operations=int(request.POST.get('total_operations') or 0),
                total_smv=request.POST.get('total_smv') or 0,
                target_efficiency_pct=int(request.POST.get('target_efficiency_pct') or 65),
                production_line=request.POST.get('production_line', ''),
                status=request.POST.get('status', 'draft'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'SMV sheet added.')
        elif action == 'delete':
            get_object_or_404(SMVSheet, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:smv', slug=slug)

    sheets = SMVSheet.objects.filter(business=biz)
    return render(request, 'factory_ops/smv.html', {
        'biz': biz, 'sheets': sheets,
        'total_styles': sheets.values('style').distinct().count(),
        'approved': sheets.filter(status='approved').count(),
    })


@login_required
def capacity_study(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            CapacityStudy.objects.create(
                business=biz,
                study_id=_next_id('CAP', CapacityStudy.objects.filter(business=biz), 'study_id'),
                line=request.POST.get('line', ''),
                section=request.POST.get('section', ''),
                style=request.POST.get('style', ''),
                operators=int(request.POST.get('operators') or 0),
                working_hours=request.POST.get('working_hours') or 8,
                line_smv=request.POST.get('line_smv') or 0,
                target_efficiency_pct=int(request.POST.get('target_efficiency_pct') or 65),
                status=request.POST.get('status', 'active'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Capacity study added.')
        elif action == 'delete':
            get_object_or_404(CapacityStudy, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:capacity', slug=slug)

    studies = CapacityStudy.objects.filter(business=biz)
    return render(request, 'factory_ops/capacity.html', {
        'biz': biz, 'studies': studies,
        'active_lines': studies.filter(status='active').count(),
        'total_operators': studies.filter(status='active').aggregate(total=Sum('operators'))['total'] or 0,
    })


@login_required
def style_costing(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            StyleCosting.objects.create(
                business=biz,
                costing_id=_next_id('COST', StyleCosting.objects.filter(business=biz), 'costing_id'),
                style=request.POST.get('style', ''),
                material_cost=request.POST.get('material_cost') or 0,
                labor_minutes=request.POST.get('labor_minutes') or 0,
                labor_rate_per_minute=request.POST.get('labor_rate_per_minute') or 0,
                overhead_pct=int(request.POST.get('overhead_pct') or 35),
                target_margin_pct=int(request.POST.get('target_margin_pct') or 20),
                status=request.POST.get('status', 'draft'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Costing added.')
        elif action == 'delete':
            get_object_or_404(StyleCosting, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:costing', slug=slug)

    costings = StyleCosting.objects.filter(business=biz)
    return render(request, 'factory_ops/costing.html', {
        'biz': biz, 'costings': costings,
        'approved': costings.filter(status='approved').count(),
        'total_styles': costings.count(),
    })


# ─── QUALITY ──────────────────────────────────────────────────────────────────

@login_required
def qc_inspections(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            qc_obj = QCInspection.objects.create(
                business=biz,
                inspection_id=_next_id('QC', QCInspection.objects.filter(business=biz), 'inspection_id'),
                checkpoint=request.POST.get('checkpoint', ''),
                style=request.POST.get('style', ''),
                production_order_ref=request.POST.get('production_order_ref', ''),
                inspector=request.POST.get('inspector', ''),
                inspection_date=request.POST.get('inspection_date') or timezone.now().date(),
                lot_size=int(request.POST.get('lot_size') or 0),
                checked=int(request.POST.get('checked') or 0),
                defects_found=int(request.POST.get('defects_found') or 0),
                stage=request.POST.get('stage', 'final'),
                result=request.POST.get('result', 'pass'),
                lot_number=request.POST.get('lot_number', ''),
                aql_level=request.POST.get('aql_level', '2.5'),
                defect_severity=request.POST.get('defect_severity', ''),
                is_first_inspection=request.POST.get('is_first_inspection') != 'no',
                notes=request.POST.get('notes', ''),
            )
            if request.FILES.get('report_file'):
                qc_obj.report_file = request.FILES['report_file']
                qc_obj.save(update_fields=['report_file'])
            messages.success(request, 'Inspection recorded.')
        elif action == 'delete':
            get_object_or_404(QCInspection, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:qc', slug=slug)

    inspections = QCInspection.objects.filter(business=biz)
    total = inspections.count()
    first_pass = inspections.filter(is_first_inspection=True, result='pass').count()
    total_first = inspections.filter(is_first_inspection=True).count()
    ftr_rate = round(first_pass / total_first * 100, 1) if total_first else 0
    return render(request, 'factory_ops/qc.html', {
        'biz': biz, 'inspections': inspections,
        'total': total,
        'failed': inspections.filter(result='fail').count(),
        'passed': inspections.filter(result='pass').count(),
        'ftr_rate': ftr_rate,
        'ftr_target': 92,
        'aql_choices': QCInspection.AQL,
        'severity_choices': QCInspection.SEVERITY,
    })


@login_required
def rework_defects(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            ReworkRecord.objects.create(
                business=biz,
                rework_id=_next_id('RW', ReworkRecord.objects.filter(business=biz), 'rework_id'),
                rework_date=request.POST.get('rework_date') or timezone.now().date(),
                production_order_ref=request.POST.get('production_order_ref', ''),
                style=request.POST.get('style', ''),
                stage=request.POST.get('stage', ''),
                defect_type=request.POST.get('defect_type', ''),
                qty_affected=int(request.POST.get('qty_affected') or 0),
                qty_recovered=int(request.POST.get('qty_recovered') or 0),
                qty_rejected=int(request.POST.get('qty_rejected') or 0),
                labor_cost=request.POST.get('labor_cost') or 0,
                root_cause=request.POST.get('root_cause', ''),
                status=request.POST.get('status', 'open'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Rework record added.')
        elif action == 'close':
            rw = get_object_or_404(ReworkRecord, pk=request.POST.get('pk'), business=biz)
            rw.status = 'closed'
            rw.save()
        elif action == 'delete':
            get_object_or_404(ReworkRecord, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:rework', slug=slug)

    records = ReworkRecord.objects.filter(business=biz)
    return render(request, 'factory_ops/rework.html', {
        'biz': biz, 'records': records,
        'open_count': records.filter(status__in=['open', 'in_progress']).count(),
        'total_affected': records.aggregate(total=Sum('qty_affected'))['total'] or 0,
        'total_rejected': records.aggregate(total=Sum('qty_rejected'))['total'] or 0,
        'total_cost': records.aggregate(total=Sum('labor_cost'))['total'] or 0,
    })


@login_required
def factory_sops(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            sop = FactorySOP.objects.create(
                business=biz,
                sop_id=_next_id('SOP', FactorySOP.objects.filter(business=biz), 'sop_id'),
                title=request.POST.get('title', ''),
                department=request.POST.get('department', ''),
                owner=request.POST.get('owner', ''),
                version=request.POST.get('version', '1.0'),
                updated_date=request.POST.get('updated_date') or None,
                status=request.POST.get('status', 'active'),
                description=request.POST.get('description', ''),
            )
            if request.FILES.get('document'):
                sop.document = request.FILES['document']
                sop.save(update_fields=['document'])
            messages.success(request, 'SOP added.')
        elif action == 'delete':
            get_object_or_404(FactorySOP, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:sops', slug=slug)

    sops = FactorySOP.objects.filter(business=biz)
    return render(request, 'factory_ops/sops.html', {
        'biz': biz, 'sops': sops,
        'active': sops.filter(status='active').count(),
        'in_review': sops.filter(status='review').count(),
        'departments': sops.values_list('department', flat=True).distinct(),
    })


# ─── COMMERCIAL ───────────────────────────────────────────────────────────────

@login_required
def buyers(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            Buyer.objects.create(
                business=biz,
                buyer_id=_next_id('BY', Buyer.objects.filter(business=biz), 'buyer_id'),
                name=request.POST.get('name', ''),
                country=request.POST.get('country', ''),
                contact=request.POST.get('contact', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                payment_terms=request.POST.get('payment_terms', ''),
                rating=request.POST.get('rating', 'B'),
                status=request.POST.get('status', 'prospect'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Buyer added.')
        elif action == 'delete':
            get_object_or_404(Buyer, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:buyers', slug=slug)

    buyer_qs = Buyer.objects.filter(business=biz)
    return render(request, 'factory_ops/buyers.html', {
        'biz': biz, 'buyers': buyer_qs,
        'active_count': buyer_qs.filter(status='active').count(),
        'total_ytd': buyer_qs.aggregate(total=Sum('ytd_volume'))['total'] or 0,
    })


@login_required
def sales_pipeline(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            SalesDeal.objects.create(
                business=biz,
                deal_id=_next_id('SL', SalesDeal.objects.filter(business=biz), 'deal_id'),
                deal_name=request.POST.get('deal_name', ''),
                buyer_name=request.POST.get('buyer_name', ''),
                value=request.POST.get('value') or 0,
                stage=request.POST.get('stage', 'lead'),
                probability=int(request.POST.get('probability') or 50),
                target_close=request.POST.get('target_close') or None,
                next_action=request.POST.get('next_action', ''),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Deal added.')
        elif action == 'update_stage':
            deal = get_object_or_404(SalesDeal, pk=request.POST.get('pk'), business=biz)
            deal.stage = request.POST.get('stage', deal.stage)
            deal.probability = int(request.POST.get('probability') or deal.probability)
            deal.save()
        elif action == 'delete':
            get_object_or_404(SalesDeal, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:sales', slug=slug)

    deals = SalesDeal.objects.filter(business=biz)
    open_deals = deals.exclude(stage__in=['won', 'lost'])
    return render(request, 'factory_ops/sales.html', {
        'biz': biz, 'deals': deals,
        'open_count': open_deals.count(),
        'pipeline_value': open_deals.aggregate(total=Sum('value'))['total'] or 0,
        'won_value': deals.filter(stage='won').aggregate(total=Sum('value'))['total'] or 0,
        'stages': SalesDeal.STAGE,
    })


@login_required
def customer_orders(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            CustomerOrder.objects.create(
                business=biz,
                order_id=_next_id('ORD', CustomerOrder.objects.filter(business=biz), 'order_id'),
                buyer_name=request.POST.get('buyer_name', ''),
                style=request.POST.get('style', ''),
                qty=int(request.POST.get('qty') or 0),
                unit_price=request.POST.get('unit_price') or 0,
                channel=request.POST.get('channel', 'Export'),
                order_date=request.POST.get('order_date') or None,
                delivery_date=request.POST.get('delivery_date') or None,
                status=request.POST.get('status', 'confirmed'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Order added.')
        elif action == 'delete':
            get_object_or_404(CustomerOrder, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:orders', slug=slug)

    orders = CustomerOrder.objects.filter(business=biz)
    open_orders = orders.exclude(status__in=['delivered', 'cancelled'])
    return render(request, 'factory_ops/orders.html', {
        'biz': biz, 'orders': orders,
        'open_count': open_orders.count(),
        'total_qty': open_orders.aggregate(total=Sum('qty'))['total'] or 0,
        'total_value': sum(o.order_value for o in open_orders),
    })


@login_required
def invoices(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            inv_obj = FactoryInvoice.objects.create(
                business=biz,
                invoice_id=_next_id('INV', FactoryInvoice.objects.filter(business=biz), 'invoice_id'),
                order_ref=request.POST.get('order_ref', ''),
                buyer_name=request.POST.get('buyer_name', ''),
                amount=request.POST.get('amount') or 0,
                issue_date=request.POST.get('issue_date') or None,
                due_date=request.POST.get('due_date') or None,
                status=request.POST.get('status', 'unpaid'),
                notes=request.POST.get('notes', ''),
            )
            if request.FILES.get('document'):
                inv_obj.document = request.FILES['document']
                inv_obj.save(update_fields=['document'])
            messages.success(request, 'Invoice created.')
        elif action == 'mark_paid':
            inv = get_object_or_404(FactoryInvoice, pk=request.POST.get('pk'), business=biz)
            inv.status = 'paid'
            inv.save()
            messages.success(request, 'Marked as paid.')
        elif action == 'delete':
            get_object_or_404(FactoryInvoice, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:invoices', slug=slug)

    inv_qs = FactoryInvoice.objects.filter(business=biz)
    unpaid = inv_qs.filter(status='unpaid')
    return render(request, 'factory_ops/invoices.html', {
        'biz': biz, 'invoices': inv_qs,
        'unpaid_count': unpaid.count(),
        'unpaid_total': unpaid.aggregate(total=Sum('amount'))['total'] or 0,
        'overdue_count': sum(1 for i in inv_qs if i.is_overdue),
    })


@login_required
def vendors(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_vendor':
            Vendor.objects.create(
                business=biz,
                vendor_id=_next_id('VND', Vendor.objects.filter(business=biz), 'vendor_id'),
                name=request.POST.get('name', ''),
                category=request.POST.get('category', 'Other'),
                contact=request.POST.get('contact', ''),
                email=request.POST.get('email', ''),
                phone=request.POST.get('phone', ''),
                payment_terms=request.POST.get('payment_terms', ''),
                status=request.POST.get('vendor_status', 'active'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Vendor added.')
        elif action == 'create_po':
            VendorPO.objects.create(
                business=biz,
                po_id=_next_id('PO-V', VendorPO.objects.filter(business=biz), 'po_id'),
                vendor_name=request.POST.get('vendor_name', ''),
                items_description=request.POST.get('items_description', ''),
                value=request.POST.get('value') or 0,
                order_date=request.POST.get('order_date') or None,
                expected_date=request.POST.get('expected_date') or None,
                received_pct=int(request.POST.get('received_pct') or 0),
                status=request.POST.get('po_status', 'open'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'PO added.')
        elif action == 'delete_po':
            get_object_or_404(VendorPO, pk=request.POST.get('pk'), business=biz).delete()
        elif action == 'delete_vendor':
            get_object_or_404(Vendor, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:vendors', slug=slug)

    vendor_qs = Vendor.objects.filter(business=biz)
    po_qs = VendorPO.objects.filter(business=biz)
    return render(request, 'factory_ops/vendors.html', {
        'biz': biz, 'vendors': vendor_qs, 'pos': po_qs,
        'active_vendors': vendor_qs.filter(status='active').count(),
        'open_pos': po_qs.exclude(status='received').count(),
        'open_po_value': po_qs.exclude(status='received').aggregate(total=Sum('value'))['total'] or 0,
    })


@login_required
def supplier_scorecard(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            SupplierScore.objects.create(
                business=biz,
                vendor_name=request.POST.get('vendor_name', ''),
                category=request.POST.get('category', 'Other'),
                orders_ytd=int(request.POST.get('orders_ytd') or 0),
                on_time_pct=int(request.POST.get('on_time_pct') or 0),
                quality_pct=int(request.POST.get('quality_pct') or 0),
                defect_rate=request.POST.get('defect_rate') or 0,
                price_rating=request.POST.get('price_rating', 'competitive'),
                status=request.POST.get('status', 'approved'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Scorecard added.')
        elif action == 'delete':
            get_object_or_404(SupplierScore, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:supplier_scorecard', slug=slug)

    scores = SupplierScore.objects.filter(business=biz)
    return render(request, 'factory_ops/supplier_scorecard.html', {
        'biz': biz, 'scores': scores,
        'preferred': scores.filter(status='preferred').count(),
        'watch': scores.filter(status='watch').count(),
        'total': scores.count(),
    })


# ─── DISTRIBUTION & SALES FORCE ───────────────────────────────────────────────

@login_required
def distribution(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            DistributionChannel.objects.create(
                business=biz,
                channel_id=_next_id('DC', DistributionChannel.objects.filter(business=biz), 'channel_id'),
                name=request.POST.get('name', ''),
                channel_type=request.POST.get('channel_type', 'Distributor'),
                region=request.POST.get('region', ''),
                contact=request.POST.get('contact', ''),
                coverage=request.POST.get('coverage', ''),
                credit_limit=request.POST.get('credit_limit') or 0,
                ytd_sales=request.POST.get('ytd_sales') or 0,
                status=request.POST.get('status', 'active'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Channel added.')
        elif action == 'delete':
            get_object_or_404(DistributionChannel, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:distribution', slug=slug)

    channels = DistributionChannel.objects.filter(business=biz)
    return render(request, 'factory_ops/distribution.html', {
        'biz': biz, 'channels': channels,
        'active_count': channels.filter(status='active').count(),
        'total_ytd': channels.aggregate(total=Sum('ytd_sales'))['total'] or 0,
    })


@login_required
def wholesale(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            WholesaleAccount.objects.create(
                business=biz,
                account_id=_next_id('WS', WholesaleAccount.objects.filter(business=biz), 'account_id'),
                name=request.POST.get('name', ''),
                location=request.POST.get('location', ''),
                buyer_type=request.POST.get('buyer_type', ''),
                payment_terms=request.POST.get('payment_terms', ''),
                credit_limit=request.POST.get('credit_limit') or 0,
                outstanding=request.POST.get('outstanding') or 0,
                ytd_volume=request.POST.get('ytd_volume') or 0,
                status=request.POST.get('status', 'active'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Account added.')
        elif action == 'delete':
            get_object_or_404(WholesaleAccount, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:wholesale', slug=slug)

    accounts = WholesaleAccount.objects.filter(business=biz)
    return render(request, 'factory_ops/wholesale.html', {
        'biz': biz, 'accounts': accounts,
        'active_count': accounts.filter(status='active').count(),
        'total_volume': accounts.aggregate(total=Sum('ytd_volume'))['total'] or 0,
        'total_outstanding': accounts.aggregate(total=Sum('outstanding'))['total'] or 0,
    })


@login_required
def sales_team(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            SalesRep.objects.create(
                business=biz,
                rep_id=_next_id('SR', SalesRep.objects.filter(business=biz), 'rep_id'),
                name=request.POST.get('name', ''),
                role=request.POST.get('role', ''),
                territory=request.POST.get('territory', ''),
                joined_date=request.POST.get('joined_date') or None,
                monthly_target=request.POST.get('monthly_target') or 0,
                mtd_achieved=request.POST.get('mtd_achieved') or 0,
                accounts_count=int(request.POST.get('accounts_count') or 0),
                status=request.POST.get('status', 'active'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Rep added.')
        elif action == 'delete':
            get_object_or_404(SalesRep, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:sales_team', slug=slug)

    reps = SalesRep.objects.filter(business=biz)
    return render(request, 'factory_ops/sales_team.html', {
        'biz': biz, 'reps': reps,
        'active_count': reps.filter(status__in=['active', 'probation']).count(),
        'total_target': reps.aggregate(total=Sum('monthly_target'))['total'] or 0,
        'total_achieved': reps.aggregate(total=Sum('mtd_achieved'))['total'] or 0,
    })


@login_required
def sales_targets(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            SalesTarget.objects.create(
                business=biz,
                target_id=_next_id('TGT', SalesTarget.objects.filter(business=biz), 'target_id'),
                period=request.POST.get('period', ''),
                scope=request.POST.get('scope', ''),
                owner_name=request.POST.get('owner_name', ''),
                target_value=request.POST.get('target_value') or 0,
                achieved_value=request.POST.get('achieved_value') or 0,
                channel=request.POST.get('channel', ''),
                status=request.POST.get('status', 'on_track'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Target added.')
        elif action == 'delete':
            get_object_or_404(SalesTarget, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:targets', slug=slug)

    targets = SalesTarget.objects.filter(business=biz)
    return render(request, 'factory_ops/targets.html', {
        'biz': biz, 'targets': targets,
        'on_track': targets.filter(status='on_track').count(),
        'at_risk': targets.filter(status='at_risk').count(),
        'total_target': targets.aggregate(total=Sum('target_value'))['total'] or 0,
        'total_achieved': targets.aggregate(total=Sum('achieved_value'))['total'] or 0,
    })


@login_required
def tasks(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            FactoryTask.objects.create(
                business=biz,
                task_id=_next_id('TSK', FactoryTask.objects.filter(business=biz), 'task_id'),
                title=request.POST.get('title', ''),
                assignee=request.POST.get('assignee', ''),
                priority=request.POST.get('priority', 'med'),
                due_date=request.POST.get('due_date') or None,
                category=request.POST.get('category', ''),
                status=request.POST.get('status', 'todo'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Task added.')
        elif action == 'complete':
            t = get_object_or_404(FactoryTask, pk=request.POST.get('pk'), business=biz)
            t.status = 'done'
            t.save()
        elif action == 'delete':
            get_object_or_404(FactoryTask, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:tasks', slug=slug)

    task_qs = FactoryTask.objects.filter(business=biz)
    status_filter = request.GET.get('status', '')
    if status_filter:
        task_qs = task_qs.filter(status=status_filter)
    return render(request, 'factory_ops/tasks.html', {
        'biz': biz, 'task_list': task_qs,
        'open_count': FactoryTask.objects.filter(business=biz).exclude(status__in=['done', 'cancelled']).count(),
        'overdue_count': sum(1 for t in FactoryTask.objects.filter(business=biz) if t.is_overdue),
        'status_filter': status_filter,
    })


@login_required
def marketing(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            MarketingCampaign.objects.create(
                business=biz,
                campaign_id=_next_id('MKT', MarketingCampaign.objects.filter(business=biz), 'campaign_id'),
                name=request.POST.get('name', ''),
                channel=request.POST.get('channel', 'Digital'),
                budget=request.POST.get('budget') or 0,
                spent=request.POST.get('spent') or 0,
                start_date=request.POST.get('start_date') or None,
                end_date=request.POST.get('end_date') or None,
                status=request.POST.get('status', 'planned'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Campaign added.')
        elif action == 'delete':
            get_object_or_404(MarketingCampaign, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:marketing', slug=slug)

    campaigns = MarketingCampaign.objects.filter(business=biz)
    return render(request, 'factory_ops/marketing.html', {
        'biz': biz, 'campaigns': campaigns,
        'active_count': campaigns.filter(status='active').count(),
        'total_budget': campaigns.aggregate(total=Sum('budget'))['total'] or 0,
        'total_spent': campaigns.aggregate(total=Sum('spent'))['total'] or 0,
    })


# ─── FINANCE & ADMIN ──────────────────────────────────────────────────────────

@login_required
def ar_ap_ledger(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            ARAPEntry.objects.create(
                business=biz,
                entry_id=_next_id('AR', ARAPEntry.objects.filter(business=biz), 'entry_id'),
                entry_type=request.POST.get('entry_type', 'receivable'),
                party=request.POST.get('party', ''),
                invoice_ref=request.POST.get('invoice_ref', ''),
                amount=request.POST.get('amount') or 0,
                due_date=request.POST.get('due_date') or None,
                status=request.POST.get('status', 'open'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Entry added.')
        elif action == 'mark_paid':
            e = get_object_or_404(ARAPEntry, pk=request.POST.get('pk'), business=biz)
            e.status = 'paid'
            e.save()
        elif action == 'delete':
            get_object_or_404(ARAPEntry, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:ar_ap', slug=slug)

    entries = ARAPEntry.objects.filter(business=biz)
    ar = entries.filter(entry_type='receivable').exclude(status='paid')
    ap = entries.filter(entry_type='payable').exclude(status='paid')
    return render(request, 'factory_ops/ar_ap.html', {
        'biz': biz, 'entries': entries,
        'total_ar': ar.aggregate(total=Sum('amount'))['total'] or 0,
        'total_ap': ap.aggregate(total=Sum('amount'))['total'] or 0,
        'overdue_ar': ar.filter(status='overdue').aggregate(total=Sum('amount'))['total'] or 0,
        'type_filter': request.GET.get('type', ''),
    })


@login_required
def banking(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_account':
            BankAccount.objects.create(
                business=biz,
                account_id=_next_id('BA', BankAccount.objects.filter(business=biz), 'account_id'),
                name=request.POST.get('name', ''),
                bank=request.POST.get('bank', ''),
                account_number=request.POST.get('account_number', ''),
                currency=request.POST.get('currency', 'BDT'),
                balance=request.POST.get('balance') or 0,
                last_txn_date=request.POST.get('last_txn_date') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Account added.')
        elif action == 'create_lc':
            LetterOfCredit.objects.create(
                business=biz,
                lc_id=_next_id('LC', LetterOfCredit.objects.filter(business=biz), 'lc_id'),
                description=request.POST.get('description', ''),
                bank=request.POST.get('lc_bank', ''),
                beneficiary=request.POST.get('beneficiary', ''),
                value=request.POST.get('lc_value') or 0,
                currency=request.POST.get('lc_currency', 'BDT'),
                expiry_date=request.POST.get('expiry_date') or None,
                status=request.POST.get('lc_status', 'active'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'LC added.')
        elif action == 'delete_account':
            get_object_or_404(BankAccount, pk=request.POST.get('pk'), business=biz).delete()
        elif action == 'delete_lc':
            get_object_or_404(LetterOfCredit, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:banking', slug=slug)

    accounts = BankAccount.objects.filter(business=biz, is_active=True)
    lcs = LetterOfCredit.objects.filter(business=biz)
    cash_total = accounts.aggregate(total=Sum('balance'))['total'] or 0
    return render(request, 'factory_ops/banking.html', {
        'biz': biz, 'accounts': accounts, 'lcs': lcs,
        'cash_position': cash_total,
        'active_lcs': lcs.filter(status='active').count(),
        'total_lc_value': lcs.filter(status='active').aggregate(total=Sum('value'))['total'] or 0,
    })


@login_required
def hr_roster(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            FactoryEmployee.objects.create(
                business=biz,
                emp_id=_next_id('EMP', FactoryEmployee.objects.filter(business=biz), 'emp_id'),
                name=request.POST.get('name', ''),
                designation=request.POST.get('designation', ''),
                department=request.POST.get('department', 'Production'),
                joined_date=request.POST.get('joined_date') or None,
                salary=request.POST.get('salary') or 0,
                monthly_attendance=request.POST.get('monthly_attendance', ''),
                status=request.POST.get('status', 'active'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Employee added.')
        elif action == 'delete':
            get_object_or_404(FactoryEmployee, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:hr', slug=slug)

    dept_filter = request.GET.get('dept', '')
    employees = FactoryEmployee.objects.filter(business=biz)
    if dept_filter:
        employees = employees.filter(department=dept_filter)
    active = employees.filter(status__in=['active', 'probation'])
    return render(request, 'factory_ops/hr.html', {
        'biz': biz, 'employees': employees,
        'headcount': active.count(),
        'payroll_total': active.aggregate(total=Sum('salary'))['total'] or 0,
        'probation_count': employees.filter(status='probation').count(),
        'dept_filter': dept_filter,
        'departments': [d[0] for d in FactoryEmployee._meta.get_field('department').choices],
    })


@login_required
def approvals(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            ApprovalRequest.objects.create(
                business=biz,
                request_id=_next_id('APR', ApprovalRequest.objects.filter(business=biz), 'request_id'),
                request_date=request.POST.get('request_date') or timezone.now().date(),
                request_type=request.POST.get('request_type', 'other'),
                requested_by=request.POST.get('requested_by', ''),
                amount=request.POST.get('amount') or 0,
                party=request.POST.get('party', ''),
                status='pending',
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Request submitted.')
        elif action in ('approve', 'reject'):
            req = get_object_or_404(ApprovalRequest, pk=request.POST.get('pk'), business=biz)
            req.status = 'approved' if action == 'approve' else 'rejected'
            req.review_notes = request.POST.get('review_notes', '')
            req.save()
            messages.success(request, f"Request {req.status}.")
        elif action == 'delete':
            get_object_or_404(ApprovalRequest, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:approvals', slug=slug)

    status_filter = request.GET.get('status', '')
    reqs = ApprovalRequest.objects.filter(business=biz)
    if status_filter:
        reqs = reqs.filter(status=status_filter)
    all_reqs = ApprovalRequest.objects.filter(business=biz)
    return render(request, 'factory_ops/approvals.html', {
        'biz': biz, 'requests': reqs,
        'pending_count': all_reqs.filter(status='pending').count(),
        'total_pending_amount': all_reqs.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0,
        'status_filter': status_filter,
        # Spending threshold tiers (Blueprint)
        'threshold_petty': 5000,
        'threshold_manager': 25000,
    })


@login_required
def product_inventory(request, slug):
    biz = _biz(request, slug)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            ProductSKU.objects.create(
                business=biz,
                sku_id=_next_id('SKU', ProductSKU.objects.filter(business=biz), 'sku_id'),
                name=request.POST.get('name', ''),
                category=request.POST.get('category', 'Other'),
                uom=request.POST.get('uom', 'pairs'),
                on_hand=request.POST.get('on_hand') or 0,
                reorder_point=request.POST.get('reorder_point') or 0,
                unit_cost=request.POST.get('unit_cost') or 0,
                supplier=request.POST.get('supplier', ''),
                last_in_date=request.POST.get('last_in_date') or None,
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'SKU added.')
        elif action == 'adjust':
            sku = get_object_or_404(ProductSKU, pk=request.POST.get('pk'), business=biz)
            sku.on_hand = request.POST.get('on_hand') or sku.on_hand
            sku.save()
            messages.success(request, 'Stock updated.')
        elif action == 'delete':
            get_object_or_404(ProductSKU, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:inventory', slug=slug)

    cat_filter = request.GET.get('cat', '')
    skus = ProductSKU.objects.filter(business=biz)
    if cat_filter and cat_filter != 'low':
        skus = skus.filter(category=cat_filter)
    elif cat_filter == 'low':
        skus = [s for s in skus if s.is_low_stock]

    all_skus = ProductSKU.objects.filter(business=biz)
    return render(request, 'factory_ops/inventory.html', {
        'biz': biz,
        'skus': skus,
        'cat_filter': cat_filter,
        'total_skus': all_skus.count(),
        'low_stock_count': sum(1 for s in all_skus if s.is_low_stock),
        'total_value': sum(s.stock_value for s in all_skus),
        'categories': [c[0] for c in ProductSKU._meta.get_field('category').choices],
    })


@login_required
def financials_report(request, slug):
    biz = _biz(request, slug)
    cfg = _get_settings(biz)
    today = timezone.now().date()

    # Period filter (default: current month)
    try:
        period_month = int(request.GET.get('month', today.month))
        period_year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        period_month, period_year = today.month, today.year
    period_month = max(1, min(12, period_month))

    # ── Revenue (period-filtered) ──
    delivered_orders = CustomerOrder.objects.filter(
        business=biz, status__in=['delivered', 'partial_delivered', 'ready'],
        delivery_date__month=period_month, delivery_date__year=period_year)
    order_revenue = sum(o.order_value for o in delivered_orders)
    invoice_revenue = FactoryInvoice.objects.filter(
        business=biz, issue_date__month=period_month, issue_date__year=period_year,
    ).aggregate(total=Sum('amount'))['total'] or 0
    revenue = float(max(order_revenue, invoice_revenue))

    # ── COGS ──
    shipped_fg = FinishedGoodsLot.objects.filter(
        business=biz, status__in=['shipped', 'partial_shipped'])
    fg_cost = sum(float(f.qty) * float(f.unit_cost) for f in shipped_fg if hasattr(f, 'unit_cost'))
    estimated_cogs = fg_cost if fg_cost > 0 else round(revenue * float(cfg.cogs_estimate_pct) / 100)
    gross_profit = revenue - estimated_cogs
    gross_margin = (gross_profit / revenue * 100) if revenue else 0

    # ── Operating Expenses ──
    active_employees = FactoryEmployee.objects.filter(
        business=biz, status__in=['active', 'probation'])
    monthly_payroll = float(
        active_employees.aggregate(total=Sum('salary'))['total'] or 0)
    marketing_spend = float(
        MarketingCampaign.objects.filter(business=biz).aggregate(total=Sum('spent'))['total'] or 0)
    operating_profit = gross_profit - monthly_payroll - marketing_spend

    # ── Interest & Tax (from FactorySettings) ──
    FIXED_ASSETS = float(cfg.fixed_assets)
    LONG_TERM_DEBT = float(cfg.long_term_debt)
    interest_expense = round(LONG_TERM_DEBT * cfg.interest_rate / 12)
    profit_before_tax = operating_profit - interest_expense
    tax = max(0, round(profit_before_tax * cfg.tax_rate))
    net_profit = profit_before_tax - tax
    net_margin = (net_profit / revenue * 100) if revenue else 0

    # ── Balance Sheet ──
    cash = float(BankAccount.objects.filter(business=biz, is_active=True).aggregate(
        total=Sum('balance'))['total'] or 0)
    receivables = float(ARAPEntry.objects.filter(
        business=biz, entry_type='receivable').exclude(status='paid').aggregate(
        total=Sum('amount'))['total'] or 0)
    payables = float(ARAPEntry.objects.filter(
        business=biz, entry_type='payable').exclude(status='paid').aggregate(
        total=Sum('amount'))['total'] or 0)
    rm_value = sum(r.stock_value for r in RawMaterial.objects.filter(business=biz))
    wip_value = float(WIPLot.objects.filter(business=biz).aggregate(
        total=Sum('wip_value'))['total'] or 0)
    fg_value = float(FinishedGoodsLot.objects.filter(business=biz).aggregate(
        total=Sum('total_cost'))['total'] or 0) if hasattr(FinishedGoodsLot, 'total_cost') else 0
    inventory_total = rm_value + wip_value + fg_value
    current_assets = cash + receivables + inventory_total
    total_assets = current_assets + FIXED_ASSETS
    od_liability = 0
    current_liabilities = payables + od_liability
    total_liabilities = current_liabilities + LONG_TERM_DEBT
    equity = total_assets - total_liabilities
    current_ratio = round(current_assets / current_liabilities, 2) if current_liabilities else 0

    # ── Cash Flow ──
    cf_receivables = -round(receivables * 0.15)
    cf_inventory = -round(inventory_total * 0.10)
    cf_payables = round(payables * 0.12)
    net_operating_cf = net_profit + cf_receivables + cf_inventory + cf_payables
    cf_investing = -1_200_000
    cf_financing = -interest_expense - 500_000
    net_cash_flow = net_operating_cf + cf_investing + cf_financing

    import calendar
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(today.year - 2, today.year + 2))

    return render(request, 'factory_ops/financials.html', {
        'biz': biz, 'cfg': cfg,
        'period_month': period_month, 'period_year': period_year,
        'months': months, 'years': years,
        # KPIs
        'revenue': revenue, 'net_profit': net_profit,
        'net_margin': round(net_margin, 1),
        'total_assets': total_assets, 'equity': equity,
        'current_ratio': current_ratio,
        # Income Statement
        'estimated_cogs': estimated_cogs,
        'gross_profit': gross_profit, 'gross_margin': round(gross_margin, 1),
        'monthly_payroll': monthly_payroll, 'marketing_spend': marketing_spend,
        'operating_profit': operating_profit,
        'interest_expense': interest_expense,
        'profit_before_tax': profit_before_tax,
        'tax': tax,
        # Balance Sheet
        'cash': cash, 'receivables': receivables,
        'rm_value': rm_value, 'wip_value': wip_value, 'fg_value': fg_value,
        'inventory_total': inventory_total,
        'current_assets': current_assets,
        'fixed_assets': FIXED_ASSETS,
        'payables': payables, 'od_liability': od_liability,
        'current_liabilities': current_liabilities,
        'long_term_debt': LONG_TERM_DEBT,
        'total_liabilities': total_liabilities,
        # Cash Flow
        'net_operating_cf': net_operating_cf,
        'cf_receivables': cf_receivables, 'cf_inventory': cf_inventory,
        'cf_payables': cf_payables, 'cf_investing': cf_investing,
        'cf_financing': cf_financing, 'net_cash_flow': net_cash_flow,
    })


@login_required
def mis_report(request, slug):
    biz = _biz(request, slug)
    today = timezone.now().date()

    # Period filter (default: current month)
    try:
        period_month = int(request.GET.get('month', today.month))
        period_year = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        period_month, period_year = today.month, today.year
    period_month = max(1, min(12, period_month))

    production_qs = ProductionOrder.objects.filter(business=biz)
    active_orders = production_qs.exclude(current_stage='shipped')
    qc_qs = QCInspection.objects.filter(
        business=biz, inspection_date__month=period_month, inspection_date__year=period_year)
    rework_qs = ReworkRecord.objects.filter(business=biz)
    sales_qs = SalesDeal.objects.filter(business=biz)
    orders_qs = CustomerOrder.objects.filter(business=biz)
    ar_qs = ARAPEntry.objects.filter(business=biz, entry_type='receivable').exclude(status='paid')
    ap_qs = ARAPEntry.objects.filter(business=biz, entry_type='payable').exclude(status='paid')

    # FTR Rate — first-time-right
    total_first = qc_qs.filter(is_first_inspection=True).count()
    first_pass = qc_qs.filter(is_first_inspection=True, result='pass').count()
    ftr_rate = round(first_pass / total_first * 100, 1) if total_first else 0

    # Average line efficiency from daily reports
    daily_qs = DailyProductionReport.objects.filter(business=biz)
    efficiencies = [r.line_efficiency_pct for r in daily_qs if r.line_efficiency_pct > 0]
    avg_line_efficiency = round(sum(efficiencies) / len(efficiencies), 1) if efficiencies else 0

    # Schedule adherence — orders delivered on/before delivery_date
    delivered = orders_qs.filter(status__in=['delivered', 'partial_delivered'])
    on_time = sum(1 for o in delivered if o.delivery_date and o.delivery_date >= (o.order_date or o.delivery_date))
    schedule_adherence = round(on_time / delivered.count() * 100, 1) if delivered.count() else 0

    # Collection efficiency — paid AR vs total invoiced AR
    all_ar = ARAPEntry.objects.filter(business=biz, entry_type='receivable')
    paid_ar = float(all_ar.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0)
    total_invoiced = float(all_ar.aggregate(total=Sum('amount'))['total'] or 0)
    collection_efficiency = round(paid_ar / total_invoiced * 100, 1) if total_invoiced else 0

    import calendar
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]
    years = list(range(today.year - 2, today.year + 2))

    return render(request, 'factory_ops/mis.html', {
        'biz': biz,
        'today': today,
        'period_month': period_month, 'period_year': period_year,
        'months': months, 'years': years,
        # Production KPIs
        'active_orders': active_orders.count(),
        'overdue_orders': sum(1 for o in active_orders if o.is_overdue),
        'total_pairs_wip': active_orders.aggregate(total=Sum('qty'))['total'] or 0,
        'total_packed': production_qs.filter(current_stage='packed').count(),
        # IE KPIs
        'approved_smv': SMVSheet.objects.filter(business=biz, status='approved').count(),
        'active_lines': CapacityStudy.objects.filter(business=biz, status='active').count(),
        'approved_costings': StyleCosting.objects.filter(business=biz, status='approved').count(),
        'avg_line_efficiency': avg_line_efficiency,
        'efficiency_target': 65,
        # Quality KPIs
        'qc_total': qc_qs.count(),
        'qc_fail_rate': round(qc_qs.filter(result='fail').count() / max(qc_qs.count(), 1) * 100, 1),
        'open_rework': rework_qs.filter(status__in=['open', 'in_progress']).count(),
        'total_rejected': rework_qs.aggregate(total=Sum('qty_rejected'))['total'] or 0,
        'ftr_rate': ftr_rate,
        'ftr_target': 92,
        # Sales KPIs
        'pipeline_value': sales_qs.exclude(stage__in=['won', 'lost']).aggregate(total=Sum('value'))['total'] or 0,
        'won_ytd': sales_qs.filter(stage='won').aggregate(total=Sum('value'))['total'] or 0,
        'open_orders': orders_qs.exclude(status__in=['delivered', 'cancelled']).count(),
        'schedule_adherence': schedule_adherence,
        # Finance KPIs
        'total_ar': ar_qs.aggregate(total=Sum('amount'))['total'] or 0,
        'overdue_ar': ar_qs.filter(status='overdue').aggregate(total=Sum('amount'))['total'] or 0,
        'total_ap': ap_qs.aggregate(total=Sum('amount'))['total'] or 0,
        'cash_position': BankAccount.objects.filter(business=biz, is_active=True).aggregate(total=Sum('balance'))['total'] or 0,
        'collection_efficiency': collection_efficiency,
        # HR
        'headcount': FactoryEmployee.objects.filter(business=biz, status__in=['active', 'probation']).count(),
        'payroll_total': FactoryEmployee.objects.filter(business=biz, status__in=['active', 'probation']).aggregate(total=Sum('salary'))['total'] or 0,
        # Inventory
        'low_stock_count': sum(1 for r in RawMaterial.objects.filter(business=biz) if r.is_low_stock),
        'fg_ready': FinishedGoodsLot.objects.filter(business=biz, status='ready_to_ship').count(),
        # Pending approvals
        'pending_approvals': ApprovalRequest.objects.filter(business=biz, status='pending').count(),
    })


# ─── FLOOR MANAGEMENT ─────────────────────────────────────────────────────────

@login_required
def hourly_production_board(request, slug):
    biz = _biz(request, slug)
    today = timezone.now().date()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'upsert':
            obj, _ = HourlyProductionEntry.objects.update_or_create(
                business=biz,
                entry_date=request.POST.get('entry_date') or today,
                line=request.POST.get('line', ''),
                hour_slot=request.POST.get('hour_slot', ''),
                defaults=dict(
                    target=int(request.POST.get('target') or 0),
                    actual=int(request.POST.get('actual') or 0),
                    root_cause=request.POST.get('root_cause', ''),
                    corrective_action=request.POST.get('corrective_action', ''),
                    action_owner=request.POST.get('action_owner', ''),
                ),
            )
            messages.success(request, 'Entry saved.')
        elif action == 'delete':
            get_object_or_404(HourlyProductionEntry, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:hourly_board', slug=slug)

    date_filter = request.GET.get('date', str(today))
    line_filter = request.GET.get('line', '')
    entries = HourlyProductionEntry.objects.filter(business=biz, entry_date=date_filter)
    if line_filter:
        entries = entries.filter(line=line_filter)

    lines = HourlyProductionEntry.objects.filter(business=biz).values_list('line', flat=True).distinct()
    red_count = sum(1 for e in entries if e.status == 'red')
    amber_count = sum(1 for e in entries if e.status == 'amber')
    green_count = sum(1 for e in entries if e.status == 'green')

    HOUR_SLOTS = ['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
    return render(request, 'factory_ops/hourly_board.html', {
        'biz': biz, 'entries': entries,
        'date_filter': date_filter, 'line_filter': line_filter,
        'lines': lines,
        'red_count': red_count, 'amber_count': amber_count, 'green_count': green_count,
        'hour_slots': HOUR_SLOTS,
    })


@login_required
def petty_cash(request, slug):
    biz = _biz(request, slug)
    today = timezone.now().date()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            PettyCash.objects.create(
                business=biz,
                voucher_id=_next_id('PC', PettyCash.objects.filter(business=biz), 'voucher_id'),
                txn_date=request.POST.get('txn_date') or today,
                description=request.POST.get('description', ''),
                category=request.POST.get('category', 'other'),
                amount=request.POST.get('amount') or 0,
                paid_to=request.POST.get('paid_to', ''),
                receipt_ref=request.POST.get('receipt_ref', ''),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Voucher recorded.')
        elif action == 'delete':
            get_object_or_404(PettyCash, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:petty_cash', slug=slug)

    cat_filter = request.GET.get('cat', '')
    entries = PettyCash.objects.filter(business=biz)
    if cat_filter:
        entries = entries.filter(category=cat_filter)

    all_entries = PettyCash.objects.filter(business=biz)
    needs_approval = [e for e in all_entries if e.requires_approval]
    month_total = float(all_entries.filter(txn_date__month=today.month, txn_date__year=today.year).aggregate(
        total=Sum('amount'))['total'] or 0)

    return render(request, 'factory_ops/petty_cash.html', {
        'biz': biz, 'entries': entries,
        'cat_filter': cat_filter,
        'total_entries': all_entries.count(),
        'month_total': month_total,
        'needs_approval_count': len(needs_approval),
        'threshold_petty': 5000,
        'threshold_manager': 25000,
        'categories': [c[0] for c in PettyCash._meta.get_field('category').choices],
    })


@login_required
def worker_advances(request, slug):
    biz = _biz(request, slug)
    today = timezone.now().date()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            WorkerAdvance.objects.create(
                business=biz,
                advance_id=_next_id('ADV', WorkerAdvance.objects.filter(business=biz), 'advance_id'),
                employee_name=request.POST.get('employee_name', ''),
                emp_id_ref=request.POST.get('emp_id_ref', ''),
                date_issued=request.POST.get('date_issued') or today,
                amount=request.POST.get('amount') or 0,
                purpose=request.POST.get('purpose', ''),
                recovery_per_month=request.POST.get('recovery_per_month') or 0,
                amount_recovered=request.POST.get('amount_recovered') or 0,
                status=request.POST.get('status', 'outstanding'),
                notes=request.POST.get('notes', ''),
            )
            messages.success(request, 'Advance recorded.')
        elif action == 'update_recovery':
            adv = get_object_or_404(WorkerAdvance, pk=request.POST.get('pk'), business=biz)
            adv.amount_recovered = request.POST.get('amount_recovered') or adv.amount_recovered
            adv.status = request.POST.get('status', adv.status)
            adv.save()
            messages.success(request, 'Recovery updated.')
        elif action == 'delete':
            get_object_or_404(WorkerAdvance, pk=request.POST.get('pk'), business=biz).delete()
        return redirect('factory_ops:worker_advances', slug=slug)

    status_filter = request.GET.get('status', '')
    advances = WorkerAdvance.objects.filter(business=biz)
    if status_filter:
        advances = advances.filter(status=status_filter)

    all_advances = WorkerAdvance.objects.filter(business=biz)
    total_issued = float(all_advances.aggregate(total=Sum('amount'))['total'] or 0)
    total_recovered = float(all_advances.aggregate(total=Sum('amount_recovered'))['total'] or 0)
    total_outstanding = total_issued - total_recovered

    return render(request, 'factory_ops/worker_advances.html', {
        'biz': biz, 'advances': advances,
        'status_filter': status_filter,
        'total_issued': total_issued,
        'total_recovered': total_recovered,
        'total_outstanding': total_outstanding,
        'outstanding_count': all_advances.filter(status__in=['outstanding', 'recovering']).count(),
    })


# ─── SETTINGS ─────────────────────────────────────────────────────────────────

@login_required
def factory_settings(request, slug):
    biz = _biz(request, slug)
    if not _is_owner(request, biz):
        messages.error(request, 'Only the business owner can access settings.')
        return redirect('factory_ops:index', slug=slug)

    cfg = _get_settings(biz)

    if request.method == 'POST':
        cfg.fixed_assets = request.POST.get('fixed_assets') or cfg.fixed_assets
        cfg.long_term_debt = request.POST.get('long_term_debt') or cfg.long_term_debt
        cfg.interest_rate_pct = request.POST.get('interest_rate_pct') or cfg.interest_rate_pct
        cfg.tax_rate_pct = request.POST.get('tax_rate_pct') or cfg.tax_rate_pct
        cfg.cogs_estimate_pct = request.POST.get('cogs_estimate_pct') or cfg.cogs_estimate_pct
        cfg.currency = request.POST.get('currency', cfg.currency)
        cfg.factory_address = request.POST.get('factory_address', cfg.factory_address)
        cfg.tax_id = request.POST.get('tax_id', cfg.tax_id)
        cfg.bank_details = request.POST.get('bank_details', cfg.bank_details)
        cfg.working_hours_per_day = request.POST.get('working_hours_per_day') or cfg.working_hours_per_day
        cfg.petty_cash_limit = request.POST.get('petty_cash_limit') or cfg.petty_cash_limit
        cfg.manager_approval_limit = request.POST.get('manager_approval_limit') or cfg.manager_approval_limit
        cfg.save()
        messages.success(request, 'Settings saved.')
        return redirect('factory_ops:settings', slug=slug)

    return render(request, 'factory_ops/settings.html', {'biz': biz, 'cfg': cfg})


# ─── STOCK MOVEMENTS ──────────────────────────────────────────────────────────

@login_required
def stock_movements(request, slug):
    biz = _biz(request, slug)

    move_filter = request.GET.get('type', '')
    item_filter = request.GET.get('item_type', '')
    qs = StockMovement.objects.filter(business=biz)
    if move_filter:
        qs = qs.filter(move_type=move_filter)
    if item_filter:
        qs = qs.filter(item_type=item_filter)

    return render(request, 'factory_ops/stock_movements.html', {
        'biz': biz,
        'movements': qs[:200],
        'move_filter': move_filter,
        'item_filter': item_filter,
        'total_count': qs.count(),
        'move_types': StockMovement.MOVE_TYPE,
        'item_types': StockMovement.ITEM_TYPE,
    })


# ─── PRINTABLE INVOICE ────────────────────────────────────────────────────────

@login_required
def invoice_print(request, slug, pk):
    biz = _biz(request, slug)
    invoice = get_object_or_404(FactoryInvoice, pk=pk, business=biz)
    cfg = _get_settings(biz)
    return render(request, 'factory_ops/invoice_print.html', {
        'biz': biz, 'invoice': invoice, 'cfg': cfg,
    })


# ─── CSV EXPORTS ──────────────────────────────────────────────────────────────

def _csv_response(filename):
    resp = HttpResponse(content_type='text/csv')
    resp['Content-Disposition'] = f'attachment; filename="{filename}"'
    return resp


@login_required
def export_production_csv(request, slug):
    biz = _biz(request, slug)
    resp = _csv_response(f'production_{slug}.csv')
    w = csv.writer(resp)
    w.writerow(['Order ID', 'Style', 'Buyer', 'Qty', 'Line', 'Start Date',
                'Target Date', 'Stage', 'Priority'])
    for o in ProductionOrder.objects.filter(business=biz):
        w.writerow([o.order_id, o.style, o.buyer, o.qty, o.line,
                    o.start_date, o.target_date, o.get_current_stage_display(), o.get_priority_display()])
    return resp


@login_required
def export_daily_report_csv(request, slug):
    biz = _biz(request, slug)
    resp = _csv_response(f'daily_report_{slug}.csv')
    w = csv.writer(resp)
    w.writerow(['Date', 'Line', 'Style', 'Target', 'Actual', 'Manpower',
                'Efficiency %', 'Downtime Cause', 'SMV/Pair', 'Status'])
    for r in DailyProductionReport.objects.filter(business=biz):
        w.writerow([r.report_date, r.line, r.style, r.target_output, r.actual_output,
                    r.manpower, r.line_efficiency_pct, r.downtime_cause,
                    r.smv_per_pair, r.get_status_display()])
    return resp


@login_required
def export_inventory_csv(request, slug):
    biz = _biz(request, slug)
    resp = _csv_response(f'inventory_{slug}.csv')
    w = csv.writer(resp)
    w.writerow(['Type', 'ID', 'Name', 'Category', 'UOM', 'On Hand',
                'Reorder Level', 'Unit Cost', 'Stock Value'])
    for r in RawMaterial.objects.filter(business=biz):
        w.writerow(['Raw', r.item_id, r.name, r.category, r.uom,
                    r.on_hand, r.reorder_level, r.unit_cost, r.stock_value])
    for s in ProductSKU.objects.filter(business=biz):
        w.writerow(['SKU', s.sku_id, s.name, s.category, 'pcs',
                    s.stock_on_hand, '', s.unit_cost, s.stock_value])
    return resp


@login_required
def export_arap_csv(request, slug):
    biz = _biz(request, slug)
    resp = _csv_response(f'ar_ap_{slug}.csv')
    w = csv.writer(resp)
    w.writerow(['Entry ID', 'Type', 'Party', 'Amount', 'Due Date', 'Status', 'Notes'])
    for e in ARAPEntry.objects.filter(business=biz):
        w.writerow([e.entry_id, e.get_entry_type_display(), e.party,
                    e.amount, e.due_date, e.get_status_display(), e.notes])
    return resp


@login_required
def export_attendance_csv(request, slug):
    biz = _biz(request, slug)
    resp = _csv_response(f'attendance_{slug}.csv')
    w = csv.writer(resp)
    w.writerow(['Date', 'Section', 'Present', 'Absent', 'On Leave', 'OT Hours',
                'Day Wage Total', 'OT Wage Total'])
    for a in AttendanceSheet.objects.filter(business=biz):
        w.writerow([a.sheet_date, a.section, a.present, a.absent,
                    a.on_leave, a.ot_hours, a.day_wage_total, a.ot_wage_total])
    return resp


@login_required
def export_invoices_csv(request, slug):
    biz = _biz(request, slug)
    resp = _csv_response(f'invoices_{slug}.csv')
    w = csv.writer(resp)
    w.writerow(['Invoice ID', 'Order Ref', 'Buyer', 'Amount', 'Issue Date',
                'Due Date', 'Status'])
    for inv in FactoryInvoice.objects.filter(business=biz):
        w.writerow([inv.invoice_id, inv.order_ref, inv.buyer_name,
                    inv.amount, inv.issue_date, inv.due_date, inv.get_status_display()])
    return resp


# ─── EMAIL NOTIFICATIONS ──────────────────────────────────────────────────────

def _send_factory_alert(subject, body, owner_email):
    from django.core.mail import send_mail
    from django.conf import settings as django_settings
    try:
        send_mail(
            subject, body,
            getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@bengalbound.com'),
            [owner_email], fail_silently=True,
        )
    except Exception:
        pass


# ─── PERFORMANCE & INCENTIVES ─────────────────────────────────────────────────

@login_required
def kpi_templates(request, slug):
    biz = _biz(request, slug)
    templates_qs = KPITemplate.objects.filter(business=biz)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            criteria_names   = request.POST.getlist('criteria_name')
            criteria_weights = request.POST.getlist('criteria_weight')
            criteria_descs   = request.POST.getlist('criteria_desc')
            criteria = []
            for n, w, d in zip(criteria_names, criteria_weights, criteria_descs):
                if n.strip():
                    try:
                        criteria.append({'name': n.strip(), 'weight': float(w or 1), 'description': d.strip()})
                    except ValueError:
                        pass
            KPITemplate.objects.create(
                business=biz,
                role=request.POST.get('role', '').strip(),
                department=request.POST.get('department', 'Production'),
                bonus_pct_of_salary=request.POST.get('bonus_pct', '10') or 10,
                criteria=criteria,
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(request, 'KPI Template created.')
        elif action == 'delete':
            KPITemplate.objects.filter(business=biz, pk=request.POST.get('pk')).delete()
            messages.success(request, 'Template deleted.')
        elif action == 'toggle':
            t = get_object_or_404(KPITemplate, business=biz, pk=request.POST.get('pk'))
            t.is_active = not t.is_active
            t.save()
        return redirect('factory_ops:kpi_templates', slug=slug)

    return render(request, 'factory_ops/kpi_templates.html', {
        'biz': biz, 'templates': templates_qs,
        'dept_choices': KPITemplate.DEPT,
    })


@login_required
def evaluations(request, slug):
    biz = _biz(request, slug)
    import calendar as _cal
    today = timezone.now().date()
    try:
        period_month = int(request.GET.get('month', today.month))
        period_year  = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        period_month, period_year = today.month, today.year
    period_month = max(1, min(12, period_month))

    evals_qs    = EmployeeEvaluation.objects.filter(business=biz, period_month=period_month, period_year=period_year)
    templates_qs = KPITemplate.objects.filter(business=biz, is_active=True)
    employees_qs = FactoryEmployee.objects.filter(business=biz, status__in=['active', 'probation'])

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            p_month = int(request.POST.get('period_month', today.month))
            p_year  = int(request.POST.get('period_year', today.year))
            emp_name = request.POST.get('employee_name', '').strip()
            emp_role = request.POST.get('role', '').strip()
            salary   = request.POST.get('salary_ref', 0) or 0
            evaluated_by = request.POST.get('evaluated_by', '').strip()

            emp_id = request.POST.get('employee_id', '')
            if emp_id:
                try:
                    emp = FactoryEmployee.objects.get(pk=emp_id, business=biz)
                    emp_name = emp_name or emp.name
                    emp_role = emp_role or emp.designation
                    salary = salary or float(emp.salary)
                except FactoryEmployee.DoesNotExist:
                    pass

            tpl_id = request.POST.get('template_id', '')
            scores = []
            tpl = None
            if tpl_id:
                try:
                    tpl = KPITemplate.objects.get(pk=tpl_id, business=biz)
                    score_vals   = request.POST.getlist('score')
                    remarks_vals = request.POST.getlist('score_remarks')
                    for i, crit in enumerate(tpl.criteria):
                        sc = 0
                        try:
                            sc = max(0, min(100, float(score_vals[i]))) if i < len(score_vals) else 0
                        except (ValueError, IndexError):
                            pass
                        scores.append({
                            'name': crit.get('name', ''),
                            'weight': crit.get('weight', 1),
                            'score': sc,
                            'remarks': remarks_vals[i] if i < len(remarks_vals) else '',
                        })
                except KPITemplate.DoesNotExist:
                    pass

            EmployeeEvaluation.objects.create(
                business=biz, template=tpl, employee_name=emp_name, role=emp_role,
                period_month=p_month, period_year=p_year, salary_ref=salary,
                scores=scores, evaluated_by=evaluated_by,
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(request, f'Evaluation for {emp_name} saved.')
        elif action == 'approve':
            ev = get_object_or_404(EmployeeEvaluation, business=biz, pk=request.POST.get('pk'))
            ev.status = 'approved'
            ev.save()
        elif action == 'delete':
            EmployeeEvaluation.objects.filter(business=biz, pk=request.POST.get('pk')).delete()
        return redirect(f"{request.path}?month={period_month}&year={period_year}")

    months = [(i, _cal.month_name[i]) for i in range(1, 13)]
    years  = list(range(today.year - 2, today.year + 2))
    return render(request, 'factory_ops/evaluations.html', {
        'biz': biz, 'evals': evals_qs, 'templates': templates_qs,
        'employees': employees_qs, 'months': months, 'years': years,
        'period_month': period_month, 'period_year': period_year,
    })


@login_required
def sales_incentives(request, slug):
    biz = _biz(request, slug)
    import calendar as _cal
    today = timezone.now().date()
    try:
        period_month = int(request.GET.get('month', today.month))
        period_year  = int(request.GET.get('year', today.year))
    except (ValueError, TypeError):
        period_month, period_year = today.month, today.year
    period_month = max(1, min(12, period_month))

    incentives_qs = SalesIncentive.objects.filter(business=biz, period_month=period_month, period_year=period_year)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            SalesIncentive.objects.create(
                business=biz,
                employee_name=request.POST.get('employee_name', '').strip(),
                period_month=int(request.POST.get('period_month', today.month)),
                period_year=int(request.POST.get('period_year', today.year)),
                pairs_sold=int(request.POST.get('pairs_sold', 0) or 0),
                rate_per_pair=request.POST.get('rate_per_pair', 0) or 0,
                new_accounts=int(request.POST.get('new_accounts', 0) or 0),
                bonus_per_account=request.POST.get('bonus_per_account', 0) or 0,
                collection_achieved=request.POST.get('collection_achieved', 0) or 0,
                collection_target=request.POST.get('collection_target', 0) or 0,
                collection_bonus_rate=request.POST.get('collection_bonus_rate', 0) or 0,
                notes=request.POST.get('notes', '').strip(),
            )
            messages.success(request, 'Incentive record added.')
        elif action == 'approve':
            inc = get_object_or_404(SalesIncentive, business=biz, pk=request.POST.get('pk'))
            inc.status = 'approved'
            inc.save()
        elif action == 'mark_paid':
            inc = get_object_or_404(SalesIncentive, business=biz, pk=request.POST.get('pk'))
            inc.status = 'paid'
            inc.save()
        elif action == 'delete':
            SalesIncentive.objects.filter(business=biz, pk=request.POST.get('pk')).delete()
        return redirect(f"{request.path}?month={period_month}&year={period_year}")

    months = [(i, _cal.month_name[i]) for i in range(1, 13)]
    years  = list(range(today.year - 2, today.year + 2))
    total  = sum(i.total_incentive for i in incentives_qs)
    return render(request, 'factory_ops/sales_incentives.html', {
        'biz': biz, 'incentives': incentives_qs, 'months': months, 'years': years,
        'period_month': period_month, 'period_year': period_year, 'total_incentive': total,
    })


@login_required
def sample_orders(request, slug):
    biz = _biz(request, slug)
    status_filter = request.GET.get('status', '')
    orders_qs = SampleOrder.objects.filter(business=biz)
    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            mat_parts  = request.POST.getlist('mat_part')
            mat_names  = request.POST.getlist('mat_name')
            mat_colors = request.POST.getlist('mat_color')
            mat_thick  = request.POST.getlist('mat_thickness')
            mat_units  = request.POST.getlist('mat_unit')
            mat_qtys   = request.POST.getlist('mat_qty')
            materials = [
                {'part': p.strip(), 'material_name': n.strip(), 'color': c.strip(),
                 'thickness': t.strip(), 'unit': u.strip(), 'qty_per_pair': q.strip()}
                for p, n, c, t, u, q in zip(mat_parts, mat_names, mat_colors, mat_thick, mat_units, mat_qtys)
                if n.strip()
            ]

            step_nos      = request.POST.getlist('step_no')
            step_ops      = request.POST.getlist('step_operation')
            step_machines = request.POST.getlist('step_machine')
            step_notes    = request.POST.getlist('step_notes')
            process_steps = [
                {'step_no': no.strip(), 'operation': op.strip(),
                 'machine': mach.strip(), 'notes': note.strip()}
                for no, op, mach, note in zip(step_nos, step_ops, step_machines, step_notes)
                if op.strip()
            ]

            prob_areas = request.POST.getlist('prob_area')
            prob_descs = request.POST.getlist('prob_desc')
            problems   = [{'area': a.strip(), 'description': d.strip()}
                          for a, d in zip(prob_areas, prob_descs) if d.strip()]

            instructions = [i.strip() for i in request.POST.getlist('instruction') if i.strip()]

            so = SampleOrder.objects.create(
                business=biz,
                order_ref=request.POST.get('order_ref', '').strip(),
                requested_by=request.POST.get('requested_by', '').strip(),
                buyer_name=request.POST.get('buyer_name', '').strip(),
                style_name=request.POST.get('style_name', '').strip(),
                style_ref=request.POST.get('style_ref', '').strip(),
                target_date=request.POST.get('target_date') or None,
                sample_type=request.POST.get('sample_type', 'proto'),
                priority=request.POST.get('priority', 'standard'),
                last_number=request.POST.get('last_number', '').strip(),
                last_type=request.POST.get('last_type', ''),
                heel_height_mm=request.POST.get('heel_height_mm') or None,
                toe_allowance_mm=request.POST.get('toe_allowance_mm') or None,
                heel_allowance_mm=request.POST.get('heel_allowance_mm') or None,
                ball_allowance_mm=request.POST.get('ball_allowance_mm') or None,
                materials=materials,
                thread_color=request.POST.get('thread_color', '').strip(),
                thread_count=request.POST.get('thread_count', '').strip(),
                adhesive_type=request.POST.get('adhesive_type', '').strip(),
                primer_required=bool(request.POST.get('primer_required')),
                construction_type=request.POST.get('construction_type', 'cement'),
                process_steps=process_steps,
                problems=problems,
                special_instructions=instructions,
                assigned_to=request.POST.get('assigned_to', '').strip(),
                remarks=request.POST.get('remarks', '').strip(),
            )
            if request.FILES.get('document'):
                so.document = request.FILES['document']
                so.save()
            messages.success(request, f'Sample order {so.order_ref} created.')
        elif action == 'status':
            so = get_object_or_404(SampleOrder, business=biz, pk=request.POST.get('pk'))
            so.status = request.POST.get('new_status', so.status)
            if request.POST.get('approved_by'):
                so.approved_by = request.POST.get('approved_by')
                so.approval_date = timezone.now().date()
            so.save()
            messages.success(request, 'Status updated.')
        elif action == 'delete':
            SampleOrder.objects.filter(business=biz, pk=request.POST.get('pk')).delete()
        return redirect(f"{request.path}?status={status_filter}")

    return render(request, 'factory_ops/sample_orders.html', {
        'biz': biz, 'orders': orders_qs,
        'status_filter': status_filter, 'status_choices': SampleOrder.STATUS,
    })


def trigger_factory_notifications(biz):
    """
    Call this from views after any action that may generate alerts.
    Sends email to the business owner for:
      - Overdue approvals pending >48h
      - Low-stock raw materials
      - Overdue customer orders
    """
    owner_email = biz.owner.email
    alerts = []

    overdue_approvals = ApprovalRequest.objects.filter(
        business=biz, status='pending',
        created_at__lt=timezone.now() - timezone.timedelta(hours=48),
    )
    if overdue_approvals.exists():
        alerts.append(
            f'{overdue_approvals.count()} approval request(s) have been pending for over 48 hours.'
        )

    low_stock = [r for r in RawMaterial.objects.filter(business=biz) if r.is_low_stock]
    if low_stock:
        names = ', '.join(r.name for r in low_stock[:5])
        alerts.append(f'Low stock alert: {names}' + (' and more.' if len(low_stock) > 5 else '.'))

    overdue_orders = [
        o for o in CustomerOrder.objects.filter(
            business=biz).exclude(status__in=['delivered', 'cancelled'])
        if o.delivery_date and o.delivery_date < timezone.now().date()
    ]
    if overdue_orders:
        alerts.append(f'{len(overdue_orders)} customer order(s) are past their delivery date.')

    if alerts:
        body = '\n\n'.join(alerts)
        _send_factory_alert(
            f'[{biz.name}] Factory Operations Alerts',
            f'Hi,\n\nThe following items require your attention:\n\n{body}\n\nBengalBound HUB',
            owner_email,
        )
