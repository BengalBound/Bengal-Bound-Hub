from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone

from hub.views import _get_business_for_user
from .models import ManufacturingOrder, WorkOrderOperation, MaterialConsumption, ProductionKPISnapshot

try:
    from modules.inventory.models import Product, Warehouse
except ImportError:
    Product = None
    Warehouse = None

try:
    from modules.bom.models import BillOfMaterials
except ImportError:
    BillOfMaterials = None


def _biz(slug, user):
    return _get_business_for_user(slug, user)


def _next_mo_number(biz):
    count = ManufacturingOrder.objects.filter(business=biz).count() + 1
    return f"{count:05d}"


@login_required(login_url='/accounts/login/')
def index(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    orders = ManufacturingOrder.objects.filter(business=biz)
    stats = {
        'total': orders.count(),
        'in_progress': orders.filter(status='in_progress').count(),
        'confirmed': orders.filter(status='confirmed').count(),
        'done': orders.filter(status='done').count(),
    }
    recent = orders.select_related('product', 'responsible').order_by('-created_at')[:10]
    return render(request, 'production/index.html', {
        'biz': biz, 'stats': stats, 'recent_orders': recent,
    })


@login_required(login_url='/accounts/login/')
def manufacturing_orders(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    status_filter = request.GET.get('status', '')
    qs = ManufacturingOrder.objects.filter(business=biz).select_related('product', 'bom', 'responsible').order_by('-created_at')
    if status_filter:
        qs = qs.filter(status=status_filter)
    products = Product.objects.filter(business=biz) if Product else []
    boms = BillOfMaterials.objects.filter(business=biz, status='active') if BillOfMaterials else []
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            product = get_object_or_404(Product, pk=request.POST.get('product'), business=biz) if Product else None
            ManufacturingOrder.objects.create(
                business=biz,
                mo_number=_next_mo_number(biz),
                product=product,
                bom_id=request.POST.get('bom') or None,
                quantity_to_produce=request.POST.get('quantity_to_produce', 1) or 1,
                priority=request.POST.get('priority', 'normal'),
                scheduled_start=request.POST.get('scheduled_start') or None,
                scheduled_end=request.POST.get('scheduled_end') or None,
                responsible=request.user,
                notes=request.POST.get('notes', ''),
                created_by=request.user,
            )
            messages.success(request, 'Manufacturing order created.')
        return redirect('production:manufacturing_orders', slug=slug)
    return render(request, 'production/manufacturing_orders.html', {
        'biz': biz, 'orders': qs, 'products': products, 'boms': boms, 'status_filter': status_filter,
    })


@login_required(login_url='/accounts/login/')
def mo_detail(request, slug, pk):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()
    mo = get_object_or_404(ManufacturingOrder, pk=pk, business=biz)
    operations = mo.operations.select_related('work_center', 'worker')
    consumptions = mo.material_consumptions.select_related('product', 'recorded_by')
    products = Product.objects.filter(business=biz) if Product else []
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_status':
            new_status = request.POST.get('status', mo.status)
            mo.status = new_status
            if new_status == 'in_progress' and not mo.actual_start:
                mo.actual_start = timezone.now()
            elif new_status == 'done':
                mo.actual_end = timezone.now()
                mo.quantity_produced = request.POST.get('quantity_produced', mo.quantity_to_produce) or mo.quantity_to_produce
            mo.save()
            messages.success(request, f'Status updated to {mo.get_status_display()}.')
        elif action == 'add_consumption':
            product = get_object_or_404(Product, pk=request.POST.get('product'), business=biz) if Product else None
            MaterialConsumption.objects.create(
                manufacturing_order=mo,
                product=product,
                planned_qty=request.POST.get('planned_qty', 0) or 0,
                consumed_qty=request.POST.get('consumed_qty', 0) or 0,
                uom=request.POST.get('uom', '').strip(),
                recorded_by=request.user,
            )
            messages.success(request, 'Material consumption recorded.')
        elif action == 'update_operation':
            op = get_object_or_404(WorkOrderOperation, pk=request.POST.get('op_id'), manufacturing_order=mo)
            op.status = request.POST.get('op_status', op.status)
            if op.status == 'in_progress' and not op.started_at:
                op.started_at = timezone.now()
            elif op.status == 'done' and not op.completed_at:
                op.completed_at = timezone.now()
                op.actual_duration = request.POST.get('actual_duration', op.planned_duration) or op.planned_duration
            op.save()
            messages.success(request, 'Operation updated.')
        elif action == 'delete':
            mo.delete()
            messages.success(request, 'Manufacturing order deleted.')
            return redirect('production:manufacturing_orders', slug=slug)
        return redirect('production:mo_detail', slug=slug, pk=pk)
    return render(request, 'production/mo_detail.html', {
        'biz': biz, 'mo': mo, 'operations': operations,
        'consumptions': consumptions, 'products': products,
    })


# ── KPI Dashboard ─────────────────────────────────────────────────────────────

@login_required(login_url='/accounts/login/')
def kpi_dashboard(request, slug):
    biz = _biz(slug, request.user)
    if not biz:
        return HttpResponseForbidden()

    if request.method == 'POST':
        ProductionKPISnapshot.objects.update_or_create(
            business=biz,
            snapshot_date=request.POST['snapshot_date'],
            period=request.POST.get('period', 'daily'),
            defaults={
                'orders_due': request.POST.get('orders_due', 0) or 0,
                'orders_on_time': request.POST.get('orders_on_time', 0) or 0,
                'pairs_to_final_qc': request.POST.get('pairs_to_final_qc', 0) or 0,
                'pairs_passed_first': request.POST.get('pairs_passed_first', 0) or 0,
                'pairs_produced': request.POST.get('pairs_produced', 0) or 0,
                'pairs_rejected_reworked': request.POST.get('pairs_rejected_reworked', 0) or 0,
                'total_labour_hours': request.POST.get('total_labour_hours', 0) or 0,
                'wip_pairs_at_lasting': request.POST.get('wip_pairs_at_lasting', 0) or 0,
                'total_production_cost': request.POST.get('total_production_cost') or None,
                'notes': request.POST.get('notes', '').strip(),
                'recorded_by': request.user,
            }
        )
        messages.success(request, 'KPI snapshot saved.')
        return redirect('production:kpi_dashboard', slug=slug)

    period_filter = request.GET.get('period', 'daily')
    snapshots = ProductionKPISnapshot.objects.filter(business=biz, period=period_filter).order_by('-snapshot_date')[:30]
    latest = snapshots.first()

    return render(request, 'production/kpi_dashboard.html', {
        'biz': biz,
        'snapshots': snapshots,
        'latest': latest,
        'period_filter': period_filter,
        'periods': ProductionKPISnapshot.PERIOD,
    })
